import re
from rest_framework import permissions
from rest_framework import authentication 
from ai_auth.models import UserAttribute, AiUser
from django.contrib.auth.backends import BaseBackend
from bcrypt import checkpw

class IsCustomer(permissions.BasePermission):
    """
    Object-level permission to only allow owners of an object to edit it.
    Assumes the model instance has an `owner` attribute.
    """

    def has_object_permission(self, request, view):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        # if request.method in permissions.SAFE_METHODS:
        #     return True

        # Instance must have an attribute named `owner`.
 
        print("Is Customer checking...")
        return UserAttribute.objects.get(user=request.user).user_type == 1 

class MysqlBackend(BaseBackend):
    """Extra Backend Authetication for Migrated MySql User Records"""
    def authenticate(self, request, email=None, password=None):
        # print("Mysql Backend Autentication")
        ai_user = AiUser.objects.filter(email=email).first()
        # print("Firt if ---> ",password.encode("utf-8"))
        if ai_user and ai_user.password.startswith('pbkdf2'):
            ai_user.from_mysql = False
            ai_user.save()
            return None
            
        if ai_user and (ai_user.from_mysql==True):
            # print("Firt if ---> ",password.encode("utf-8"))
            if checkpw( password.encode("utf-8") , ai_user.password.encode("utf-8") ):
                # print("sECOND IF CONDITION-----", ai_user.password.encode("utf-8"))
                ai_user.set_password(password)
                
                ai_user.from_mysql = False  
                ai_user.save()
                # print("savedddddddddddd")
                return ai_user
            else: return None 
        else:
            return None 


    def get_user(self, pk):
        try:
            return AiUser.objects.get(pk=pk)
        except AiUser.DoesNotExist:
            pass
        return None
    

class APIAuthentication(authentication.TokenAuthentication):
    '''
    Change Autorization header keyword
    '''
    keyword = 'Api-Key'