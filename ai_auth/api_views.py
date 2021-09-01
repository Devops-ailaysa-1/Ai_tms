from ai_auth.serializers import (OfficialInformationSerializer, PersonalInformationSerializer,
                                ProfessionalidentitySerializer,UserAttributeSerializer,
                                UserProfileSerializer,CustomerSupportSerializer,ContactPricingSerializer,
                                TempPricingPreferenceSerializer)
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from django.shortcuts import get_object_or_404
#from ai_auth.serializers import RegisterSerializer,UserAttributeSerializer
from rest_framework import generics , viewsets
from ai_auth.models import (AiUser, OfficialInformation, PersonalInformation, Professionalidentity,
                            UserAttribute,UserProfile,CustomerSupport,ContactPricing,
                            TempPricingPreference)
from django.http import Http404,JsonResponse
from rest_framework import status
from django.db import IntegrityError
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import renderers
from rest_framework.decorators import api_view,permission_classes
from django.core.mail import EmailMessage
from django.template import Context
from django.template.loader import get_template
from django.template.loader import render_to_string
from datetime import datetime
from django.conf import settings
from djstripe.models import Customer,Invoice
from ai_staff.models import SupportType
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

    def put(self,request,pk):
        user = Professionalidentity.objects.get(user_id=pk)
        # user = get_object_or_404(queryset, pk=pk)
        serializer= ProfessionalidentitySerializer(user,data=request.data,partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors)


class UserProfileCreateView(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    def list(self,request):
        try:
            queryset = UserProfile.objects.get(user_id = request.user.id)
            serializer = UserProfileSerializer(queryset)
            return Response(serializer.data)
        except:
            return Response(status=status.HTTP_204_NO_CONTENT)

    def create(self,request):
        id = request.user.id
        serializer = UserProfileSerializer(data={**request.POST.dict(),'user':id})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response({'msg':'description already exists'}, status=status.HTTP_400_BAD_REQUEST)

    def update(self,request,pk):
        queryset = UserProfile.objects.filter(user_id=self.request.user.id).all()
        user = get_object_or_404(queryset, pk=pk)
        serializer= UserProfileSerializer(user,data={**request.POST.dict()},partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors)


class CustomerSupportCreateView(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    def list(self,request):
        queryset = self.get_queryset()
        serializer = CustomerSupportSerializer(queryset,many=True)
        return Response(serializer.data)
    def get_queryset(self):
        queryset= CustomerSupport.objects.filter(user_id=self.request.user.id).all()
        return queryset

    def create(self,request):
        id = request.user.id
        email = AiUser.objects.get(id=id).email
        support_type = request.POST.get("support_type")
        support_type_name = SupportType.objects.get(id=support_type).support_type
        description = request.POST.get("description")
        timestamp = datetime.now()
        serializer = CustomerSupportSerializer(data={**request.POST.dict(),'user':id})
        subject='Regarding Customer Support'
        template = 'customer_support_email.html'
        context = {'user': email,'support_type_name': support_type_name,'description':description,'timestamp':timestamp}
        if serializer.is_valid():
            serializer.save()
            send_email(subject,template,context)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class ContactPricingCreateView(viewsets.ViewSet):
    def list(self,request):
        user_id = request.user.id
        if user_id:
            name = AiUser.objects.get(id=user_id).fullname
            email = AiUser.objects.get(id=user_id).email
            return JsonResponse({"name":name,"email":email},safe=False)
        else:
            return Response({"message":"user is not authorized"})

    def create(self,request):
        name = request.POST.get("name")
        description = request.POST.get("description")
        email = request.POST.get("business_email")
        timestamp = datetime.now()
        template = 'contact_pricing_email.html'
        subject='Regarding Contact-Us Pricing'
        context = {'user': email,'name':name,'description':description,'timestamp':timestamp}
        serializer = ContactPricingSerializer(data={**request.POST.dict()})
        if serializer.is_valid():
            serializer.save()
            send_email(subject,template,context)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


def send_email(subject,template,context):
    content = render_to_string(template, context)
    msg = EmailMessage(subject, content, settings.DEFAULT_FROM_EMAIL , to=['thenmozhivijay20@gmail.com',])#to emailaddress need to change
    msg.content_subtype = 'html'
    msg.send()
    # return JsonResponse({"message":"Email Successfully Sent"},safe=False)


class TempPricingPreferenceCreateView(viewsets.ViewSet):

    def create(self,request):
        serializer = TempPricingPreferenceSerializer(data={**request.POST.dict()})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET',])
@permission_classes((IsAuthenticated, ))
def get_payment_details(request):
    user,user_invoice_details=None,None
    try:
        user = Customer.objects.get(subscriber_id = request.user.id).id
        user_invoice_details=Invoice.objects.filter(customer_id = user).all()
        print(user_invoice_details)
    except Exception as error:
        print(error)
    if user_invoice_details:
        out=[]
        for i in user_invoice_details:
            new={}
            Invoice_number = Invoice.objects.get(id = i.id).number
            Invoice_value = Invoice.objects.get(id=i.id).amount_paid
            Invoice_date = Invoice.objects.get(id = i.id).created
            status =  Invoice.objects.get(id = i.id).status
            pdf_download_link = Invoice.objects.get(id = i.id).invoice_pdf
            view_invoice_url = Invoice.objects.get(id =i.id).hosted_invoice_url
            output={"Invoice_number":Invoice_number,"Invoice_value":Invoice_value,"Invoice_date":Invoice_date,
                    "Status":status,"Invoice_Pdf_download_link":pdf_download_link,
                    "Invoice_view_URL":view_invoice_url}
            new.update(output)
            out.append(new)
    else:
        out = "No invoice details Exists"
    return JsonResponse({"out":out},safe=False)


@api_view(['GET',])
@permission_classes((IsAuthenticated, ))
def get_addon_details(request):
    try:
        user = Customer.objects.get(subscriber_id = request.user.id).id
        add_on_list = Session.objects.filter(Q(customer_id=user) & Q(mode = "payment")).all()
    except Exception as error:
        print(error)
    if add_on_list:
        out=[]
        for i in add_on_list:
            new={}
            add_on=Charge.objects.get(payment_intent_id=i.payment_intent_id)
            amount = add_on.amount_captured
            receipt = add_on.receipt_url
            output ={"Amount":amount,"Receipt":receipt}
            new.update(output)
            out.append(new)
    else:
        out = "No Add-on details Exists"
    return JsonResponse({"out":out},safe=False)
