from rest_framework import permissions


class BIuser(permissions.BasePermission):

    def has_permission(self, request, view):
        if request.user.is_staff or request.user.is_superuser:
            return True
