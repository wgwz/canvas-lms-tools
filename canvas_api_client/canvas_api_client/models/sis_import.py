import logging
import pprint
from typing import Any, List

from canvas_api_client.types import ResponseJson

from requests import Response

logger = logging.getLogger()

COMPLETED_STATES = (
    'imported',
    'imported_with_messages',
    'failed',
    'failed_with_messages')  # yapf: disable
PROCESSING_WARNINGS_KEY = 'processing_warnings'
PROCESSING_ERRORS_KEY = 'processing_errors'


class FieldNotFoundError(Exception):
    """
    Raise when a required field in the SIS import response is not found.
    """


def get_response_field(response_json: ResponseJson, key: str) -> Any:
    """
    Try to return a value for a key in the SIS Import response JSON,
    throwing a custom exception for failures.
    """
    try:
        return response_json[key]
    except KeyError:
        logger.debug('SIS import response: {}'.format(response_json))
        raise FieldNotFoundError(
            'Unable to find field "{}" in SIS import response. '
            'See debug log for response data.'.format(key))


def has_non_empty_field(response_json: ResponseJson, key: str) -> bool:
    return key in response_json and response_json[key]


class SisImport(object):
    def __init__(self, response_json: ResponseJson) -> None:
        self._json = response_json

    @classmethod
    def from_response(cls, response: Response):
        return cls(response.json())

    def __str__(self):
        return pprint.pformat(self._json, indent=2)

    @property
    def id(self) -> str:
        return get_response_field(self._json, 'id')

    @property
    def has_errors(self) -> bool:
        return has_non_empty_field(self._json, 'errors')

    @property
    def errors(self) -> List[str]:
        return get_response_field(self._json, 'errors')

    @property
    def has_processing_warnings(self) -> bool:
        return has_non_empty_field(self._json, PROCESSING_WARNINGS_KEY)

    @property
    def processing_warnings(self) -> List[List[str]]:
        return get_response_field(self._json, PROCESSING_WARNINGS_KEY)

    @property
    def has_processing_errors(self) -> bool:
        return has_non_empty_field(self._json, PROCESSING_ERRORS_KEY)

    @property
    def processing_errors(self) -> List[List[str]]:
        return get_response_field(self._json, PROCESSING_ERRORS_KEY)

    @property
    def progress(self) -> str:
        return get_response_field(self._json, 'progress')

    @property
    def workflow_state(self) -> str:
        return get_response_field(self._json, 'workflow_state')

    @property
    def is_complete(self) -> bool:
        return self.workflow_state in COMPLETED_STATES
