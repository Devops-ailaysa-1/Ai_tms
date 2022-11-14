import pytest

@pytest.fixture
def api_client():
   from rest_framework.test import APIClient
   return APIClient()

def pytest_collection_modifyitems(items):
    for item in items:
        item.add_marker('all')
        