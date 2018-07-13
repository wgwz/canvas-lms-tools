from canvas_api_client.v1_client import CanvasAPIv1
from canvas_api_client.errors import APIPaginationException

from unittest import TestCase, main
from unittest.mock import MagicMock, patch, mock_open

from requests import HTTPError

DEFAULT_PARAMS = {'per_page': 100}

TEST_TOKEN = 'foo_token'
TEST_HEADERS = {
    'Authorization': 'Bearer {}'.format(TEST_TOKEN),
    'params': DEFAULT_PARAMS
    }

TEST_LIST = [
    'item 0',
    'item 1',
    'item 2',
    'item 3'
    ]

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


def get_mock_response_array_with_pagination(url):
    mock_response = MagicMock(
        headers={'link': url + 'page=1'},
        links={
            'next': {
                'url': url + 'page=2'
            }
        })
    mock_response.json.return_value = TEST_LIST[0:2]
    return mock_response


def _assert_request_called_once_with(mock_request_object, url, params=None, **kwargs):
    """
    Execute assert_called_once_with() on a unittest.mock object with default logic.
    """
    if params is None:
        params = {}

    params.update(DEFAULT_PARAMS)
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

    @patch('canvas_api_client.v1_client.logger')
    def test_send_request_not_ok(self, mock_logger):
        url = 'https://foo.cc.columbia.edu/api/v1/search'
        mock_response = MagicMock(ok=False, url=url)

        test_callback = self._mock_requests.get
        test_callback.return_value = mock_response

        returned_response = self.test_client._send_request(
            test_callback,
            url,
            exit_on_error=True,
            headers={'foo': 'bar'},
            params={
                'x': 'y'
            })
        debug_msg = 'Error status code for url "{}"'.format(url)
        mock_logger.debug.assert_called_once_with(debug_msg)

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

    def test_get_flattened_exception(self):
        mock_response = MagicMock()
        mock_response.headers = {}
        mock_response.json.return_value == {}

        self._mock_requests.get.return_value = mock_response

        url = 'https://foo.cc.columbia.edu/api/v1/search'

        with self.assertRaises(APIPaginationException):
            next(self.test_client._get_flattened(url))

    def test_get_flattened(self):
        url = 'https://foo.cc.columbia.edu/api/v1/search'

        mock_response_1 = get_mock_response_array_with_pagination(url)

        mock_response_2 = MagicMock(headers={'link': url + 'page=2'})
        mock_response_2.json.return_value = TEST_LIST[2:4]

        self._mock_requests.get.side_effect = [
            mock_response_1, mock_response_2
            ]

        generator = self.test_client._get_flattened(url)

        for idx, target_item in enumerate(TEST_LIST, start=0):
            next_value = next(generator)
            self.assertEqual(next_value, TEST_LIST[idx])

        # there should be no additional items, so expect an error:
        with self.assertRaises(StopIteration):
            next(generator)

    def test_get_account_courses(self):
        url = 'https://foo.cc.columbia.edu/api/v1/accounts/1/courses'

        mock_response_1 = get_mock_response_with_pagination(url)
        self._mock_requests.get.return_value = mock_response_1

        next(self.test_client.get_account_courses('1'))
        _assert_request_called_once_with(self._mock_requests.get, url)

    def test_get_course_info(self):
        url = 'https://foo.cc.columbia.edu/api/v1/courses/57000'

        self.test_client.get_course_info('57000')
        _assert_request_called_once_with(self._mock_requests.get, url)

    def test_get_course_info_sis_id(self):
        url = 'https://foo.cc.columbia.edu/api/v1/courses/sis_course_id:ABCD'

        self.test_client.get_course_info('ABCD', is_sis_course_id=True)
        _assert_request_called_once_with(self._mock_requests.get, url)

    def test_get_course_info_with_params(self):
        url = 'https://foo.cc.columbia.edu/api/v1/courses/57000'
        params = {
            'include[]': ['term', 'total_students', 'teachers']
        }

        self.test_client.get_course_info('57000', params=params)

        _assert_request_called_once_with(
            self._mock_requests.get,
            url,
            params=params)

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
        params.update(DEFAULT_PARAMS)
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

    def test_update_course(self):
        self.test_client.update_course('ASDFD5100_007_2018_2', is_sis_course_id=True)
        url = ('https://foo.cc.columbia.edu/api/v1/courses/'
               'sis_course_id:ASDFD5100_007_2018_2')
        _assert_request_called_once_with(self._mock_requests.put, url)

    def test_update_course_error(self):
        self._mock_requests.put.side_effect = HTTPError
        with self.assertRaises(HTTPError):
            self.test_client.update_course('ASDFD5100_007_2018_2',
                is_sis_course_id=True)

    def test_publish_course(self):
        params = {'offer': 'true'}
        self.test_client.publish_course('ASDFD5100_007_2018_2', is_sis_course_id=True)
        url = ('https://foo.cc.columbia.edu/api/v1/courses/'
               'sis_course_id:ASDFD5100_007_2018_2')
        _assert_request_called_once_with(self._mock_requests.put, url, params=params)

    def test_publish_course_error(self):
        self._mock_requests.put.side_effect = HTTPError
        with self.assertRaises(HTTPError):
            self.test_client.publish_course('ASDFD5100_007_2018_2',
                is_sis_course_id=True)

    def test_associate_courses_to_blueprint(self):
        course_id = '66642'
        course_ids = ['66649', '66650', '66651', '66652', '66653']

        self.test_client.associate_courses_to_blueprint(
            course_id,
            course_ids)

        url = (
            "https://foo.cc.columbia.edu/api/v1/"
            "courses/{course_id}/blueprint_templates/"
            "default/update_associations").format(course_id=course_id)
        data = {
            'course_ids_to_add[]': course_ids
        }

        _assert_request_called_once_with(
            self._mock_requests.put,
            url,
            params=DEFAULT_PARAMS,
            data=data)

    def test_associate_courses_to_blueprint_error(self):
        self._mock_requests.put.side_effect = HTTPError
        with self.assertRaises(HTTPError):
            self.test_client.associate_courses_to_blueprint(
                'null',
                [])

    def test_get_account_blueprint_courses(self):
        account_id = '115'

        self.test_client.get_account_blueprint_courses(account_id)

        url = (
            "https://foo.cc.columbia.edu/api/v1/"
            "accounts/{account_id}/courses").format(account_id=account_id)
        params = {
            'blueprint': 'true',
            'include[]': ['subaccount', 'term']
        }

        _assert_request_called_once_with(
            self._mock_requests.get,
            url,
            params=params)

    def test_get_account_blueprint_courses_error(self):
        self._mock_requests.get.side_effect = HTTPError
        with self.assertRaises(HTTPError):
            self.test_client.get_account_blueprint_courses('null')


