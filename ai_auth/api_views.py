from ai_auth.serializers import OfficialInformationSerializer, PersonalInformationSerializer, ProfessionalidentitySerializer,UserAttributeSerializer,UserProfileSerializer
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from django.shortcuts import get_object_or_404
#from ai_auth.serializers import RegisterSerializer,UserAttributeSerializer
from rest_framework import generics , viewsets
from ai_auth.models import AiUser, OfficialInformation, PersonalInformation, Professionalidentity,UserAttribute,UserProfile
from django.http import Http404
from rest_framework import status
from django.db import IntegrityError
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import renderers
from djstripe.models import Customer,Price
import stripe
from django.conf import settings
# class MyObtainTokenPairView(TokenObtainPairView):
#     permission_classes = (AllowAny,)
#     serializer_class = MyTokenObtainPairSerializer

# class RegisterView(generics.CreateAPIView):
#     queryset = AiUser.objects.all()
#     permission_classes = (AllowAny,)
#     serializer_class = RegisterSerializer

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



# class JPEGRenderer(renderers.BaseRenderer):
#     media_type = 'image/png'
#     format = 'png'
#     charset = None
#     render_style = 'binary'

#     def render(self, data, media_type=None, renderer_context=None):
#         return data


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
        try:
            photo = Professionalidentity.objects.get(user_id=request.user.id)
        except Professionalidentity.DoesNotExist:
            return Response(status=204)
        serializer = ProfessionalidentitySerializer(photo)
        return Response(serializer.data)

    def post(self, request, format=None):
        # print(request.data)
        # print(request.data.get('logo'))
        # print("files",request.FILES.get('logo'))
        serializer = ProfessionalidentitySerializer(data=request.data, context={'request':request})
        if serializer.is_valid():
            try:
                serializer.save()
            except IntegrityError:
                return Response(serializer.errors, status=status.HTTP_409_CONFLICT)
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


class UserProfileCreateView(viewsets.ViewSet):
    def list(self,request):
        try:
            queryset = UserProfile.objects.get(user_id = self.request.user.id)
            print(queryset)
            serializer = UserProfileSerializer(queryset)
            return Response(serializer.data)
        except:
            return Response(status=status.HTTP_204_NO_CONTENT)

    # def get_queryset(self):
    #     queryset=UserProfile.objects.filter(user_id=self.request.user.id).all()
    #     return queryset

    def create(self,request):
        id = request.user.id
        serializer = UserProfileSerializer(data={**request.POST.dict(),'user':id})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response({'msg':'description already exists'}, status=status.HTTP_400_BAD_REQUEST)

    def update(self,request,pk=None):
        queryset = UserProfile.objects.get(user_id=self.request.user.id)
        serializer= UserProfileSerializer(queryset,data={**request.POST.dict()},partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors)


def create_checkout_session(user,price_id):
    domain_url = settings.CLIENT_BASE_URL
    if settings.STRIPE_LIVE_MODE == True :
        api_key = settings.STRIPE_LIVE_SECRET_KEY
    else:
        api_key = settings.STRIPE_TEST_SECRET_KEY    

    stripe.api_key = api_key

    checkout_session = stripe.checkout.Session.create(
        client_reference_id=user.id,
        success_url=domain_url + 'success?session_id={CHECKOUT_SESSION_ID}',
        cancel_url=domain_url + 'cancel/',
        payment_method_types=['card'],
        mode='subscription',
        line_items=[
            {
                'price': price_id,
                'quantity': 1,
            }
        ]
    )
    return checkout_session


def create_checkout_session_addon(user,price_id):
    domain_url = settings.CLIENT_BASE_URL
    if settings.STRIPE_LIVE_MODE == True :
        api_key = settings.STRIPE_LIVE_SECRET_KEY
    else:
        api_key = settings.STRIPE_TEST_SECRET_KEY    

    stripe.api_key = api_key

    checkout_session = stripe.checkout.Session.create(
        client_reference_id=user.id,
        success_url=domain_url + 'success?session_id={CHECKOUT_SESSION_ID}',
        cancel_url=domain_url + 'cancel/',
        payment_method_types=['card'],
        mode='payment',
        customer = 'cus_K66n5FtHzVSLw0',
        line_items=[
            {
                'price': price_id,
                'quantity': 1,
            }
        ]
    )
    return checkout_session
        # except Exception as e:
        #     return JsonResponse({'error': str(e)})


class UserSubscriptionCreateView(viewsets.ViewSet):
    # def list(self,request):
    #     try:
    #         queryset = UserProfile.objects.get(user_id = self.request.user.id)
    #         print(queryset)
    #         serializer = UserProfileSerializer(queryset)
    #         return Response(serializer.data)
    #     except:
    #         return Response(status=status.HTTP_204_NO_CONTENT)

    # def get_queryset(self):
    #     queryset=UserProfile.objects.filter(user_id=self.request.user.id).all()
    #     return queryset

    # def generate_subscription_checkout(self):
    #     customer = Customer.objects.get(subscriber=request.user)
    #     stripe.api_key = STRIPE_SECRET_KEY
    #     session = stripe.checkout.Session.create(
    #         customer=customer.id,
    #         payment_method_types=['card'],
    #         subscription_data={
    #         'items': [{
    #         'plan': request.data["plan"],
    #         }],
    #         },
    #         success_url='http://example.com/success',
    #         cancel_url='http://example.com/cancelled',
    #     )

    #     data = {
    #     "session_id": session.id
    #     }
    #     return Response(data, status=200)






    def create(self,request):
        # user = request.user.id
        #customer = Customer.objects.get(subscriber=request.user)
        #serializer = UserProfileSerializer(data={**request.POST.dict(),'user':id})
        #price = Price.objects.get(id="price_1JQWziSAQeQ4W2LNzgKUjrIS")
        price = Price.objects.get(id="price_1JKwJ9SAQeQ4W2LN9ua8GgzM")
        #customer = Customer.get_or_create(subscriber=request.user)
        user=request.user
        session = create_checkout_session(user=user,price_id="price_1JKwJ9SAQeQ4W2LN9ua8GgzM")
        #print(customer)
        #customer = Customer.objects.first()
        #customer[0].subscribe(price=price)
        
        # if serializer.is_valid():
        #     serializer.save()
        #     return Response(serializer.data)
        return Response({'stripe_url':session.url}, status=201)
        #return Response({'msg':'Successfully created'}, status=201)

    # def update(self,request,pk=None):
    #     queryset = UserProfile.objects.get(user_id=self.request.user.id)
    #     serializer= UserProfileSerializer(queryset,data={**request.POST.dict()},partial=True)
    #     if serializer.is_valid():
    #         serializer.save()
    #         return Response(serializer.data)
    #     else:
    #         return Response(serializer.errors)


# class UserSubscriptionChoiceView(viewsets.ViewSet):
#     def create(self,request):
#         price = Price.objects.get(id="price_1JQWziSAQeQ4W2LNzgKUjrIS")
#         #price = Price.objects.get(id="price_1JKwJ9SAQeQ4W2LN9ua8GgzM")
#         customer = Customer.get_or_create(subscriber=request.user)
#         print(customer)
#         #customer = Customer.objects.first()
#         customer[0].subscribe(price=price)
        
#         # if serializer.is_valid():
#         #     serializer.save()
#         #     return Response(serializer.data)
#         return Response({'msg':'Successfully created'}, status=201)