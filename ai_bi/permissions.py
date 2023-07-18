from rest_framework import permissions
from ai_bi.models import BiUser


class IsBiUser(permissions.BasePermission):
    
    def has_permission(self, request, view):
        try:
            if request.user.id !=None:
                user=BiUser.objects.get(bi_user=request.user)
                if user:
                    return True
        except BiUser.DoesNotExist:
            return False

class IsBiAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        try:
            if request.user.id !=None:
                user=BiUser.objects.get(bi_user=request.user)
                if user.bi_role=="ADMIN":
                    return True
        except BiUser.DoesNotExist:
            return False
        