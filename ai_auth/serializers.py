from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework.validators import UniqueValidator
from django.contrib.auth.password_validation import validate_password
from ai_auth.models import AiUser


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):

    @classmethod
    def get_token(cls, user):
        token = super(MyTokenObtainPairSerializer, cls).get_token(user)

        # Add custom claims
        token['username'] = user.email
        return token



class RegisterSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
            required=True,
            validators=[UniqueValidator(queryset=AiUser.objects.all())]
            )

    password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = AiUser
        fields = ('password', 'email', 'fullname')
        extra_kwargs = {
            'fullname': {'required': True}
        }

 
    def create(self, validated_data):
        user = AiUser.objects.create(
            email=validated_data['email'],
            fullname=validated_data['fullname'],
        )

        
        user.set_password(validated_data['password'])
        user.save()

        return user