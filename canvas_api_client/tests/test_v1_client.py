import os

from canvas_api_client.v1_client import CanvasAPIv1
from canvas_api_client.errors import APIPaginationException

from unittest import (skipIf, TestCase)
from unittest.mock import MagicMock, patch


def get_mock_response_with_pagination(url):
    mock_response = MagicMock(
        headers={'link': url + 'page=1'},
        links={'next': {'url': url + 'page=2'}})
    mock_response.json.return_value = {
        'value': 'first response'}
    return mock_response


class TestCanvasAPIv1Client(TestCase):

    @patch('canvas_api_client.v1_client.requests')
    def setUp(self, mock_requests):
        self.test_client = CanvasAPIv1(
            'https://foo.cc.columbia.edu/api/v1/',
            'foo_token')

    # TODO(lcary): https://github.com/lcary/canvas-lms-tools/issues/3
    @skipIf("TRAVIS" in os.environ and os.environ["TRAVIS"] == "true",
        "Skipping this test on Travis CI due to nonsensical error.")
    def test_send_request(self):
        mock_requests = MagicMock()
        mock_response = MagicMock()

        test_callback = mock_requests.get
        test_callback.return_value = mock_response

        url = 'https://foo.cc.columbia.edu/api/v1/search'

        returned_response = self.test_client._send_request(
            url,
            test_callback,
            exit_on_error=True,
            headers={'foo': 'bar'},
            params={'x': 'y'})

        returned_response.raise_for_status.assert_called_once()
        test_callback.assert_called_once_with(
            url,
            headers={'foo': 'bar', 'Authorization': 'Bearer foo_token'},
            params={'x': 'y'})

    @patch('canvas_api_client.v1_client.requests')
    def test_get_paginated_exception(self, mock_requests):
        mock_response = MagicMock()
        mock_response.headers = {}
        mock_response.json.return_value == {}

        mock_requests.get.return_value = mock_response

        url = 'https://foo.cc.columbia.edu/api/v1/search'

        with self.assertRaises(APIPaginationException):
            next(self.test_client._get_paginated(url))

    @patch('canvas_api_client.v1_client.requests')
    def test_get_paginated(self, mock_requests):
        url = 'https://foo.cc.columbia.edu/api/v1/search'

        mock_response_1 = get_mock_response_with_pagination(url)

        mock_response_2 = MagicMock(
            headers={'link': url + 'page=2'})
        mock_response_2.json.return_value = {
            'value': 'second response'}

        mock_requests.get.side_effect = [mock_response_1, mock_response_2]

        generator = self.test_client._get_paginated(url)
        next_value = next(generator)
        assert 'value' in next_value
        assert next_value['value'] == 'first response'
        next_value = next(generator)
        assert 'value' in next_value
        assert next_value['value'] == 'second response'

        # there should be no additional pages to paginate, so expect an error:
        with self.assertRaises(StopIteration):
            next(generator)

    @patch('canvas_api_client.v1_client.requests')
    def test_get_account_courses(self, mock_requests):
        url = 'https://foo.cc.columbia.edu/api/v1/accounts/1/courses'

        mock_response_1 = get_mock_response_with_pagination(url)
        mock_requests.get.return_value = mock_response_1

        next(self.test_client.get_account_courses('1'))
        mock_requests.get.assert_called_once_with(
            url,
            params={},
            headers={'Authorization': 'Bearer foo_token'})

    @patch('canvas_api_client.v1_client.requests')
    def test_get_course_users(self, mock_requests):
        url = 'https://foo.cc.columbia.edu/api/v1/courses/sis_course_id:ASDFD5100_007_2018_1/users'

        mock_response_1 = get_mock_response_with_pagination(url)
        mock_requests.get.return_value = mock_response_1

        next(self.test_client.get_course_users('ASDFD5100_007_2018_1'))
        mock_requests.get.assert_called_once_with(
            url,
            params={},
            headers={'Authorization': 'Bearer foo_token'})

    @patch('canvas_api_client.v1_client.requests')
    def test_delete_enrollment(self, mock_requests):
        self.test_client.delete_enrollment(1234, 432432)
        url = 'https://foo.cc.columbia.edu/api/v1/courses/1234/enrollments/432432'
        mock_requests.delete.assert_called_once_with(
            url,
            params={},
            headers={'Authorization': 'Bearer foo_token'})
