'''
The sis_import tool imports CSV data into Canvas.

The `sis_import.py` module is intended for use with automation
that keeps a Canvas instance up-to-date with the data received
from a university Student Information System. This module can
be used as both a python library and a command run from the
command line.

The import can be viewed by admins in the Canvas API, e.g. at:
https://your_university_canvas.com/accounts/<id>/sis_import
'''

from argparse import ArgumentParser, Namespace, ArgumentDefaultsHelpFormatter
import logging
import pprint
import time
import re
from typing import Any, Callable, Dict, List, Optional, Tuple

from canvas_api_client.interface import CanvasAPIClient
from canvas_api_client.types import RequestParams

from requests import Response

logger = logging.getLogger()

DEFAULT_TIMEOUT_SECONDS = 60 * 60 * 2  # 2 hours
COMPLETED_STATES = ('imported',
                    'imported_with_messages',
                    'failed',
                    'failed_with_messages')

# Python types
SisImportResponse = Tuple[Response, List[List[str]], List[List[str]]]


class SisImportTimeoutError(Exception):
    """
    Raise if the SIS import takes too long.
    """


class FieldNotFoundError(Exception):
    """
    Raise when a required field in the SIS import response is not found.
    """


def _get_field(data: Dict[str, Any], key: str) -> Any:
    """
    Try to return a value for a key in a data dictionary,
    throw custom exception for failures.
    """
    try:
        return data[key]
    except KeyError:
        logger.debug('sis import data: {}'.format(data))
        raise FieldNotFoundError(
            'Unable to find field "{}" in sis import data. '
            'See debug log for data.'.format(key))


def is_import_complete(api_client: CanvasAPIClient,
                       account_id: str,
                       sis_import_id: str) -> bool:
    """
    Check if the import is complete. Returns a boolean, true if imported.
    """
    import_response = api_client.get_sis_import_status(account_id, sis_import_id).json()
    progress = _get_field(import_response, 'progress')
    logger.info('SIS import progress: {}% complete'.format(progress))
    return _get_field(import_response, 'workflow_state') in COMPLETED_STATES


def _check_elapsed_time(start_seconds: int, timeout: int) -> None:
    """
    Check the elapsed time since the beginning of a SIS import.

    If the elapsed time is greater than the timeout, then raise an error.
    """
    elapsed_seconds = time.time() - start_seconds
    if elapsed_seconds > timeout:
        msg = 'SIS Import took {} seconds. Max allowed import time is {} seconds.'
        msg = msg.format(elapsed_seconds, timeout)
        raise SisImportTimeoutError(msg)


def _wait_for_completion(api_client: CanvasAPIClient,
                         account_id: str,
                         sis_import_id: str,
                         timeout: Optional[int] = None) -> None:
    """
    Wait until the SIS import is complete.
    """
    start_seconds = time.time()
    retry_count = 0
    while not is_import_complete(api_client, account_id, sis_import_id):
        if timeout is not None:
            _check_elapsed_time(start_seconds, timeout)
        retry_count += 1
        if retry_count < 5:
            time.sleep(1)
        else:
            # ensure we allow the api to rest between subsequent retries
            time.sleep(30)


def _log_message(logger_func: Callable[[str], None],
                 message_list: List[Tuple[str, str]]) -> List[str]:
    """
    Call a logger function on each message in a message list and return the messages.
    """
    messages = []
    for filename, message in message_list:
        logger_func("Below warning occurred while importing file {}".format(filename))
        logger_func(message)
        messages.append(message)
    return messages


def _log_sis_errors(api_client: CanvasAPIClient,
                    account_id: str,
                    sis_import_id: str) -> SisImportResponse:
    """
    Log warnings and errors that occurred during the SIS import.
    """

    sis_import = api_client.get_sis_import_status(account_id, sis_import_id).json()

    warnings = []
    errors = []

    if 'processing_warnings' in sis_import:
        warnings = _log_message(logger.warn, sis_import['processing_warnings'])
    if 'processing_errors' in sis_import:
        errors = _log_message(logger.error, sis_import['processing_errors'])

    return (sis_import, warnings, errors)


