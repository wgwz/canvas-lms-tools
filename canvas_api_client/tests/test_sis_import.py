import os
from unittest import TestCase
from unittest.mock import call, MagicMock, patch

from canvas_api_client import sis_import
from canvas_api_client.test_helpers import (mock_get_sis_import_status,
                                            get_import_complete_status,
                                            get_response_data_counts)

from requests import HTTPError

DEFAULT_CSV = 'courses.csv'


class TestSisImporter(TestCase):
    def setUp(self):
        self.api_client = MagicMock()
        self.importer = sis_import.SisImporter(self.api_client, 1)

    def test_assert_defaults(self):
        timeout = sis_import.DEFAULT_TIMEOUT_SECONDS
        self.assertFalse(self.importer._dryrun)
        self.assertEqual(self.importer._timeout, timeout)
        self.assertTrue(self.importer._wait_for_completion)

    def test_import_complete(self):
        response_json = {'progress': '100', 'workflow_state': 'imported'}
        self.importer._api_client = mock_get_sis_import_status([response_json])
        assert self.importer.is_import_complete('14589')

    def test_import_failed(self):
        response_json = {'progress': '100', 'workflow_state': 'failed'}
        self.importer._api_client = mock_get_sis_import_status([response_json])
        assert self.importer.is_import_complete('14589')

    def test_import_incomplete(self):
        response_json = {'progress': '50', 'workflow_state': 'importing'}
        self.importer._api_client = mock_get_sis_import_status([response_json])
        assert not self.importer.is_import_complete('14589')

    def test_start_import(self):
        mock_response = MagicMock()
        mock_response.json.return_value = {'errors': ['foo'], 'id': '10'}
        self.importer._api_client.import_sis_data.return_value = mock_response
        self.importer._start_import('foo.csv')

    @patch('time.sleep', return_value=None)
    @patch('time.time')
    def test_wait_for_completion(self, mock_time, mock_sleep):
        mock_time.side_effect = [
            1517933001.93932,  # start time.time()
            1517933002.93932,  # time.time() called by log function
            1517933032.93932,  # time.time() called by 1st while-loop iteration
            1517933062.93932  # time.time() called by 2nd while-loop iteration
        ]
        response1 = {'progress': 50, 'workflow_state': 'importing'}
        response2 = {'progress': 100, 'workflow_state': 'imported'}
        self.importer._api_client = mock_get_sis_import_status(
            [response1, response2])
        try:
            self.importer.wait_for_completion('14589')
        except sis_import.SisImportTimeoutError:
            self.fail(
                "_wait_for_completion() raised SisImportTimeoutError unexpectedly."
            )

    @patch('time.sleep', return_value=None)
    @patch('time.time')
    def test_wait_for_completion_timeout(self, mock_time, mock_sleep):
        mock_time.side_effect = [
            1517933001.93932,  # start time.time()
            1617933032.93932,  # time.time() called by log function
            1717933032.93932  # time.time() called by 1st while-loop iteration. Too high!
        ]
        response1 = {'progress': 50, 'workflow_state': 'importing'}
        response2 = {'progress': 50, 'workflow_state': 'importing'}
        self.importer._api_client = mock_get_sis_import_status(
            [response1, response2])
        with self.assertRaises(sis_import.SisImportTimeoutError):
            self.importer.wait_for_completion('14589')

    @patch('canvas_api_client.sis_import.logger')
    def test_log_final_response(self, mock_logger):
        processing_warnings = [[
            'students.csv', ('user John Doe has already claimed john_doe\'s '
                             'requested login information, skipping')
        ]]
        processing_errors = [[
            'students.csv',
            'Error while importing CSV. Please contact support.'
        ]]
        response_dict = {
            'progress': 100,
            'workflow_state': 'imported',
            'processing_warnings': processing_warnings,
            'processing_errors': processing_errors
        }
        self.importer._log_final_response(sis_import.SisImport(response_dict))
        mock_logger.warn.assert_called_once_with(
            'Below warning occurred while importing {} file:\n{}'.format(
                processing_warnings[0][0], processing_warnings[0][1]))
        mock_logger.error.assert_called_once_with(
            'Below warning occurred while importing {} file:\n{}'.format(
                processing_errors[0][0], processing_errors[0][1]))

    @patch('time.sleep', return_value=None)
    @patch('time.time')
    def test_import_csv(self, mock_time, mock_sleep):
        mock_time.side_effect = [
            1517933001.93932,  # start time.time()
            1517933002.13932,  # time.time() called by 1st log function
            1517933002.93932,  # time.time() called by 2nd log function
            1517933002.93932,  # time.time() called by 3rd log function
            1517933032.93932,  # time.time() called by 1st while-loop iteration
            1517933062.93932  # time.time() called by 2nd while-loop iteration
        ]
        response_json0 = {
            'id': 13012,
            'progress': 0,
            'workflow_state': 'created'
        }
        response_json1 = {'progress': 50, 'workflow_state': 'importing'}
        response_json2 = {'progress': 100, 'workflow_state': 'imported'}
        response_json3 = {'progress': 100, 'workflow_state': 'imported'}

        mock_first_response = MagicMock()
        mock_first_response.json.return_value = response_json0
        self.importer._api_client = mock_get_sis_import_status(
            [response_json1, response_json2, response_json3])
        self.importer._api_client.import_sis_data.return_value = mock_first_response

        response = self.importer.import_csv('foo.csv')
        self.assertEqual(response.json(), response_json3)

    def test_import_csv_dryrun(self):
        self.importer._dryrun = True
        response = self.importer.import_csv('foo.csv')
        self.assertEqual(response, None)
