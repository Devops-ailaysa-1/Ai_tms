import requests
import pytest


test_base_url ="http://localhost:8087"

pytestmark = pytest.mark.unit


def test_api_get():
    url = f"{test_base_url}/auth/dj-rest-auth/login/"
    payload={'email': 'stephenlangtest+loc45v@gmail.com',
    'password': 'admin@1000'}
    response = requests.request("POST", url, data=payload)


    assert (response.status_code == 200), "Status code is not 200. Rather found : " + str(response.status_code)
    data= response.json()
    assert data.get('access_token',None) != None,"access token not found"

        # if record['id'] == 4:
        #     assert record['first_name'] == "Eve",\
        #         "Data not matched! Expected : Eve, but found : " + str(record['first_name'])
        #     assert record['last_name'] == "Holt",\
        #         "Data not matched! Expected : Holt, but found : " + str(record['last_name'])


# @pytest.mark.dependency()