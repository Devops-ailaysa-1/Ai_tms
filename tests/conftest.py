import pytest
from django.core.management import call_command
from rest_framework.test import APIClient
from django.db import IntegrityError
from ai_auth.models import AiUser,UserAttribute   
from allauth.account.models import EmailAddress
from django.contrib.auth.hashers import check_password,make_password
from tests import get_fixture_path

@pytest.fixture
def api_client():
   return APIClient


@pytest.fixture
def api_client_with_credentials(
   db, api_client,django_user_model,test_create
    ):
    user = django_user_model.objects.get(email='stephenlangtest@gmail.com')
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {pytest.access_token}')
    # yield api_client
    # api_client.force_authenticate(user=None)


def pytest_deselected(items):
    if not items:
        return
    config = items[0].session.config
    reporter = config.pluginmanager.getplugin("terminalreporter")
    reporter.ensure_newline()
    for item in items:
        reporter.line(f"deselected: {item.nodeid}", yellow=True, bold=True)


def pytest_configure():
    pytest.access_token = ''
    pytest.refresh_token = ''
    pytest.task_id =None
    pytest.project_id = None
    pytest.job_id = None



@pytest.fixture
def task_id(task):
    task_id =task
    return task_id



# @pytest.fixture
# def task_id(task):
#     return task 

# @pytest.fixture
# def token_assign():
#     return pytest.access_token 

@pytest.fixture
def db_no_rollback(request, django_db_setup, django_db_blocker):
    django_db_blocker.unblock()
    request.addfinalizer(django_db_blocker.restore)

# @pytest.fixture(name= "")
# def django_db_setup(django_db_setup, django_db_blocker):
#     with django_db_blocker.unblock():
#         call_command('loaddata', 'fixtures/aistaff.json')


@pytest.fixture(scope='session')
def django_db_setup(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        call_command('loaddata', 'fixtures/aistaff.json')
        call_command('loaddata', 'fixtures/aiuser_re.json')
        call_command('loaddata', 'fixtures/stripe_customer.json')
        call_command('loaddata', 'fixtures/userattribute.json')
        call_command('loaddata', 'fixtures/emailaddress.json')
        call_command('loaddata', 'fixtures/steps.json')
        call_command('loaddata', 'fixtures/user_credits.json')
        call_command('loaddata', 'fixtures/ChoiceLists.json')
        # call_command('loaddata', 'fixtures/ChoiceListSelected.json')
        call_command('loaddata', 'fixtures/SelflearningAsset.json')
        # call_command('loaddata', 'fixtures/Project.json')
        # call_command('loaddata', 'fixtures/Account.json')
        # call_command('loaddata', 'fixtures/Product.json')
        # call_command('loaddata', 'fixtures/Plan.json')
        # call_command('loaddata', 'fixtures/Price.json')
        # call_command('loaddata', 'fixtures/AilaysaCampaigns.json')
        # call_command('loaddata', 'fixtures/prompt_categories.json')
        # call_command('loaddata', 'fixtures/prompt_sub_categories.json')
        # call_command('loaddata', 'fixtures/prompt_start_phrases.json')
        # call_command('loaddata', 'fixtures/prompt_tone.json')
        # call_command('loaddata', 'fixtures/ai_customize.json')

        from djstripe.models import Account
        default_djstripe_owner=Account.objects.first()
        
                
# @pytest.fixture
# def test_create():     
#     create_user("stephenlangtest@gmail.com","stephenlangtest@gmail.com",101,'test@123#')

# def create_user(name,email,country,password):
#     #password = AiUser.objects.make_random_password()
#     hashed = make_password(password)
#     print("randowm pass",password)
#     try:
#         user = AiUser.objects.create(fullname =name,email = email,country_id=country,password = hashed)
#         UserAttribute.objects.create(user=user)
#         EmailAddress.objects.create(email = email, verified = True, primary = True, user = user)
#     except IntegrityError as e:
#         print("Intergrity error",str(e))
#         return None
#     return user,password



        # if record['id'] == 4:
        #     assert record['first_name'] == "Eve",\
        #         "Data not matched! Expected : Eve, but found : " + str(record['first_name'])
        #     assert record['last_name'] == "Holt",\
        #         "Data not matched! Expected : Holt, but found : " + str(record['last_name'])




# @pytest.fixture
# def user_create_data(django_db_setup, django_db_blocker):  
#     with django_db_blocker.unblock():
#         call_command('loaddata', get_fixture_path("aiuser_re.json"))



@pytest.fixture(scope="class")
def load_djstipe_acc(db):
    from djstripe.models import Account
    default_djstripe_owner=Account.objects.first()
