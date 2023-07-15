from rest_framework import permissions
from ai_bi.models import BiUser

class IsBiUser(permissions.BasePermission):
    
    def has_permission(self, request, view):
        if BiUser.objects.get(bi_user=request.user):
            return True

class IsBiAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        user=BiUser.objects.get(bi_user=request.user)
        if user.bi_role=="ADMIN":
            return True
        