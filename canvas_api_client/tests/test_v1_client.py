import os

from canvas_api_client.v1_client import CanvasAPIv1
from canvas_api_client.errors import APIPaginationException

from unittest import (skipIf, TestCase)
from unittest.mock import MagicMock, patch, mock_open

DEFAULT_PARAMS = {'per_page': 100}

def get_mock_response_with_pagination(url):
    mock_response = MagicMock(
        headers={'link': url + 'page=1'},
        links={
            'next': {
                'url': url + 'page=2'
            }
        })
    mock_response.json.return_value = {'value': 'first response'}
    return mock_response


def _assert_request_called_once_with(mock_request_object, url, params=None, **kwargs):
    """
    Execute assert_called_once_with() on a unittest.mock object with default logic.
    """
    if params is None:
        params = DEFAULT_PARAMS
    mock_request_object.assert_called_once_with(
        url, params=params, headers={
            'Authorization': 'Bearer foo_token'
        }, **kwargs)


class TestCanvasAPIv1Client(TestCase):

    def setUp(self,):
        self._mock_requests = MagicMock()
        self.test_client = CanvasAPIv1('https://foo.cc.columbia.edu/api/v1/',
                                       'foo_token',
                                       requests_lib=self._mock_requests)

    # TODO(lcary): https://github.com/lcary/canvas-lms-tools/issues/3
    @skipIf("TRAVIS" in os.environ and os.environ["TRAVIS"] == "true",
            "Skipping this test on Travis CI due to nonsensical error.")
    def test_send_request(self):
        mock_response = MagicMock()

        test_callback = self._mock_requests.get
        test_callback.return_value = mock_response

        url = 'https://foo.cc.columbia.edu/api/v1/search'

        returned_response = self.test_client._send_request(
            test_callback,
            url,
            exit_on_error=True,
            headers={'foo': 'bar'},
            params={
                'x': 'y'
            })

        returned_response.raise_for_status.assert_called_once_with()
        test_callback.assert_called_once_with(
            url,
            headers={'foo': 'bar',
                     'Authorization': 'Bearer foo_token'},
            params={
                'x': 'y',
                'per_page': 100
            })

    def test_get_paginated_exception(self):
        mock_response = MagicMock()
        mock_response.headers = {}
        mock_response.json.return_value == {}

        self._mock_requests.get.return_value = mock_response

        url = 'https://foo.cc.columbia.edu/api/v1/search'

        with self.assertRaises(APIPaginationException):
            next(self.test_client._get_paginated(url))

    def test_get_paginated(self):
        url = 'https://foo.cc.columbia.edu/api/v1/search'

        mock_response_1 = get_mock_response_with_pagination(url)

        mock_response_2 = MagicMock(headers={'link': url + 'page=2'})
        mock_response_2.json.return_value = {'value': 'second response'}

        self._mock_requests.get.side_effect = [mock_response_1, mock_response_2]

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

    def test_get_account_courses(self):
        url = 'https://foo.cc.columbia.edu/api/v1/accounts/1/courses'

        mock_response_1 = get_mock_response_with_pagination(url)
        self._mock_requests.get.return_value = mock_response_1

        next(self.test_client.get_account_courses('1'))
        _assert_request_called_once_with(self._mock_requests.get, url)

    def test_get_course_users(self):
        url = 'https://foo.cc.columbia.edu/api/v1/courses/57000/users'

        mock_response_1 = get_mock_response_with_pagination(url)
        self._mock_requests.get.return_value = mock_response_1

        next(self.test_client.get_course_users('57000'))
        _assert_request_called_once_with(self._mock_requests.get, url)

    def test_get_sis_course_users(self):
        course = 'ASDFD5100_007_2018_1'
        url = 'https://foo.cc.columbia.edu/api/v1/courses/sis_course_id:{}/users'.format(
            course)

        mock_response_1 = get_mock_response_with_pagination(url)
        self._mock_requests.get.return_value = mock_response_1

        generator = self.test_client.get_course_users(
            course, is_sis_course_id=True)
        next(generator)
        _assert_request_called_once_with(self._mock_requests.get, url)

    def test_delete_enrollment(self):
        self.test_client.delete_enrollment(1234, 432432)
        url = 'https://foo.cc.columbia.edu/api/v1/courses/1234/enrollments/432432'
        _assert_request_called_once_with(self._mock_requests.delete, url)

    def test_delete_enrollment_sis_course_id(self):
        course = 'ASDFD5100_007_2018_2'
        self.test_client.delete_enrollment(
            course, 432432, is_sis_course_id=True)
        course_str = "sis_course_id:{}".format(course)
        url = 'https://foo.cc.columbia.edu/api/v1/courses/{}/enrollments/432432'.format(
            course_str)
        _assert_request_called_once_with(self._mock_requests.delete, url)

    def test_delete_enrollment_delete_with_params(self):
        params = {'task': 'delete'}
        self.test_client.delete_enrollment(1234, 432432, params=params)
        url = 'https://foo.cc.columbia.edu/api/v1/courses/1234/enrollments/432432'
        _assert_request_called_once_with(
            self._mock_requests.delete, url, params=params)

    def test_put_page(self):
        course = 'ASDFD5100_007_2018_2'
        url = 'test_page'
        title = 'Test Title'
        body = '<html><body><h1>Test Title</h1><p>Foo</p></body></html>'
        data = {
            'wiki_page[url]': url,
            'wiki_page[published]': True,
            'wiki_page[notify_of_update]': False,
            'wiki_page[title]': title,
            'wiki_page[front_page]': False,
            'wiki_page[body]': body
            }

        self.test_client.put_page(
            course,
            is_sis_course_id=True,
            url=url,
            title=title,
            body=body
            )
        course_str = 'sis_course_id:{}'.format(course)
        url = 'https://foo.cc.columbia.edu/api/v1/courses/{}/pages/{}'.format(
            course_str,
            url
            )

        _assert_request_called_once_with(
            self._mock_requests.put,
            url,
            params=DEFAULT_PARAMS,
            data=data
            )


    def test_import_sis_data(self):
        url = 'https://foo.cc.columbia.edu/api/v1/accounts/1/sis_imports'
        with patch('builtins.open', mock_open(read_data="foo")):
            self.test_client.import_sis_data('1', 'foo.csv')
            with open('foo.csv', 'rb') as f:
                files = {'attachment': f}
                _assert_request_called_once_with(
                    self._mock_requests.post,
                    url,
                    params=DEFAULT_PARAMS,
                    files=files
                    )

    def test_import_sis_data_file_not_found(self):
        m = mock_open()
        m.side_effect = FileNotFoundError
        with patch('builtins.open', m):
            with self.assertRaises(FileNotFoundError):
                self.test_client.import_sis_data('1', 'foo.csv')
                assert not self._mock_requests.post.called

    def test_get_sis_import_status(self):
        self.test_client.get_sis_import_status('1', '14809')
        url = 'https://foo.cc.columbia.edu/api/v1/accounts/1/sis_imports/14809'
        _assert_request_called_once_with(self._mock_requests.get, url)

    def test_get_account_roles(self):
        self.test_client.get_account_roles('1')
        url = 'https://foo.cc.columbia.edu/api/v1/accounts/1/roles'
        _assert_request_called_once_with(self._mock_requests.get, url)

    def test_get_account_roles_sis(self):
        self.test_client.get_account_roles('ASDF', is_sis_account_id=True)
        url = 'https://foo.cc.columbia.edu/api/v1/accounts/sis_account_id:ASDF/roles'
        _assert_request_called_once_with(self._mock_requests.get, url)