class TestCanvasAPIv1ClientParams(TestCase):

    def setUp(self,):
        self._mock_requests = MagicMock()

    def test_put_page_is_sis_course_id(self):
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

        test_client = CanvasAPIv1(
            'https://foo.cc.columbia.edu/api/v1/',
            'foo_token',
            requests_lib=self._mock_requests,
            is_sis_course_id=True
            )

        test_client.put_page(
            course,
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

    def test_get_account_roles_sis(self):
        test_client = CanvasAPIv1(
            'https://foo.cc.columbia.edu/api/v1/',
            'foo_token',
            requests_lib=self._mock_requests,
            is_sis_account_id=True
            )

        test_client.get_account_roles('ASDF')
        url = 'https://foo.cc.columbia.edu/api/v1/accounts/sis_account_id:ASDF/roles'
        _assert_request_called_once_with(self._mock_requests.get, url)


    def test_get_paginated_50(self):
        url = 'https://foo.cc.columbia.edu/api/v1/search'

        mock_response_1 = get_mock_response_with_pagination(url)

        mock_response_2 = MagicMock(headers={'link': url + 'page=2'})
        mock_response_2.json.return_value = {'value': 'second response'}

        self._mock_requests.get.side_effect = [
            mock_response_1, mock_response_2
            ]

        test_client = CanvasAPIv1(
            'https://foo.cc.columbia.edu/api/v1/',
            TEST_TOKEN,
            requests_lib=self._mock_requests,
            per_page=50
            )

        generator = test_client._get_paginated(url)

        next_value = next(generator)
        assert 'value' in next_value
        assert next_value['value'] == 'first response'
        next_value = next(generator)
        assert 'value' in next_value
        assert next_value['value'] == 'second response'

        print(self._mock_requests.get.mock_calls)

        # there should be no additional pages to paginate, so expect an error:
        with self.assertRaises(StopIteration):
            next(generator)


if __name__ == '__main__':
    main()
