import os
from unittest import TestCase
from unittest.mock import call, MagicMock, patch

from canvas_api_client import sis_import
from canvas_api_client.test_helpers import (
    mock_get_sis_import_status,
    get_import_complete_status,
    get_response_data_counts)

from requests import HTTPError

DEFAULT_CSV = 'courses.csv'


class TestSisImportFunctions(TestCase):

    def test_get_field(self):
        assert sis_import._get_field({'foo': 'bar'}, 'foo') == 'bar'

    def test_get_field_error(self):
        with self.assertRaises(sis_import.FieldNotFoundError):
            sis_import._get_field({'foo': 'bar'}, 'baz')

    def test_import_complete(self):
        response = {'progress': 100, 'workflow_state': 'imported'}
        api_client = mock_get_sis_import_status([response])
        assert sis_import.is_import_complete(api_client, '1', '14589')

    def test_import_failed(self):
        response = {'progress': 100, 'workflow_state': 'failed'}
        api_client = mock_get_sis_import_status([response])
        assert sis_import.is_import_complete(api_client, '1', '14589')

    def test_import_incomplete(self):
        response = {'progress': 50, 'workflow_state': 'importing'}
        api_client = mock_get_sis_import_status([response])
        assert not sis_import.is_import_complete(api_client, '1', '14589')

    @patch('time.sleep', return_value=None)
    @patch('time.time')
    def test_wait_for_completion(self, mock_time, mock_sleep):
        mock_time.side_effect = [
            1517933001.93932,  # start time.time()
            1517933002.93932,  # time.time() called by log function
            1517933032.93932,  # time.time() called by 1st while-loop iteration
            1517933062.93932   # time.time() called by 2nd while-loop iteration
        ]
        response1 = {'progress': 50, 'workflow_state': 'importing'}
        response2 = {'progress': 100, 'workflow_state': 'imported'}
        api_client = mock_get_sis_import_status([response1, response2])
        try:
            sis_import._wait_for_completion(api_client, '1', '14589')
        except sis_import.SisImportTimeoutError:
            self.fail("_wait_for_completion() raised SisImportTimeoutError unexpectedly.")

    @patch('time.sleep', return_value=None)
    @patch('time.time')
    def test_wait_for_completion_timeout(self, mock_time, mock_sleep):
        mock_time.side_effect = [
            1517933001.93932,  # start time.time()
            1617933032.93932,  # time.time() called by log function
            1717933032.93932   # time.time() called by 1st while-loop iteration. Too high!
        ]
        response1 = {'progress': 50,
                        'workflow_state': 'importing'}
        response2 = {'progress': 50,
                        'workflow_state': 'importing'}
        api_client = mock_get_sis_import_status([response1, response2])
        with self.assertRaises(sis_import.SisImportTimeoutError):
            sis_import._wait_for_completion(api_client, '1', '14589',
                sis_import.DEFAULT_TIMEOUT_SECONDS)

    def test_log_sis_errors(self):
        processing_warnings = [["students.csv", 
            "user John Doe has already claimed john_doe's requested login information, skipping"]]
        processing_errors = [["students.csv",
            "Error while importing CSV. Please contact support."]]
        sis_import_response = {'progress': 100,
                      'workflow_state': 'imported',
                      'processing_warnings': processing_warnings,
                      'processing_errors': processing_errors}
        api_client = mock_get_sis_import_status([sis_import_response])
        (response, warnings, errors) = sis_import._log_sis_errors(
            api_client, '1', '14589')
        self.assertEqual(response, sis_import_response)
        self.assertEqual(warnings, [processing_warnings[0][1]])
        self.assertEqual(errors, [processing_errors[0][1]])

    @patch('time.sleep', return_value=None)
    @patch('time.time')
    def test_import_sis_csv(self, mock_time, mock_sleep):
        mock_time.side_effect = [
            1517933001.93932,  # start time.time()
            1517933002.13932,  # time.time() called by 1st log function
            1517933002.93932,  # time.time() called by 2nd log function
            1517933002.93932,  # time.time() called by 3rd log function
            1517933032.93932,  # time.time() called by 1st while-loop iteration
            1517933062.93932   # time.time() called by 2nd while-loop iteration
        ]
        response0 = {'id': 13012, 'progress': 0, 'workflow_state': 'created'}
        response1 = {'progress': 50, 'workflow_state': 'importing'}
        response2 = {'progress': 100, 'workflow_state': 'imported'}
        response3 = {'progress': 100, 'workflow_state': 'imported'}
        api_client = mock_get_sis_import_status([response1, response2, response3])
        import_response = MagicMock()
        import_response.json.return_value = response0
        api_client.import_sis_data.return_value = import_response

        (import_response, warnings, errors) = sis_import._import_sis_csv(
            api_client, '1', 'foo.csv')
        self.assertEqual((import_response, warnings, errors), (response3, [], []))


class TestSisImportClass(TestCase):

    def setUp(self):
        self.api_client = MagicMock()
        self.sis_import = sis_import.SisImport(self.api_client, 1)

    def _mock_sis_import_response(self, response_dict=None):
        if response_dict is None:
            response_dict = get_import_complete_status()
        response = MagicMock()
        response.json.return_value = response_dict
        self.api_client.import_sis_data.return_value = response
        self.api_client.get_sis_import_status.return_value = response
        return response_dict

    def test_assert_defaults(self):
        timeout = sis_import.DEFAULT_TIMEOUT_SECONDS
        self.assertFalse(self.sis_import._dryrun)
        self.assertDictEqual(self.sis_import._errors, {})
        self.assertDictEqual(self.sis_import._warnings, {})
        self.assertEqual(self.sis_import._timeout, timeout)
        self.assertFalse(self.sis_import._dryrun)

    def test_dryrun_check_stored_data(self):
        self.sis_import._dryrun = True
        self.sis_import.import_csv(DEFAULT_CSV)
        self.assertDictEqual(self.sis_import._warnings, {DEFAULT_CSV: []})
        self.assertDictEqual(self.sis_import._errors, {DEFAULT_CSV: []})

    def test_check_stored_data(self):
        self._mock_sis_import_response()
        self.sis_import.import_csv(DEFAULT_CSV)
        self.assertDictEqual(self.sis_import._warnings, {DEFAULT_CSV: []})
        self.assertDictEqual(self.sis_import._errors, {DEFAULT_CSV: []})

    def test_check_error(self):
        self.sis_import._errors[DEFAULT_CSV] = 'There was an error!'
        with self.assertRaises(sis_import.SisImportError):
            self.sis_import.check_errors()

    def test_check_error_none(self):
        try:
            self.sis_import.check_errors()
        except sis_import.SisImportError:
            self.fail("sis_import.check_errors() raised SisImportError unexpectedly.")
