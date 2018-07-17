from unittest import TestCase
from unittest.mock import MagicMock, patch

from evalkit_api_client.v1_client import EvalKitAPIv1
from evalkit_api_client.errors import APIPaginationException


class TestEvalKitAPIv1Client(TestCase):

    def setUp(self):
        self.base_url = 'https://sub.evaluationkit.com/api/v1'
        self.token = 'foo_token'
        self.client = EvalKitAPIv1(
            self.base_url,
            self.token)

    def test_send_request(self):
        url = self.client._get_url('foo')

        mock_callback = MagicMock()
        mock_response = MagicMock(ok=True)
        mock_callback.return_value = mock_response



        self.client._send_request(
            mock_callback,
            url,
            exit_on_error=True,
            headers={'foo': 'bar'},
            params={
                'x': 'y'
            })

        mock_response.raise_for_status.assert_called_once_with()
        mock_callback.assert_called_once_with(
            url,
            headers={'foo': 'bar', 'AuthToken': 'foo_token'},
            params={'x': 'y'})

    def test_send_request_not_ok(self):
        url = self.client._get_url('foo')

        mock_callback = MagicMock()
        mock_response = MagicMock(ok=False, url=url)
        mock_callback.return_value = mock_response

        with self.assertLogs(level='DEBUG'):
            self.client._send_request(
                mock_callback,
                url,
                exit_on_error=True,
                headers={'foo': 'bar'},
                params={
                    'x': 'y'
                })

        mock_response.raise_for_status.assert_called_once_with()

    def test_get_paginated_exception(self):
        self.client._get = MagicMock()
        self.client._get.return_value.json.return_value = {}
        url = 'baz'

        with self.assertRaises(APIPaginationException):
            res = list(self.client._get_paginated(url))

        self.client._get.assert_called_once_with(
            url,
            headers=None,
            params={'page': 1})

    def test_get_paginated_one_page(self):
        self.client._get = MagicMock()
        self.client._get.return_value.json.return_value = {
            'page': 1,
            'pageSize': 10,
            'resultList': [1,2,3,4,5,6]
        }
        url = 'baz'

        res = list(self.client._get_paginated(url))

        self.client._get.assert_called_once_with(
            url,
            headers=None,
            params={'page': 1})

        assert res == [{
            'page': 1,
            'pageSize': 10,
            'resultList': [1,2,3,4,5,6]
        }]

    def test_get_paginated_multiple_pages(self):
        self.client._get = MagicMock()
        resp1 = MagicMock()
        resp1.json.return_value = {
            'page': 1,
            'pageSize': 10,
            'resultList': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        }
        resp2 = MagicMock()
        resp2.json.return_value = {
            'page': 2,
            'pageSize': 10,
            'resultList': [1, 2, 3, 4, 5, 6, 7, 8, 9]
        }
        self.client._get.side_effect = [resp1, resp2]

        url = 'baz'

        res = list(self.client._get_paginated(url))

        assert self.client._get.call_count == 2

        assert res == [{
            'page': 1,
            'pageSize': 10,
            'resultList': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        }, {
            'page': 2,
            'pageSize': 10,
            'resultList': [1, 2, 3, 4, 5, 6, 7, 8, 9]
        }]
