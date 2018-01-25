import logging
import os
from typing import (Any, Dict, Iterator)

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

    def __init__(self, api_url: str, api_token: str) -> None:
        self._api_url = api_url
        self._api_token = api_token

    def _get_url(self, endpoint: str) -> str:
        return "{base_url}{endpoint}".format(
            base_url=self._api_url, endpoint=endpoint)

    def _add_bearer_token(self, headers: Dict[str, Any]):
        token_str = "Bearer {}".format(self._api_token)
        headers.update({'Authorization': token_str})

    def _send_request(self,
                      url: str,
                      callback,
                      exit_on_error: bool = True,
                      headers: RequestHeaders = None,
                      params: RequestParams = None) -> Response:
        """
        Sends an API call to the Canvas server via callback method.

        The callback should be a requests.<func> function.

        Note: since raise_for_status() will raise an exception for error
        codes, the user is responsible for catching requests.exceptions.HTTPError
        exceptions unless they run with the exit_on_error set to False.
        """
        if headers is None:
            headers = {}
        if params is None:
            params = {}

        self._add_bearer_token(headers)

        response = callback(url, headers=headers, params=params)
        if not response.ok:
            logger.debug('Error status code for url "{}"'.format(response.url))
        if exit_on_error:
            response.raise_for_status()

        return response

    def _get(self,
             url: str,
             headers: RequestHeaders = None,
             params: RequestParams = None) -> Response:
        """
        Sends a GET request to the Canvas v1 API.
        """
        return self._send_request(
            url, requests.get, headers=headers, params=params)

    def _delete(self,
                url: str,
                headers: RequestHeaders = None,
                params: RequestParams = None) -> Response:
        """
        Sends a DELETE request to the Canvas v1 API.
        """
        return self._send_request(
            url, requests.delete, headers=headers, params=params)

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
