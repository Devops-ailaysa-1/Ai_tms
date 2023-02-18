from ai_auth.models import AiUser,UserAttribute
from allauth.account.models import EmailAddress
import pytest
from django.db import IntegrityError
from django.contrib.auth.hashers import check_password,make_password
import django.apps



# class TestSubjectModel():
#     def test_list():



# def test_contributors_cannot_delete_repos(oso):
#     repo = Repository("oso")
#     contributor = User([Role(name="contributors", repository=repo)])
#     with pytest.raises(ForbiddenError):
#         oso.authorize(contributor, "read", repo)

# class TestAllModelOwnerPermission:
#     def test_ai_auth_models(user):
#         if user != None:
#             django.apps.apps.get_models()

#     def test_ai_workspace_models():
#         pass
