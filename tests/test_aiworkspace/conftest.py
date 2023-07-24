import pytest
from tests import get_fixture_path
from django.core.management import call_command

# def pytest_collection_modifyitems(items):
#     for item in items:
#         item.add_marker('all')

import json
@pytest.fixture
def selflearningasset():
    with open('fixtures/SelflearningAsset.json') as f:
        data = json.load(f)
    return data

@pytest.fixture
def choicelist():
    with open('fixtures/ChoiceLists.json') as f:
        data = json.load(f)
    return data

@pytest.fixture
def choicelistselected():
    with open ("fixtures/ChoiceListSelected.json") as f:
        data=json.load(f)
    return data

@pytest.fixture
def document():
    with open ("fixtures/Document.json") as f:
        data=json.load(f)
    return data
