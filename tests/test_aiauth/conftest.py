import pytest
import json 
import os

# @pytest.fixture
# def api_client():
#    from rest_framework.test import APIClient
#    return APIClient

# def pytest_collection_modifyitems(items):
#     for item in items:
#         item.add_marker('all')
        


# @pytest.fixture
# def user_data(request):
#     with open('data.json') as f:
#         data = json.load(f)
#     return data[request.param]


@pytest.fixture()
def signup_test_data(request):
    return request.param

@pytest.fixture()
def signin_test_data(request):
    return request.param

#in conftest.py
def pytest_generate_tests(metafunc):
    if "signup_test_data" in metafunc.fixturenames:
        data = get_test_json_data('test_signup.json')
        k =[]
        for i in range(0,len(data['input']['email'])):
            l = list()
            for j in  list(data['input'].keys()):
                l.append(data['input'][j][i])
            k.append((tuple(l),data['output']['status'][i]))
            

        metafunc.parametrize('signup_test_data', k, indirect=True)

    if "signin_test_data" in metafunc.fixturenames:
        data = get_test_json_data('test_signin.json')
        k =[]
        for i in range(0,len(data['input']['email'])):
            l = list()
            for j in  list(data['input'].keys()):
                l.append(data['input'][j][i])
            k.append((tuple(l),data['output']['status'][i]))
            

        metafunc.parametrize('signin_test_data', k, indirect=True)




# def get_test_data(filename):
#     folder_path = os.path.abspath(os.path.dirname(__file__))
#     folder = os.path.join(folder_path, 'fixtures')
#     jsonfile = os.path.join(folder, filename)
#     with open(jsonfile) as file:
#         data = json.load(file)

#     list(data['input'].keys())

#     # for i in data[]

#     valid_data = [(item, 1) for item in data['valid_data']]
#     invalid_data = [(item, 0) for item in data['invalid_data']]

#     # data below is a list of tuples, with first element in the tuple being the 
#     # arguments for the API call and second element specifies if this is a test 
#     # from valid_data set or invalid_data. This can be used for putting in the
#     # appropriate assert statements for the API response.
#     data = valid_data + invalid_data

#     return data


def get_test_json_data(filename):
    folder_path = os.path.abspath(os.path.dirname(__file__))
    folder = os.path.join(folder_path, 'fixtures')
    jsonfile = os.path.join(folder, filename)  
    with open(jsonfile) as file:
        data = json.load(file)
    return data



    # input = [(item, 1) for item in data['input']]
    # invalid_data = [(item, 0) for item in data['invalid_data']] 


# def test_(test_data):
#     response = database_api.get_user_info(test_data[0])