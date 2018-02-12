import logging
import os
from typing import (Any, Dict, Iterator, Optional)

from canvas_api_client.errors import APIPaginationException
from canvas_api_client.interface import CanvasAPIClient
from canvas_api_client.types import (RequestHeaders, RequestParams, Response)

import requests

logger = logging.getLogger()


class CanvasAPIv1(CanvasAPIClient):
    """
    Canvas v1 API Client.

    This client can be used to make requests to the v1 Canvas API.

    Create separate clients for other versions of the Canvas API.
    """

    def __init__(self,
                 api_url: str,
                 api_token: Optional[str] = None,
                 requests_lib: Optional[Any] = requests) -> None:
        """
        Creates a canvas API client given a base URL for the API, an optional
        API token, and an optional requests library.

        The optional requests library should be either the python HTTP requests
        library or the equivalent (e.g. a Requests-OAuthlib session object).
        """
        self._api_url = api_url
        self._api_token = api_token
        self._requests_lib = requests_lib

    def _get_url(self, endpoint: str) -> str:
        """
        Formats a Canvas API URL from a given endpoint.
        """
        return "{base_url}{endpoint}".format(
            base_url=self._api_url, endpoint=endpoint)

    def _add_bearer_token(self, headers: Dict[str, Any]):
        """
        Adds the authentication bearer token. Only run this if the token exists.
        """
        token_str = "Bearer {}".format(self._api_token)
        headers.update({'Authorization': token_str})

    def _send_request(self,
                      callback,
                      url: str,
                      exit_on_error: bool = True,
                      headers: RequestHeaders = None,
                      params: RequestParams = None,
                      **kwargs) -> Response:
        """
        Sends an API call to the Canvas server via callback method.

        The callback should be a requests.<func> function or the equivalent.

        Note: since raise_for_status() will raise an exception for error
        codes, the user is responsible for catching requests.exceptions.HTTPError
        exceptions unless they run with the exit_on_error set to False.
        """
        if headers is None:
            headers = {}
        if params is None:
            params = {}

        if self._api_token is not None:
            self._add_bearer_token(headers)

        response = callback(url, headers=headers, params=params, **kwargs)
        if not response.ok:
            logger.debug('Error status code for url "{}"'.format(response.url))
        if exit_on_error:
            response.raise_for_status()

        return response

    def _get(self, *args, **kwargs) -> Response:
        """
        Sends a GET request to the API.
        """
        return self._send_request(self._requests_lib.get, *args, **kwargs)

    def _delete(self, *args, **kwargs) -> Response:
        """
        Sends a DELETE request to the API.
        """
        return self._send_request(self._requests_lib.delete, *args, **kwargs)

    def _post(self, *args, **kwargs) -> Response:
        """
        Sends a POST request to the API.
        """
        return self._send_request(self._requests_lib.post, *args, **kwargs)

    def _put(self, *args, **kwargs) -> Response:
        """
        Sends a PUT request to the API.
        """
        return self._send_request(self._requests_lib.put, *args, **kwargs)

    def _check_response_headers_for_pagination(self, response: Response):
        """
        Check the response headers for a "link" (a header indicating that the
        API has pagination enabled for the request url) and throw an exception
        if it does not exist.
        """
        if 'link' not in response.headers:
            logger.error("Response: {}".format(response.json()['errors']))
            raise APIPaginationException(
                "Canvas API did not return a response with pagination "
                "for a request to {}".format(response.url))

    def _get_paginated(self,
                       url: str,
                       headers: RequestHeaders = None,
                       params: RequestParams = None) -> Iterator[Response]:
        """
        Send an API call to the Canvas server with pagination.

        Returns a generator of response objects.
        """
        response = self._get(url, headers=headers, params=params)
        self._check_response_headers_for_pagination(response)

        yield response.json()

        while 'next' in response.links:
            response = self._get(
                response.links['next']['url'], headers=headers)
            yield response.json()

    def _format_sis_course_id(self, course_id: str):
        """
        Returns request string for querying with a SIS course ID.
        """
        return "sis_course_id:{}".format(course_id)

    def get_account_courses(self,
                            account_id: str,
                            params: RequestParams = None
                            ) -> Iterator[Response]:
        """
        Returns a generator of courses for a given account from the v1 API.

        https://canvas.instructure.com/doc/api/accounts.html#method.accounts.courses_api
        """
        endpoint = "accounts/{account_id}/courses".format(
            account_id=account_id)

        return self._get_paginated(self._get_url(endpoint), params=params)

    def get_course_users(self,
                         course_id: str,
                         is_sis_course_id: bool = False,
                         params: RequestParams = None) -> Iterator[Response]:
        """
        Returns a generator of course enrollments for a given course from the v1 API.

        https://canvas.instructure.com/doc/api/courses.html#method.courses.users
        """
        if is_sis_course_id:
            course_id = self._format_sis_course_id(course_id)

        endpoint = "courses/{}/users".format(course_id)

        return self._get_paginated(self._get_url(endpoint), params=params)

    def delete_enrollment(self,
                          course_id: str,
                          enrollment_id: str,
                          is_sis_course_id: bool = False,
                          params: RequestParams = None) -> Response:
        """
        Deletes an enrollment for a given course from the v1 API. Use with caution.

        https://canvas.instructure.com/doc/api/enrollments.html#method.enrollments_api.destroy
        """
        if is_sis_course_id:
            course_id = self._format_sis_course_id(course_id)

        endpoint = "courses/{course_id}/enrollments/{id}".format(
            course_id=course_id, id=enrollment_id)

        return self._delete(self._get_url(endpoint), params=params)

    def import_sis_data(self,
                        account_id: str,
                        data_file: str,
                        params: RequestParams = None) -> Response:
        """
        Import SIS data into Canvas. Must be on a root account with SIS imports enabled.

        https://canvas.instructure.com/doc/api/sis_imports.html#method.sis_imports_api.create

        https://canvas.instructure.com/doc/api/file.sis_csv.html
        """
        endpoint = 'accounts/{}/sis_imports'.format(account_id)
        url = self._get_url(endpoint)
        with open(data_file, 'rb') as f:
            files = {'attachment': f}
            return self._post(url, params=params, files=files)

    def get_sis_import_status(self,
                              account_id: str,
                              sis_import_id: str,
                              params: RequestParams = None) -> Response:
        """
        Get the status of an already created SIS import.

        https://canvas.instructure.com/doc/api/sis_imports.html#method.sis_imports_api.show
        """
        endpoint = 'accounts/{}/sis_imports/{}'.format(account_id, sis_import_id)
        return self._get(self._get_url(endpoint), params=params)
