'''
Helper functions for running unit tests.
'''
from uniitest.mock import MagicMock


def mock_get_sis_import_status(sis_imports):
    """
    Mock a get_sis_import_status() response obect
    """
    responses = []
    for sis_import in sis_imports:
        response = MagicMock()
        response.json.return_value = sis_import
        responses.append(response)
    api_client = MagicMock()
    api_client.get_sis_import_status.side_effect = responses
    return api_client


def get_import_complete_status():
    return {'id': 13012,
            'progress': 100,
            'workflow_state': 'imported'}

def get_response_data_counts():
    return {
        'data': {
            'counts': {
                'change_sis_ids': 0,
                'accounts': 0,
                'terms': 0,
                'abstract_courses': 0,
                'courses': 0,
                'sections': 0,
                'xlists': 0,
                'users': 0,
                'enrollments': 0,
                'admins': 0,
                'group_categories': 0,
                'groups': 0,
                'group_memberships': 0,
                'grade_publishing_results': 0,
                'user_observers': 0,
                'error_count': 0,
                'warning_count': 0
            },
            'supplied_batches': []
        }
    }
