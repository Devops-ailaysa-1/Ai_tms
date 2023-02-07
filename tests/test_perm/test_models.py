from ai_auth.models import AiUser,UserAttribute
import pytest
from django.db import IntegrityError
from django.contrib.auth.hashers import check_password,make_password
import django
from django.contrib import admin
# from model_bakery import baker

# app_models = apps.get_app_config('ai_auth').get_models()
# for model in app_models:
#     try:
#         admin.site.register(model)


# def test_ai_auth_models_owner():
#     app_models = apps.get_app_config('ai_auth').get_models()
#     for model in app_models:
#         pass



# def test_contributors_cannot_delete_repos(oso):
#     repo = Repository("oso")
#     contributor = User([Role(name="contributors", repository=repo)])
#     with pytest.raises(ForbiddenError):
#         oso.authorize(contributor, "read", repo)

# @pytest.mark.mod1
# @pytest.mark.django_db
# class TestAllModelOwnerPermission:
#     def test_ai_auth_models(self):
#         models = django.apps.apps.get_models()
#         print("count-->",len(models))
#         for mod in models:
#             obj =  mod.objects.last()
#             if obj != None:
#                 try:  
#                     obj.owner
#                     print("found",mod)
#                 except AttributeError:
#                     print("No owner",mod)
#             else:
#                 print("Table empty")

                    
#     def test_ai_workspace_models():
#         pass


# def test_ai_auth_models():
#     models = django.apps.apps.get_models()
#     print("count-->",len(models))
#     for mod in models:
#         obj =  mod.objects.last()
#         if obj != None:
#             try: 
#                 assert obj.owner
#                 print("found",mod)
#             except AttributeError:
#                 print("No owner",mod)
#         else:
#             print("Table empty",mod)