def _import_sis_csv(api_client: CanvasAPIClient,
                    account_id: str,
                    csv_filepath: str,
                    timeout: Optional[int] = None,
                    request_params: RequestParams = None,
                    wait_for_completion: bool = True) -> SisImportResponse:
    """
    Import a SIS CSV file to the Canvas API. Check the status to ensure it completes successfully.
    """
    if request_params is None:
        request_params = {'import_type': 'instructure_csv',
                          'override_sis_stickiness': 'true'}

    sis_import = api_client.import_sis_data(account_id, csv_filepath, params=request_params).json()

    if 'errors' in sis_import:
        for messages in sis_import.get('errors', []):
            logger.error(messages)

    sis_import_id = _get_field(sis_import, 'id')

    logger.info('Importing {}. SIS import id: #{}'.format(csv_filepath, sis_import_id))
    if wait_for_completion:
        _wait_for_completion(api_client, account_id, sis_import_id, timeout=timeout)
        logger.info('SIS import #{} 100% complete.'.format(sis_import_id))

    return _log_sis_errors(api_client, account_id, sis_import_id)


class SisImportError(Exception):
    """
    Raise if there is an error importing the users csv to canvas.
    """


class SisImport(object):
    """
    Controller object for importing CSV files to the Canvas API.
    """

    def __init__(self,
                 api_client: CanvasAPIClient,
                 account_id: int,
                 timeout: Optional[int] = DEFAULT_TIMEOUT_SECONDS,
                 dryrun: bool = False,
                 wait_for_completion: bool = False) -> None:
        self._api_client = api_client
        self._account_id = account_id
        self._warnings = dict()
        self._errors = dict()
        self._timeout = timeout
        self._dryrun = dryrun
        self._wait_for_completion = wait_for_completion

    def import_csv(self, csv_path: str) -> SisImportResponse:
        """
        Import a CSV file to the Canvas API via SIS CSV Import.
        """
        if self._dryrun:
            warning = 'Not importing {} since running in dryrun mode!'
            logger.warn(warning.format(csv_path))
            import_response, warnings, errors = (None, [], [])
        else:
            import_response, warnings, errors = _import_sis_csv(
                self._api_client, self._account_id, csv_path,
                timeout=self._timeout,
                wait_for_completion=self._wait_for_completion)
        logger.debug('SIS Import Response JSON:')
        logger.debug(pprint.pformat(import_response, indent=2))
        self._warnings[csv_path] = warnings
        self._errors[csv_path] = errors
        return import_response

    def check_errors(self, exit_on_error: bool = True) -> None:
        """
        Raises a `SisImportError` if any errors are found.
        """
        found_error = False
        for filepath, errors in self._errors.items():
            if errors:
                msg = 'Errors occurred during Canvas SIS CSV Import of file {}: {}'
                logger.error(msg.format(filepath, errors))
                found_error = True
        if found_error and exit_on_error:
            raise SisImportError('At least one Canvas SIS CSV Import failed.')


def main():
    parser = ArgumentParser(
        description=__doc__,
        formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        'csv_path',
        help='Set path for incremental diff of data to send to canvas')
    parser.add_argument(
        '--account-id',
        type=int,
        help='The account identifier for importing SIS data.')
    parser.add_argument(
        '--dryrun',
        default=False,
        action='store_true',
        help='Run the SIS Import task in dryrun mode, so no Canvas API uploads.')
    parser.add_argument(
        '--timeout-seconds',
        type=int,
        default=DEFAULT_TIMEOUT_SECONDS,
        help=('A timeout value in seconds to ensure the SIS Import '
              'does not hang indefinitely.'))
    args = parser.parse_args()

    api_client = CanvasAPIv1(
        raw_input('Canvas API URL: '),
        raw_input('Canvas API Token: '))

    sis_import = SisImport(api_client, args.account_id, dryrun=args.dryrun)
    sis_import.import_csv(args.csv_path)
    sis_import.check_errors()

if __name__ = '__main__':
    main()
