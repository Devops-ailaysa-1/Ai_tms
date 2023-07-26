from django.contrib import admin

# Register your models here.
from ai_bi.models import BiUser,AiUserDetails


admin.site.register(BiUser)
admin.site.register(AiUserDetails)