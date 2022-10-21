from django import forms
# from django.contrib.auth.forms import UserCreationForm, UserChangeForm
# from ai_auth.models import AiUser

class UploadFileForm(forms.Form):
   insertfile = forms.FileField()




# class AiUserCreationForm(UserCreationForm):
#     """
#     A form that creats a custom user with no privilages
#     form a provided email and password.
#     """

#     def __init__(self, *args, **kargs):
#         super(AiUserCreationForm, self).__init__(*args, **kargs)
#         #del self.fields['username']

#     class Meta:
#         model = AiUser
#         fields = '__all__'

# class AiUserChangeForm(UserChangeForm):
#     """
#     A form for updating users. Includes all the fields on
#     the user, but replaces the password field with admin's
#     password hash display field.
#     """

#     def __init__(self, *args, **kargs):
#         super(AiUserChangeForm, self).__init__(*args, **kargs)
#         #del self.fields['username']

#     class Meta:
#         model = AiUser
#         fields = '__all__'
