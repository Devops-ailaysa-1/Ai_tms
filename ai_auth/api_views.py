from ai_auth.serializers import MyTokenObtainPairSerializer, OfficialInformationSerializer, PersonalInformationSerializer, ProfessionalidentitySerializer
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from ai_auth.serializers import RegisterSerializer,UserAttributeSerializer
from rest_framework import generics
from ai_auth.models import AiUser, OfficialInformation, PersonalInformation, Professionalidentity,UserAttribute
from django.http import Http404
from rest_framework import status
from django.db import IntegrityError
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import renderers

class MyObtainTokenPairView(TokenObtainPairView):
    permission_classes = (AllowAny,)
    serializer_class = MyTokenObtainPairSerializer


class RegisterView(generics.CreateAPIView):
    queryset = AiUser.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer



class UserAttributeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request,format=None):
        try:
            queryset = UserAttribute.objects.get(user_id=request.user.id)
        except UserAttribute.DoesNotExist:
            return Response(status=204)
        serializer = UserAttributeSerializer(queryset)
        return Response(serializer.data)


    def post(self, request):
        data = request.data
        serializer = UserAttributeSerializer(data=data, context={'request':request})

        if serializer.is_valid():
            try:
                serializer.save()
            except IntegrityError:
                return Response(serializer.errors, status=status.HTTP_409_CONFLICT)
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

    
    def patch(self, request, format=None):
        user_type = UserAttribute.objects.get(user_id=request.user.id)
        serializer = UserAttributeSerializer(user_type,
                                           data=request.data,
                                           partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class PersonalInformationView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request,format=None):
        try:
            queryset = PersonalInformation.objects.get(user_id=request.user.id)
        except PersonalInformation.DoesNotExist:
            return Response(status=204)

        serializer = PersonalInformationSerializer(queryset)
        return Response(serializer.data)

    def post(self, request):
        data = request.data
        print("Data==>",data)
        serializer = PersonalInformationSerializer(data=data, context={'request':request})

        if serializer.is_valid():
            try:
                serializer.save()
            except IntegrityError:
                return Response(serializer.errors, status=status.HTTP_409_CONFLICT)
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

    
    def patch(self, request, format=None):
        print(request.data)
        personal_info = PersonalInformation.objects.get(user_id=request.user.id)
        serializer = PersonalInformationSerializer(personal_info,
                                           data=request.data,
                                           partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OfficialInformationView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request,format=None):
        try:
            queryset = OfficialInformation.objects.get(user_id=request.user.id)
        except OfficialInformation.DoesNotExist:
            return Response(status=204)
        serializer = OfficialInformationSerializer(queryset)
        return Response(serializer.data)


    def post(self, request):
        data = request.data
        serializer = OfficialInformationSerializer(data=data, context={'request':request})

        if serializer.is_valid():
            try:
                serializer.save()
            except IntegrityError:
                return Response(serializer.errors, status=status.HTTP_409_CONFLICT)
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

    
    def patch(self, request, format=None):
        officaial_info = OfficialInformation.objects.get(user_id=request.user.id)
        serializer = OfficialInformationSerializer(officaial_info,
                                           data=request.data,
                                           partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class JPEGRenderer(renderers.BaseRenderer):
    media_type = 'image/png'
    format = 'png'
    charset = None
    render_style = 'binary'

    def render(self, data, media_type=None, renderer_context=None):
        return data


class ProfessionalidentityView(APIView):
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [IsAuthenticated]
    #renderer_classes=[JPEGRenderer,]

    def get_object(self, pk):
        try:
            return Professionalidentity.objects.get(user_id=pk)
        except Professionalidentity.DoesNotExist:
            raise Http404

    def get(self, request, format=None):
        photo = self.get_object(request.user.id)
        serializer = ProfessionalidentitySerializer(photo)
        return Response(serializer.data)

    def post(self, request, format=None):
        # print(request.data)
        # print(request.data.get('logo'))
        # print("files",request.FILES.get('logo'))
        serializer = ProfessionalidentitySerializer(data=request.data, context={'request':request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, format=None):
        identity = self.get_object(request.user.id)
        serializer = ProfessionalidentitySerializer(identity,
                                           data=request.data,
                                           partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


