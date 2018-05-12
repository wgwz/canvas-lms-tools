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

from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
import logging
import time
from typing import Callable, List, Optional

from canvas_api_client.interface import CanvasAPIClient
from canvas_api_client.models import SisImport
from canvas_api_client.types import RequestParams
from canvas_api_client.v1_client import CanvasAPIv1

from requests import Response

logger = logging.getLogger()

DEFAULT_TIMEOUT_SECONDS = 60 * 60 * 2  # 2 hours


class SisImportTimeoutError(Exception):
    """
    Raise if the SIS import takes too long.
    """


def _log_message(logger_func: Callable[[str], None],
                 message_list: List[List[str]]) -> None:
    """
    Call a logger function on each message in a message list and return the
    messages.
    """
    for filename, message in message_list:
        logger_func(
            "Below warning occurred while importing {} file:\n{}".format(
                filename, message))


def get_default_request_params():
    return {
        'import_type': 'instructure_csv',
        'override_sis_stickiness': 'true'
    }


class SisImporter(object):
    """
    Processes CSV files to the Canvas API.
    """

    def __init__(self,
                 api_client: CanvasAPIClient,
                 account_id: str,
                 timeout: Optional[int] = DEFAULT_TIMEOUT_SECONDS,
                 dryrun: bool = False,
                 wait_for_completion: bool = True,
                 start_import_params: RequestParams = None) -> None:
        self._api_client = api_client
        self._account_id = account_id
        self._timeout = timeout
        self._dryrun = dryrun
        self._wait_for_completion = wait_for_completion
        if start_import_params is None:
            start_import_params = get_default_request_params()
        self._start_import_params = start_import_params

    def import_csv(self, csv_path: str) -> Optional[Response]:
        """
        Import a CSV file to the Canvas API via SIS CSV Import.

        Optionally check the status and wait for completion.
        """
        if self._dryrun:
            warning = 'Not importing {} since running in dryrun mode!'
            logger.warn(warning.format(csv_path))
            return None
        sis_import = self._start_import(csv_path)
        sis_import_id = sis_import.id
        if self._wait_for_completion:
            self.wait_for_completion(sis_import_id)
            logger.info('SIS import #{} 100% complete.'.format(sis_import_id))
        return self._get_final_response(sis_import_id)

    def _start_import(self, csv_path: str) -> SisImport:
        '''
        Starts a SIS Import and returns the import identifier.
        '''
        logger.info('Starting SIS Import of {}.'.format(csv_path))
        response = self._api_client.import_sis_data(
            self._account_id, csv_path, params=self._start_import_params)
        sis_import = SisImport.from_response(response)
        self._log_initial_response(sis_import)
        return sis_import

    @staticmethod
    def _log_initial_response(sis_import: SisImport) -> None:
        '''
        Log initial response information when the SIS import starts.
        '''
        logger.info('SIS import id: {}'.format(sis_import.id))
        if sis_import.has_errors:
            for messages in sis_import.errors:
                logger.error(messages)

    def _get_final_response(self, sis_import_id: str) -> Response:
        response = self._get_import_status(sis_import_id)
        sis_import = SisImport.from_response(response)
        self._log_final_response(sis_import)
        return response

    def _get_import_status(self, sis_import_id: str) -> Response:
        return self._api_client.get_sis_import_status(self._account_id,
                                                      sis_import_id)

    @staticmethod
    def _log_final_response(sis_import: SisImport) -> None:
        """
        Log response, warnings, and errors after processing an import.
        """
        logger.debug('SIS Import Response Data:')
        logger.debug(str(sis_import))
        if sis_import.has_processing_warnings:
            _log_message(logger.warn, sis_import.processing_warnings)
        if sis_import.has_processing_errors:
            _log_message(logger.error, sis_import.processing_errors)

    def wait_for_completion(self, sis_import_id: str) -> None:
        """
        Wait until the SIS import is complete.
        """
        start_seconds = time.time()
        retry_count = 0
        while not self.is_import_complete(sis_import_id):
            if self._timeout is not None:
                self.check_elapsed_time(start_seconds, self._timeout)
            retry_count += 1
            if retry_count < 5:
                time.sleep(1)
            else:
                # ensure we allow the API to recover between subsequent retries
                time.sleep(30)

    def is_import_complete(self, sis_import_id: str) -> bool:
        """
        Check if the import is complete. Returns a boolean, true if imported.
        """
        response = self._get_import_status(sis_import_id)
        sis_import = SisImport.from_response(response)
        logger.info('SIS import progress: {}% complete'.format(
            sis_import.progress))
        return sis_import.is_complete

    @staticmethod
    def check_elapsed_time(start_seconds: float,
                           timeout_seconds: float) -> None:
        """
        Check the elapsed time since the beginning of a SIS import.

        If the elapsed time is greater than the timeout, then raise an error.
        """
        elapsed_seconds = time.time() - start_seconds
        if elapsed_seconds > timeout_seconds:
            msg = ('SIS Import took {} seconds. Max allowed import time '
                   'is {} seconds.').format(elapsed_seconds, timeout_seconds)
            raise SisImportTimeoutError(msg)


def main():
    parser = ArgumentParser(
        description=__doc__, formatter_class=ArgumentDefaultsHelpFormatter)
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
        help='Run the SIS Import without uploading to Canvas.')
    parser.add_argument(
        '--timeout-seconds',
        type=int,
        default=DEFAULT_TIMEOUT_SECONDS,
        help=('A timeout value in seconds to ensure the SIS Import '
              'does not hang indefinitely.'))
    args = parser.parse_args()

    api_client = CanvasAPIv1(
        input('Canvas API URL: '), input('Canvas API Token: '))

    sis_import = SisImport(api_client, args.account_id, dryrun=args.dryrun)
    sis_import.process(args.csv_path)
    sis_import.check_errors()


if __name__ == '__main__':
    main()
