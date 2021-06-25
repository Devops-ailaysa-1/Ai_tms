from ai_auth.serializers import MyTokenObtainPairSerializer
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView
from ai_auth.serializers import RegisterSerializer
from rest_framework import generics
from ai_auth.models import AiUser

class MyObtainTokenPairView(TokenObtainPairView):
    permission_classes = (AllowAny,)
    serializer_class = MyTokenObtainPairSerializer


class RegisterView(generics.CreateAPIView):
    queryset = AiUser.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer