from django.contrib import admin
from .models import AiUser, UserAttribute
from django.contrib.auth.models import Permission

# Register your models here.
admin.site.register(AiUser)
admin.site.register(UserAttribute)
admin.site.register(Permission)
