from unittest import TestCase

from canvas_api_client.models.sis_import import (
    FieldNotFoundError, get_response_field, has_non_empty_field,
    PROCESSING_ERRORS_KEY, PROCESSING_WARNINGS_KEY, SisImport)


class TestSisImportModel(TestCase):
    def test_get_response_field(self):
        assert get_response_field({'foo': 'bar'}, 'foo') == 'bar'

    def test_get_response_field_error(self):
        with self.assertRaises(FieldNotFoundError):
            get_response_field({'foo': 'bar'}, 'baz')

    def test_has_non_empty_field(self):
        self.assertFalse(has_non_empty_field({}, 'errors'))
        self.assertFalse(has_non_empty_field({'errors': []}, 'errors'))
        self.assertTrue(has_non_empty_field({'errors': ['foo']}, 'errors'))

    def test_id(self):
        self.assertEqual(SisImport({'id': 30}).id, 30)

    def test_has_errors(self):
        self.assertFalse(SisImport({}).has_errors)
        self.assertTrue(SisImport({'errors': ['foo']}).has_errors)

    def test_errors(self):
        self.assertEqual(SisImport({'errors': ['foo']}).errors, ['foo'])

    def test_has_processing_warnings(self):
        r = {PROCESSING_WARNINGS_KEY: [['foo.csv', 'warning!']]}
        self.assertFalse(SisImport({}).has_processing_warnings)
        self.assertTrue(SisImport(r).has_processing_warnings)

    def test_processing_warnings(self):
        warnings = [['foo.csv', 'warning!']]
        r = {PROCESSING_WARNINGS_KEY: warnings}
        self.assertTrue(SisImport(r).processing_warnings, warnings)

    def test_has_processing_errors(self):
        r = {PROCESSING_ERRORS_KEY: [['foo.csv', 'error!']]}
        self.assertFalse(SisImport({}).has_processing_errors)
        self.assertTrue(SisImport(r).has_processing_errors)

    def test_processing_errors(self):
        errors = [['foo.csv', 'error!']]
        r = {PROCESSING_ERRORS_KEY: errors}
        self.assertTrue(SisImport(r).has_processing_errors, errors)

    def test_progress(self):
        r = {'progress': '100'}
        self.assertEqual(SisImport(r).progress, '100')

    def test_workflow_state(self):
        r = {'workflow_state': 'imported'}
        self.assertEqual(SisImport(r).workflow_state, 'imported')

    def test_is_complete(self):
        r = {'workflow_state': 'imported'}
        self.assertTrue(SisImport(r).is_complete)

    def test_is_not_complete(self):
        r = {'workflow_state': 'NOT COMPLETE'}
        self.assertFalse(SisImport(r).is_complete)
