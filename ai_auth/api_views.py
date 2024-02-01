from logging import INFO
from ai_auth.checks import AilaysaTroubleShoot
from langdetect import detect
import logging
import re , requests, os
from django.core.mail import send_mail
from ai_auth import forms as auth_forms  
from ai_auth.soc_auth import GoogleLogin,ProzLogin
from allauth.account.models import EmailAddress
from dj_rest_auth.registration.serializers import SocialLoginSerializer
from djstripe.models.billing import Plan, TaxId
from rest_framework import response
from django.urls import reverse
from os.path import join
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from stripe.api_resources import subscription
# from ai_auth.access_policies import MemberCreationAccess,InternalTeamAccess,TeamAccess
from ai_auth.serializers import (BillingAddressSerializer, BillingInfoSerializer,
                                ProfessionalidentitySerializer,UserAttributeSerializer,
                                UserProfileSerializer,CustomerSupportSerializer,ContactPricingSerializer,
                                TempPricingPreferenceSerializer, UserRegistrationSerializer, UserTaxInfoSerializer,AiUserProfileSerializer,
                                CarrierSupportSerializer,VendorOnboardingSerializer,GeneralSupportSerializer,
                                TeamSerializer,InternalMemberSerializer,HiredEditorSerializer,MarketingBootcampSerializer)
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from django.shortcuts import get_object_or_404
from ai_auth.vendor_onboard_list import users_list
#from ai_auth.serializers import RegisterSerializer,UserAttributeSerializer
from rest_framework import generics , viewsets
from ai_auth.models import (AiUser, BillingAddress, CampaignUsers, Professionalidentity, ReferredUsers,
                            UserAttribute,UserProfile,CustomerSupport,ContactPricing,
                            TempPricingPreference,CreditPack, UserTaxInfo,AiUserProfile,
                            Team,InternalMember,HiredEditors,VendorOnboarding,SocStates,GeneralSupport,SubscriptionOrder,
                            PurchasedUnits,PurchasedUnitsCount,MarketingBootcamp)
from django.http import Http404,JsonResponse
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_text
from django.contrib.auth.tokens import PasswordResetTokenGenerator
# from django.utils import six
from rest_framework.pagination import PageNumberPagination
from rest_framework import status
from notifications.signals import notify
from django.db import IntegrityError
from django.contrib.auth.hashers import check_password,make_password
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import renderers
from rest_framework.decorators import api_view,permission_classes
from django.core.mail import EmailMessage
from django.template import Context
from django.template.loader import get_template
from django.template.loader import render_to_string
from datetime import datetime,date,timedelta
from djstripe.models import Price,Subscription,InvoiceItem,PaymentIntent,Charge,\
                            Customer,Invoice,Product,TaxRate,Account,Coupon
import stripe
from django.conf import settings
from ai_staff.models import (Countries, CurrencyBasedOnCountry, IndianStates, 
                            SupportType,JobPositions,SupportTopics,Role, 
                            OldVendorPasswords,Suggestion,SuggestionType)
from django.db.models import Q
from  django.utils import timezone
import time,pytz,six
from dateutil.relativedelta import relativedelta
from ai_marketplace.models import Thread,ChatMessage
from ai_auth.utils import get_plan_name,company_members_list
from ai_auth.vendor_onboard_list import VENDORS_TO_ONBOARD
from ai_vendor.models import VendorsInfo,VendorLanguagePair,VendorOnboardingInfo
from django.db import transaction
from django.contrib.sites.shortcuts import get_current_site
#for soc
from django.test.client import RequestFactory
from django.test import Client
from allauth.socialaccount.providers.google.views import ( GoogleOAuth2Adapter,)
from allauth.socialaccount.providers.oauth2.views import (
    OAuth2Adapter,
    OAuth2CallbackView,
    OAuth2LoginView,
)
from ai_auth.providers.proz.views import ProzAdapter
from django.contrib.sessions.models import Session
from django.http import HttpResponseRedirect
from urllib.parse import parse_qs, urlencode,  urlsplit
from django.shortcuts import redirect
import json
from django.contrib import messages
from ai_auth.Aiwebhooks import update_user_credits
from allauth.account.signals import email_confirmed
from ai_auth.signals import send_campaign_email
#from django_oso.decorators import authorize_request
from django_oso.auth import authorize, authorize_model
import os
from ai_auth.reports import AilaysaReport

logger = logging.getLogger('django')

try:
    default_djstripe_owner=Account.get_default_account()
except BaseException as e:
    print(f"Error : {str(e)}")

def get_stripe_api_key():
    if settings.STRIPE_LIVE_MODE == True :
        api_key = settings.STRIPE_LIVE_SECRET_KEY
    else:
        api_key = settings.STRIPE_TEST_SECRET_KEY
    return api_key

def striphtml(data):
    p = re.compile(r'<.*?>')
    return p.sub('', data)
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



# class PersonalInformationView(APIView):
#     permission_classes = [IsAuthenticated]

#     def get(self, request,format=None):
#         try:
#             queryset = PersonalInformation.objects.get(user_id=request.user.id)
#         except PersonalInformation.DoesNotExist:
#             return Response(status=204)

#         serializer = PersonalInformationSerializer(queryset)
#         return Response(serializer.data)

#     def post(self, request):
#         data = request.data
#         print("Data==>",data)
#         serializer = PersonalInformationSerializer(data=data, context={'request':request})

#         if serializer.is_valid():
#             try:
#                 serializer.save()
#             except IntegrityError:
#                 return Response(serializer.errors, status=status.HTTP_409_CONFLICT)
#             return Response(serializer.data, status=201)
#         return Response(serializer.errors, status=400)


#     def patch(self, request, format=None):
#         print(request.data)
#         personal_info = PersonalInformation.objects.get(user_id=request.user.id)
#         serializer = PersonalInformationSerializer(personal_info,
#                                            data=request.data,
#                                            partial=True)
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# class OfficialInformationView(APIView):
#     permission_classes = [IsAuthenticated]

#     def get(self, request,format=None):
#         try:
#             queryset = OfficialInformation.objects.get(user_id=request.user.id)
#         except OfficialInformation.DoesNotExist:
#             return Response(status=204)
#         serializer = OfficialInformationSerializer(queryset)
#         return Response(serializer.data)


#     def post(self, request):
#         data = request.data
#         serializer = OfficialInformationSerializer(data=data, context={'request':request})

#         if serializer.is_valid():
#             try:
#                 serializer.save()
#             except IntegrityError:
#                 return Response(serializer.errors, status=status.HTTP_409_CONFLICT)
#             return Response(serializer.data, status=201)
#         return Response(serializer.errors, status=400)


#     def patch(self, request, format=None):
#         officaial_info = OfficialInformation.objects.get(user_id=request.user.id)
#         serializer = OfficialInformationSerializer(officaial_info,
#                                            data=request.data,
#                                            partial=True)
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



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
        id = request.user.id
        avatar = request.FILES.get('avatar')
        serializer = ProfessionalidentitySerializer(data={**request.POST.dict(),'user':id,'avatar':avatar})
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


    def delete(self, request, format=None):
        identity = self.get_object(request.user.id)
        if request.POST.get('avatar',None) != None :
            identity.avatar=None
        if request.POST.get('logo',None) != None :
            identity.logo=None
        if request.POST.get('header',None) != None :
            identity.header=None
        identity.save()
        return Response({"msg":"Deleted Successfully"},status=200)
    #
    # def put(self,request,pk):
    #     user = Professionalidentity.objects.get(user_id=pk)
    #     # user = get_object_or_404(queryset, pk=pk)
    #     serializer= ProfessionalidentitySerializer(user,data=request.data,partial=True)
    #     if serializer.is_valid():
    #         serializer.save()
    #         return Response(serializer.data)
    #     else:
    #         return Response(serializer.errors)


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
        try:
            support_type_name = SupportType.objects.get(id=support_type).support_type
        except:
            support_type_name = None
        description = request.POST.get("description")
        timestamp = date.today()
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
    permission_classes = [AllowAny]
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
        today = date.today()
        template = 'contact_pricing_email.html'
        subject='Regarding Contact-Us'
        context = {'user': email,'name':name,'description':description,'timestamp':today}
        serializer = ContactPricingSerializer(data={**request.POST.dict()})
        if serializer.is_valid():
            serializer.save()
            send_email(subject,template,context)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


def send_email(subject,template,context):
    content = render_to_string(template, context)
    file_ =context.get('file')
    msg = EmailMessage(subject, content, settings.DEFAULT_FROM_EMAIL , to=['support@ailaysa.com',])#to emailaddress need to change ['support@ailaysa.com',]
    if file_:
        name = os.path.basename(file_.path)
        msg.attach(name, file_.file.read())
    msg.content_subtype = 'html'
    msg.send()
    # return JsonResponse({"message":"Email Successfully Sent"},safe=False)

def send_email_with_multiple_files(subject,template,context):
    content = render_to_string(template, context)
    files_ =context.get('files')
    msg = EmailMessage(subject, content, settings.DEFAULT_FROM_EMAIL , to=['support@ailaysa.com',])#to emailaddress need to change ['support@ailaysa.com',]
    if files_:
        for i in files_:
            path = i.app_suggestion_file.path
            name = os.path.basename(path)
            msg.attach(name, i.app_suggestion_file.file.read())
    msg.content_subtype = 'html'
    msg.send()

class TempPricingPreferenceCreateView(viewsets.ViewSet):
    permission_classes = [AllowAny]

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
        user = Customer.objects.get(subscriber_id = request.user.id,djstripe_owner_account=default_djstripe_owner).id
        user_invoice_details=Invoice.objects.filter(customer_id = user).all()
        print(user_invoice_details)
    except Exception as error:
        print(error)
    if user_invoice_details:
        out=[]
        for i in user_invoice_details:
            print("trial exists--->",i.subscription.trial_start)
            if i.subscription.trial_start ==None:
                output={"Name":i.plan.product.name,"Price":i.amount_paid,"Currency":i.currency,"Invoice_number":i.number,"Invoice_date":i.created.date(),
                        "Status":"paid" if i.paid else "unpaid","Invoice_Pdf_download_link": i.invoice_pdf,
                        "Invoice_view_URL":i.hosted_invoice_url}
                out.append(output)
    else:
        out =[]
    return JsonResponse({"Payments":out},safe=False)


@api_view(['GET',])
@permission_classes((IsAuthenticated, ))
def get_addon_details(request):
    user,add_on_list=None,None
    try:
        user = Customer.objects.get(subscriber_id = request.user.id,djstripe_owner_account=default_djstripe_owner).id
        add_on_list = PaymentIntent.objects.filter(Q(customer_id=user)&Q(metadata__contains={"type":"Addon"})).all()
        print(add_on_list)
    except Exception as error:
        print(error)
    if add_on_list:
        out=[]
        for i in add_on_list:
            try:
                add_on=Charge.objects.get(Q(payment_intent_id=i.id)&Q(status='succeeded'))
            except:
                add_on = None
            name = Price.objects.get(id=i.metadata["price"],djstripe_owner_account=default_djstripe_owner).product.name
            output ={"Name":name,"Quantity":i.metadata["quantity"],"Amount": (i.amount)/100,"Currency":i.currency,"Date":i.created.date(),"Receipt":add_on.receipt_url if add_on else None,"Status":"succeeded" if add_on else "incomplete"}
            out.append(output)
    else:
        out = []
    return JsonResponse({"out":out},safe=False)

def create_checkout_session(user,price,customer=None,trial=False):
    product_name = Price.objects.get(id = price.id,djstripe_owner_account=default_djstripe_owner).product.name
    domain_url = settings.USERPORTAL_URL
    if settings.STRIPE_LIVE_MODE == True :
        api_key = settings.STRIPE_LIVE_SECRET_KEY
    else:
        api_key = settings.STRIPE_TEST_SECRET_KEY

    stripe.api_key = api_key

    tax_rate =[]

    # if trial == True :
    #     date_time = timezone.now()
    #     trial_end = int(time.mktime(date_time.timetuple()))
    #     print("trial_end>>>",trial_end)
    # else:
    #     trial_end = None

    tax_rate=find_taxrate(user,trial)

    # if user.country.sortname == 'IN':
    #     addr=BillingAddress.objects.get(user=user)
    #     print(addr.state)
    #     state = IndianStates.objects.filter(state_name__icontains=addr.state)
    #     if state.exists() and state.first().state_code == 'TN':
    #         tax_rate=[TaxRate.objects.get(display_name = 'CGST').id,TaxRate.objects.get(display_name = 'SGST').id]
    #     elif state.exists():
    #         tax_rate=[TaxRate.objects.get(display_name = 'IGST').id,]
    # else:
    #     tax_rate=None
    # tax_rate = None
    #if user.billing
    # print("tax_rate",tax_rate)
    # print("user country>>",user.country.sortname)
    # try:
    #     BillingAddress.objects.get(user=user)
    #     addr_collect='auto'
    # except BillingAddress.DoesNotExist:
    #     addr_collect= 'required'

    coupon = check_campaign_coupon(user)
    # if coupon:
    #     if price.recurring.get('interval') == 'month':
    #         coupon = False

    checkout_session = stripe.checkout.Session.create(
        client_reference_id=user.id,
        success_url=domain_url + 'success?ses={CHECKOUT_SESSION_ID}',
        cancel_url=domain_url + 'cancel/',
        payment_method_types=['card'],
        customer =customer.id,
        #customer_email=user.email,
        mode='subscription',
        line_items=[
            {
                'price': price.id,
                'quantity': 1,
                'tax_rates':tax_rate,
            }
        ],
        #billing_address_collection=addr_collect,
        customer_update={'address':'never','name':'never'},
        #tax_id_collection={'enabled':'True'},
        allow_promotion_codes=coupon,
        subscription_data={
        'default_tax_rates':tax_rate,
        'trial_end':None,
        'metadata' : {'price':price.id,'product':product_name,'type':'subscription'},
        }
    )
    return checkout_session

def find_taxrate(user,trial=False):
    if trial:
         tax_rate=None
    else:
        if user.country.sortname == 'IN':
            addr=BillingAddress.objects.get(user=user)
            print(addr.state)
            state = IndianStates.objects.filter(Q(state_name__icontains=addr.state)|Q(state_code__contains=addr.state))
            if state.exists() and state.first().state_code == 'TN':
                tax_rate=[TaxRate.objects.filter(display_name = 'CGST').last().id,TaxRate.objects.filter(display_name = 'SGST').last().id]
            elif state.exists():
                tax_rate=[TaxRate.objects.filter(display_name = 'IGST').last().id,]
            #tax_rate=[TaxRate.objects.get(display_name = 'GST',description='IN GST').id,]
        else:
            tax_rate=None
    return tax_rate


def subscribe_trial(price,customer=None):
    product_name = Price.objects.get(id = price.id,djstripe_owner_account=default_djstripe_owner).product.name
    print("product_name>>",product_name)
    domain_url = settings.USERPORTAL_URL
    if settings.STRIPE_LIVE_MODE == True :
        api_key = settings.STRIPE_LIVE_SECRET_KEY
    else:
        api_key = settings.STRIPE_TEST_SECRET_KEY

    stripe.api_key = api_key
    tax_rate=find_taxrate(customer.subscriber,trial=True)
    subscription = stripe.Subscription.create(
    customer=customer.id,
    items=[
    {
        'price': price.id,
    },
    ],
    default_tax_rates=tax_rate,
    trial_period_days=14,

    metadata={'price':price.id,'product':product_name,'type':'subscription_trial'}
    )

    return subscription


def subscribe_lsp(user):
    plan = None
    try:
        cust = Customer.objects.get(subscriber=user,djstripe_owner_account=default_djstripe_owner)
    except Customer.DoesNotExist:
        customer,created = Customer.get_or_create(subscriber=user)
        cust=customer
        if created:
            plan = 'new'
    if cust.currency=='':
        if user.country.id == 101 :
            currency = 'inr'
        else:
            currency ='usd'
    else:
        currency =cust.currency
    price = Plan.objects.get(product__name="Business - V",currency=currency,interval='month',amount=0,djstripe_owner_account=default_djstripe_owner)
    if plan == 'new':
        sub=subscribe(price=price,customer=cust)
        return sub


def subscribe_vendor(user):
    plan = None
    try:
        cust = Customer.objects.get(subscriber=user,djstripe_owner_account=default_djstripe_owner)
    except Customer.DoesNotExist:
        customer,created = Customer.get_or_create(subscriber=user)
        cust=customer
        if created:
            plan = 'new'
    if cust.currency=='':
        if user.country.id == 101 :
            currency = 'inr'
        else:
            currency ='usd'
    else:
        currency =cust.currency
    price = Price.objects.get(product__name="Pro - V",currency=currency,djstripe_owner_account=default_djstripe_owner)
    if plan == 'new':
        sub=subscribe(price=price,customer=cust)
        return sub
    plan = get_plan_name(user)
    if plan== None or(plan != "Pro - V" and plan.startswith('Pro')):
        sub=subscribe(price=price,customer=cust)
        return sub


def subscribe(price,customer=None):
    product_name = Price.objects.get(id = price.id,djstripe_owner_account=default_djstripe_owner).product.name
    if settings.STRIPE_LIVE_MODE == True :
        api_key = settings.STRIPE_LIVE_SECRET_KEY
    else:
        api_key = settings.STRIPE_TEST_SECRET_KEY

    stripe.api_key = api_key
   # tax_rate=find_taxrate(customer.subscriber,trial=False)
    subscription = stripe.Subscription.create(
    customer=customer.id,
    items=[
    {
        'price': price.id,
    },
    ],
    #default_tax_rates=tax_rate,
    #trial_period_days=14,

    metadata={'price':price.id,'product':product_name,'type':'subscription'}
    )

    return subscription

def create_addon_paymentintent(customer,currency):
    if settings.STRIPE_LIVE_MODE == True :
        api_key = settings.STRIPE_LIVE_SECRET_KEY
    else:
        api_key = settings.STRIPE_TEST_SECRET_KEY

    stripe.api_key = api_key

    pay_intent = stripe.PaymentIntent.create(
    customer=customer.id,
    amount=0,
    currency=currency,
    payment_method_types=["card"],
    metadata= {
    "price": "price_1Jlt0nSHaXADggwo3di76YBt",
    "quantity": "1",
    "type": "Addon"
    }
    )


def create_checkout_session_addon(price,Aicustomer,tax_rate,quantity=1):
    domain_url = settings.USERPORTAL_URL
    if settings.STRIPE_LIVE_MODE == True :
        api_key = settings.STRIPE_LIVE_SECRET_KEY
    else:
        api_key = settings.STRIPE_TEST_SECRET_KEY

    stripe.api_key = api_key
    # try:
    #     BillingAddress.objects.get(user=Aicustomer.subscriber)
    #     addr_collect='auto'
    # except BillingAddress.DoesNotExist:
    #     addr_collect= 'required'

    coupon = check_campaign_coupon(Aicustomer.subscriber)

    checkout_session = stripe.checkout.Session.create(
        client_reference_id=Aicustomer.subscriber,
        success_url=domain_url + 'success?ses={CHECKOUT_SESSION_ID}',
        cancel_url=domain_url + 'cancel/',
        payment_method_types=['card'],
        mode='payment',
        customer = Aicustomer.id,
        #billing_address_collection=addr_collect,
        customer_update={'address':'never','name':'never'},
        #tax_id_collection={'enabled':'True'},
        allow_promotion_codes=coupon,
        line_items=[
            {
                'price': price.id,
                'quantity': quantity,
                'tax_rates':tax_rate,
            },
        ],
        payment_intent_data={
            'metadata' : {'price':price.id,'quantity':quantity,'type':'Addon'}, }
    )
    return checkout_session


def create_invoice_one_time(price_id,Aicustomer,tax_rate,coupon,quantity=1):
    if settings.STRIPE_LIVE_MODE == True :
        api_key = settings.STRIPE_LIVE_SECRET_KEY
    else:
        api_key = settings.STRIPE_TEST_SECRET_KEY
    print(tax_rate)
    stripe.api_key = api_key
    data1=stripe.InvoiceItem.create(
                customer=Aicustomer.id,
                price=price_id.id,
                quantity=quantity,
                tax_rates=tax_rate
                )

    data2=stripe.Invoice.create(
    customer=Aicustomer.id,
    discounts =[{'coupon':coupon}],
    auto_advance=True # auto-finalize this draft after ~1 hour
    )
    response = stripe.Invoice.finalize_invoice(
        data2['id'], )
    return response



def is_active_subscription(user):
    '''check customer exist and he has active subscription'''
    #(F,F)-->(No active subscription,Customer not exist in stripe)
    #(F,T)-->(No active subscription,Customer exist in stripe)
    #(T,T)-->(Has active subscriptionor trial subscription,Customer exist in stripe)
    try:
        customer = Customer.objects.get(subscriber=user,djstripe_owner_account=default_djstripe_owner)
    except Customer.DoesNotExist:
        return False,False
    #subscription = Subscription.objects.filter(customer=customer).last()
    subscription = customer.subscriptions
    if subscription.exists() and subscription.filter(status = 'active').exists():
        is_active = (True, True)
    elif subscription.exists() and subscription.filter(status = 'trialing').exists():
        is_active = (True, True)
    else:
        is_active = (False, True)

    return is_active


def generate_portal_session(customer):
    domain_url = settings.USERPORTAL_URL
    if settings.STRIPE_LIVE_MODE == True :
        api_key = settings.STRIPE_LIVE_SECRET_KEY
    else:
        api_key = settings.STRIPE_TEST_SECRET_KEY

    stripe.api_key = api_key
    session = stripe.billing_portal.Session.create(
        customer=customer.id,
        return_url=domain_url+'subscription-plans',
    )
    return session

# def check_active_user(func):
#     def decorator(*args, **kwargs):
#         if
#         try:
#             return func(*args, **kwargs)
#         except IntegrityError as e:
#             print("error---->", e)
#             return Response({'message': "integrirty error"}, 409)

#     return decorator

def is_deactivated(user):
    "To be Changed To decorator"
    return user.deactivate == True


# def update_billing_address(address):
#     if settings.STRIPE_LIVE_MODE == True :
#         api_key = settings.STRIPE_LIVE_SECRET_KEY
#     else:
#         api_key = settings.STRIPE_TEST_SECRET_KEY
#     try:
#         customer = Customer.objects.get(subscriber=address.user)
#     except Customer.DoesNotExist:
#         customer = Customer.objects.get(subscriber=address.user)

#     stripe.api_key = api_key
#     response =stripe.Customer.modify(
#     customer.id,
#     name = address.name if address.name is not None else address.user.fullname,
#     address={
#     "city": address.city,
#     "line1": address.line1,
#     "line2": address.line2,
#     "state": address.state,
#     "country": address.country.sortname,
#     "postal_code": address.zipcode
#     },

#     )
#     return response

# @api_view(['POST'])
# @permission_classes([IsAuthenticated])
# def buy_addon(request):
#     user = request.user
#     quantity=request.POST.get('quantity',1)
#     try:
#         price = Price.objects.get(id=request.POST.get('price'))
#     except KeyError :
#          return Response({'msg':'Invalid price'}, status=406)

#     cust=Customer.objects.get(subscriber=user.id)
#     session=create_checkout_session_addon(user,price,cust,quantity)
#     #request.POST.get('')
#     return Response({'msg':'Payment Session Generated ','stripe_session_url':session.url,'strip_session_id':session.id}, status=200)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def buy_addon(request):
    user = request.user
    if is_deactivated(user):
        return Response({'msg':'User is not active'}, status=423)
    quantity=request.POST.get('quantity',1)
    try:
        price = Price.objects.get(id=request.POST.get('price'),djstripe_owner_account=default_djstripe_owner)
    except (KeyError,Price.DoesNotExist) :
         return Response({'msg':'Invalid price'}, status=406)

    cust=Customer.objects.get(subscriber=user,djstripe_owner_account=default_djstripe_owner)
    try:
        addr=BillingAddress.objects.get(user=user)
    except BillingAddress.DoesNotExist:
        return Response({'Error':'Billing Address Not Found'}, status=412)
    tax_rate=find_taxrate(user)
    # if user.country.sortname == 'IN':
    #     try:
    #         addr=BillingAddress.objects.get(user=user)
    #     except BillingAddress.DoesNotExist:
    #         return Response({'Error':'Billing Address Not Found'}, status=412)
    #     state = IndianStates.objects.filter(state_name__icontains=addr.state)
    #     if state.exists() and state.first().state_code == 'TN':
    #         tax_rate=[TaxRate.objects.get(display_name = 'CGST').id,TaxRate.objects.get(display_name = 'SGST').id]
    #     elif state.exists():
    #         tax_rate=[TaxRate.objects.get(display_name = 'IGST').id,]
    # else:
    #     tax_rate=None
    response = create_checkout_session_addon(price,cust,tax_rate,quantity)

    #request.POST.get('')
    return Response({'msg':'Payment Session Generated ','stripe_session_url':response.url,'strip_session_id':response.id}, status=307)


def subscriptin_modify_default_tax_rate(customer,addr=None):
    if settings.STRIPE_LIVE_MODE == True :
        api_key = settings.STRIPE_LIVE_SECRET_KEY
    else:
        api_key = settings.STRIPE_TEST_SECRET_KEY

    stripe.api_key = api_key

    # if customer.subscriber.country.sortname == 'IN' and addr.country.sortname == 'IN':
    #     state = IndianStates.objects.filter(state_name__icontains=addr.state)
    #     if state.exists() and state.first().state_code == 'TN':
    #         tax_rates=[TaxRate.objects.get(display_name = 'CGST').id,TaxRate.objects.get(display_name = 'SGST').id]
    #     elif state.exists():
    #         tax_rates=[TaxRate.objects.get(display_name = 'IGST').id,]
    # else:
    #     tax_rates=None
    tax_rate=find_taxrate(customer.subscriber)
    subscriptions = customer.subscriptions.filter(status="active")
    if tax_rate != None and subscriptions.count() > 0 :
        response = stripe.Subscription.modify(
        subscriptions.last().id,
        default_tax_rates=tax_rate
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def customer_portal_session(request):
    user = request.user
    try:
        customer = Customer.objects.get(subscriber=user,djstripe_owner_account=default_djstripe_owner)
        #addr = BillingAddress.objects.get(user=request.user)
        session=generate_portal_session(customer)
        if not customer.subscriptions.exists():
             return Response({'msg':'User has No Active Subscription'}, status=402)
        subscriptin_modify_default_tax_rate(customer)
    except Customer.DoesNotExist:
        return Response({'msg':'Unable to Generate Customer Portal Session'}, status=400)
    except BillingAddress.DoesNotExist:
        return Response({'Error':'Billing Address Not Found'}, status=400)
    # except Subscription:
    #     customer.
    return Response({'msg':'Customer Portal Session Generated','stripe_session_url':session.url,'strip_session_id':session.id}, status=307)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def check_subscription(request):
    is_active = is_active_subscription(request.user)
    if is_active == (False,True):
        customer = Customer.objects.get(subscriber=request.user,djstripe_owner_account=default_djstripe_owner)
        subscriptions = Subscription.objects.filter(customer=customer)
        if subscriptions.count() != 0:
            subscriptions = subscriptions.last()
            trial = 'true' if subscriptions.metadata.get('type') == 'subscription_trial' else 'false'
            sub_name = CreditPack.objects.get(product__id=subscriptions.plan.product_id,type='Subscription').name
            return Response({'subscription_name':sub_name,'sub_status':subscriptions.status,'sub_price_id':subscriptions.plan.id,
                            'interval':subscriptions.plan.interval,'sub_period_end':subscriptions.current_period_end,'sub_currency':subscriptions.plan.currency,'sub_amount':subscriptions.plan.amount,'trial':trial,'canceled_at':subscriptions.canceled_at}, status=200)
        elif subscriptions.count() > 0:
            return Response({'subscription_name':None,'sub_status':None,'sub_price_id':None,'interval':None,'sub_period_end':None,'sub_currency':None,'sub_amount':None,'trial':None,'canceled_at':None}, status=200)
        else:
            return Response({"msg":"creating_subscription"}, status=202)
    if is_active == (True,True):
        customer = Customer.objects.get(subscriber=request.user,djstripe_owner_account=default_djstripe_owner)
        #subscription = Subscription.objects.filter(customer=customer).last()
        subscription=customer.subscriptions.filter(Q(status='trialing')|Q(status='active')).last()
        trial = 'true' if subscription.metadata.get('type') == 'subscription_trial' else 'false'
       # sub_name = SubscriptionPricing.objects.get(stripe_price_id=subscription.plan.id).plan
        sub_name = CreditPack.objects.get(product__id=subscription.plan.product_id,type='Subscription').name
        return Response({'subscription_name':sub_name,'sub_status':subscription.status,'sub_price_id':subscription.plan.id,'interval':subscription.plan.interval,'sub_period_end':subscription.current_period_end,
                        'sub_currency':subscription.plan.currency,'sub_amount':subscription.plan.amount,'trial':trial,'canceled_at':subscription.canceled_at}, status=200)
    if is_active == (False,False):
        return Response({'msg':'Not a Stripe Customer'}, status=206)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def buy_subscription(request):
    user = request.user
    if is_deactivated(user):
        return Response({'msg':'User is not active'}, status=423)
    try:
        price = Price.objects.get(id=request.POST.get('price'),djstripe_owner_account=default_djstripe_owner)
        addr = BillingAddress.objects.get(user=request.user)
    except (KeyError,Price.DoesNotExist) :
        return Response({'msg':'Invalid price'}, status=406)
    except BillingAddress.DoesNotExist:
        return Response({'Error':'Billing Address Not Found'}, status=412)
    is_active = is_active_subscription(user)
    if not is_active == (False,False):
        customer= Customer.objects.get(subscriber=user,djstripe_owner_account=default_djstripe_owner)
        session=create_checkout_session(user=user,price=price,customer=customer)
        return Response({'msg':'Payment Session Generated ','stripe_session_url':session.url,'strip_session_id':session.id}, status=307)
    else:
        return Response({'msg':'No Stripe Account Found'}, status=404)



def campaign_subscribe(user,camp):
    plan = None
    livemode = settings.STRIPE_LIVE_MODE
    api_key = get_stripe_api_key()
    try:
        cust = Customer.objects.get(subscriber=user,djstripe_owner_account=default_djstripe_owner)
    except Customer.DoesNotExist:
        customer,created = Customer.get_or_create(subscriber=user)
        cust=customer
        if created:
            plan = 'new'
    if cust.currency=='':
        if user.country.id == 101 :
            currency = 'inr'
        else:
            currency ='usd'
    else:
        currency =cust.currency
    ## Base Subscription
    price = Plan.objects.get(product__name=camp.campaign_name.subscription_name,
                        interval=camp.campaign_name.subscription_duration,currency=currency,
                        djstripe_owner_account=default_djstripe_owner,livemode=livemode)

    #if plan == 'new':
    if user.is_vendor:
        sub = Subscription.objects.filter(customer=cust,djstripe_owner_account=default_djstripe_owner).last()
    else:
        sub=subscribe(price=price,customer=cust)
        if sub:
            # camp.subscribed =True
            # camp.save()
            # send_campaign_email.send(
            # sender=camp.__class__,
            # instance = camp,
            # user=user,
            # )
            sync_sub = Subscription.sync_from_stripe_data(sub, api_key=api_key)
        else:
            print("error in creating subscription ",user.uid)

    price_addon = Price.objects.get(product__name=camp.campaign_name.Addon_name,
                        currency=currency,
                        djstripe_owner_account=default_djstripe_owner,livemode=livemode)
    print(price_addon)
    try:
        coupon = Coupon.objects.get(name=settings.CAMPAIGN)
    except:
        print("coupon not found")
        return None
    #invo = create_invoice_one_time(price_addon,cust,None,coupon.id)
    # plan = get_plan_name(user)
    # if plan== None or(plan != "Pro - V" and plan.startswith('Pro')):
    #     sub=subscribe(price=price,customer=cust)
    #     return sub
    cp = CreditPack.objects.get(product=price_addon.product)
    update_user_credits(user=user,cust=cust,price=price,
                quants=camp.campaign_name.Addon_quantity,invoice=None,payment=None,pack=cp)
    return sub

def check_campaign_coupon(user):
    camp = CampaignUsers.objects.filter(user=user)
    if camp.count() > 0:
        if camp.last().coupon_used == False:

            # camp.name.subscription_name
            return True
        elif camp.last().coupon_used == True:
            logger.warning(f"user already user campaign coupon :{user.uid}")
            return False
    else:
        return False
    
def check_campaign(user):
    camp = CampaignUsers.objects.filter(user=user)
    if camp.count() > 0:
        if camp.last().subscribed == False:
            # camp.name.subscription_name
            return campaign_subscribe(user,camp.last())
        else:
            logger.warning(f"user already registed in campaign :{user.uid}")
            return None
    else:
        return None


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_currency(request):
    curr=Customer.objects.get(subscriber=request.user,djstripe_owner_account=default_djstripe_owner).currency
    return Response({'currency':curr})

class UserSubscriptionCreateView(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    def create(self,request,price_id=None):
        livemode = settings.STRIPE_LIVE_MODE
        #price_id = self.kwargs.get('price_id')
        price_id =request.query_params.get('price_id', None)
        print("price---id",price_id)
        user=request.user
        is_active = is_active_subscription(user=request.user)
        if is_active[0] == False:
            try:
                customer = Customer.objects.get(subscriber=request.user,djstripe_owner_account=default_djstripe_owner)
            except Customer.DoesNotExist:
                cust = Customer.get_or_create(subscriber=user)
                customer=cust[0]
            try:
                # check user is from pricing page
                pre_price = TempPricingPreference.objects.filter(email=user.email).last()
                if pre_price == None:
                    raise ValueError('No Prefernece Given')
                else:
                    price_id = pre_price.price_id
                    raise ValueError('No Prefernece Given')
                if user.country.id == 101 :
                    currency = 'inr'
                else:
                    currency ='usd'
                price = Plan.objects.get(id=pre_price.price_id)
                if price.currency != currency:
                    price = Plan.objects.filter(product=price.product,interval=price.interval,currency=currency).last()
                #try:
                #address = BillingAddress.objects.get(user=user)
                session = create_checkout_session(user=user,price=price,customer=customer)
                # except BillingAddress.DoesNotExist:
                #    return Response({'Error':'Billing Address Not Found'}, status=412)
                return Response({'msg':'Payment Needed','stripe_url':session.url}, status=307)
            except (TempPricingPreference.DoesNotExist,ValueError):
                #free=CreditPack.objects.get(name='Free')

                pro = CreditPack.objects.get(name='Pro')

                if user.country.id == 101 :
                    currency = 'inr'
                else:
                    currency ='usd'

                camp = check_campaign(user)
                if camp:
                    print("campaign",camp)
                    return Response({'msg':'User Successfully created'}, status=201)
                if price_id:
                    price = Plan.objects.get(id=price_id)
                    if (price.currency != currency) or (price.interval != 'month'):
                        price = Plan.objects.get(product=price.product,interval='month',currency=currency,interval_count=1,livemode=livemode)

                else:
                    price = Plan.objects.filter(product_id=pro.product,currency=currency,interval='month',livemode=livemode).last()
                print('price>>',price)
                
                if price.product.name == os.environ.get("PLAN_PAYG"):
                    response=subscribe(price,customer)
                else:
                    response=subscribe_trial(price,customer)

                print(response)
                #customer.subscribe(price=price)
                return Response({'msg':'User Successfully created','subscription':price.product.name+"_Trial"}, status=201)
        elif is_active == (True,True):
            return Response({'msg':'User already Registerd'}, status=400)

        # elif is_active == (False,True):
        #     customer = Customer.objects.get(subscriber=request.user)
        #     subscription = Subscription.objects.filter(customer=customer).last()
        #     if subscription == None:
        #         free=CreditPack.objects.get(name='Free')
        #         price = Price.objects.filter(product_id=free.product).last()
        #         customer.subscribe(price=price)
        #         #session = create_checkout_session(user=user,price_id="price_1JQWziSAQeQ4W2LNzgKUjrIS")
        #     return Response({'msg':'User already exist in stripe'}, status=400)


class BillingInfoView(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    def list(self, request):
        queryset = AiUser.objects.get(id=request.user.id)
        serializer = BillingInfoSerializer(queryset)
        return Response(serializer.data)

    def create(self,request):
        serializer = BillingInfoSerializer(data={**request.POST.dict()})
        print(serializer.is_valid())
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class BillingAddressView(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    def list(self, request):
        try:
            queryset = BillingAddress.objects.get(user=request.user)
        except BillingAddress.DoesNotExist:
            return Response(status=204)
        serializer = BillingAddressSerializer(queryset)
        return Response(serializer.data)

    def create(self,request):
        serializer = BillingAddressSerializer(data={**request.POST.dict()},context={'request':request})
        print(serializer.is_valid())
        if serializer.is_valid():
            try:
                serializer.save(user=self.request.user)
            except IntegrityError:
                return Response(serializer.errors, status=status.HTTP_409_CONFLICT)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, pk=None):
        try:
            queryset = BillingAddress.objects.get(user=request.user)
        except BillingAddress.DoesNotExist:
            return Response(status=204)
        #queryset = BillingAddress.objects.get(id=pk)
        serializer = BillingAddressSerializer(queryset,data={**request.POST.dict()},partial=True,context={'request':request})
        print(serializer.is_valid())
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

def user_taxid_delete(taxid):
    if settings.STRIPE_LIVE_MODE == True :
        api_key = settings.STRIPE_LIVE_SECRET_KEY
    else:
        api_key = settings.STRIPE_TEST_SECRET_KEY

    stripe.api_key = api_key

    response = stripe.Customer.delete_tax_id(
    taxid.customer.id,
    taxid.id,
    )

    return response

def cancel_subscription(user):
    cust=Customer.objects.get(subscriber=user,djstripe_owner_account=default_djstripe_owner)
    subs = cust.subscriptions.all()
    if settings.STRIPE_LIVE_MODE == True :
        api_key = settings.STRIPE_LIVE_SECRET_KEY
    else:
        api_key = settings.STRIPE_TEST_SECRET_KEY

    stripe.api_key = api_key

    for sub in subs:
        if sub.status == 'active' or sub.status =='trialing':
            stripe.Subscription.modify(
            sub.id,
            cancel_at_period_end=True
            )


class UserTaxInfoView(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    def list(self, request):
        queryset = UserTaxInfo.objects.filter(user=request.user)
        if not queryset.exists():
            return Response(status=204)
        serializer = UserTaxInfoSerializer(queryset,many=True)
        return Response(serializer.data)

    def create(self,request):
        request.POST.get('tax_id') == request.POST.get('tax_id').upper()
        serializer = UserTaxInfoSerializer(data={**request.POST.dict()})
        print(serializer.is_valid())
        if serializer.is_valid():
            try:
                serializer.save(user=self.request.user)
            except ValueError as e:
                print(e)
                return Response({'Error':str(e)}, status=422)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    def update(self, request, pk=None):
        try:
            queryset = UserTaxInfo.objects.get(user=request.user,id=pk)
            print("1",queryset)
            if request.POST.get('stripe_tax_id') == None and request.POST.get('tax_id') == None:
                taxid = TaxId.objects.filter(customer__subscriber=request.user,value=queryset.tax_id,type=queryset.stripe_tax_id.tax_code).first()
                if taxid == None:
                    return Response({'msg':"Taxid not exist"}, status=404)
                user_taxid_delete(taxid)
                queryset.delete()
                return Response({'msg':'Successfully Deleted'}, status=200)
            if request.POST.get('stripe_tax_id') == queryset.stripe_tax_id and request.POST.get('tax_id') == queryset.tax_id:
                return Response({'msg':'Successfully Updated'}, status=200)
            else:
                taxid = TaxId.objects.filter(customer__subscriber=request.user,value=queryset.tax_id,type=queryset.stripe_tax_id.tax_code).first()
                print("2",taxid)
                if taxid == None:
                    return Response({'msg':"Taxid not exist"}, status=404)
                user_taxid_delete(taxid)
                queryset.delete()
        except UserTaxInfo.DoesNotExist:
            return Response(status=204)
        #queryset = BillingAddress.objects.get(id=pk)
        #if queryset
        request.POST.get('tax_id') == request.POST.get('tax_id').upper()
        serializer = UserTaxInfoSerializer(queryset,data={**request.POST.dict()},partial=True)
        print(serializer.is_valid())
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

def integrity_error(func):
    def decorator(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except IntegrityError:
            return Response({'message': "Integrity error"}, 409)
    return decorator

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def TransactionSessionInfo(request):
    session_id = request.POST.get('session_id')
    if settings.STRIPE_LIVE_MODE == True :
        api_key = settings.STRIPE_LIVE_SECRET_KEY
    else:
        api_key = settings.STRIPE_TEST_SECRET_KEY

    stripe.api_key = api_key

    response = stripe.checkout.Session.retrieve(
                 session_id
                    )
    # print("Bank Details")
    # print()
    # print(response)
    try:
        amount = response.get("total_details").get("amount_discount")

        if amount != 0:
            email = response.get("customer_details").get("email")
            camp = CampaignUsers.objects.filter(user__email=email,coupon_used=False)
            if camp.count() > 0:
                camp = camp.last()
                camp.coupon_used= True
                camp.save()
                # if camp.last().coupon_used == False:
    except BaseException as e:
        logger.error(f"Issue in campaign update sess_id :{session_id}")

    if response.mode == "subscription":
        try:
            invoice =Invoice.objects.get(subscription=response.subscription)
        except Invoice.DoesNotExist:
             return JsonResponse({"msg":"unable to find related data"},status=204,safe = False)
        charge = invoice.charge
        #     return JsonResponse({"msg":"unable to find related data"},status=204,safe = False)
        pack = CreditPack.objects.get(product__prices__id=invoice.plan.id,type="Subscription")

        if invoice.amount_paid == 0 and invoice.amount_due == 0:
            return JsonResponse({"email":invoice.customer.email,"purchased_plan":pack.name,"paid_date":None,"currency":None,"amount":None,
                    "plan_duration_start":invoice.subscription.current_period_start,"plan_duration_end":invoice.subscription.current_period_end,"plan_interval":invoice.subscription.plan.interval,
                    "paid":None,"payment_type":None,
                    "txn_id":None,"receipt_url":None},status=200,safe = False)

        return JsonResponse({"email":charge.receipt_email,"purchased_plan":pack.name,"paid_date":charge.created,"currency":charge.currency,"amount":charge.amount,
                            "plan_duration_start":invoice.subscription.current_period_start,"plan_duration_end":invoice.subscription.current_period_end,"plan_interval":invoice.subscription.plan.interval,
                            "paid":charge.paid,"payment_type":charge.payment_method.type,
                            "txn_id":charge.balance_transaction_id,"receipt_url":charge.receipt_url},status=200,safe = False)

    elif response.mode == "payment":
        try:
            charge = Charge.objects.get(payment_intent=response.payment_intent,captured=True)
        except Charge.DoesNotExist:
             return JsonResponse({"msg":"unable to find related data"},status=204,safe = False)
        pack = CreditPack.objects.get(product__prices__id=charge.metadata.get("price"),type="Addon")
        return JsonResponse({"email":charge.receipt_email,"purchased_plan":pack.name,"paid_date":charge.created,"currency":charge.currency,"amount":charge.amount, "paid":charge.paid ,"payment_type":charge.payment_method.type, "txn_id":charge.balance_transaction_id,"receipt_url":charge.receipt_url},status=200,safe = False)
    else:
        return JsonResponse({"msg":"unable to find related data"},status=204,safe = False)


class AiUserProfileView(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    def list(self, request):
        try:
            queryset = AiUserProfile.objects.get(user_id=request.user.id)
        except AiUserProfile.DoesNotExist:
            return Response(status=204)

        serializer = AiUserProfileSerializer(queryset)
        return Response(serializer.data)
    @integrity_error
    def create(self,request):
        serializer = AiUserProfileSerializer(data={**request.POST.dict()},context={'request':request})
        print(serializer.is_valid())
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, pk):
        try:
            queryset = AiUserProfile.objects.get(Q(id=pk) & Q(user_id = request.user.id))
        except AiUserProfile.DoesNotExist:
            return Response(status=204)
        serializer =AiUserProfileSerializer(queryset,data={**request.POST.dict()},partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"user_profile_id":pk,"msg":"profile updated"})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



from .models import AiTroubleshootData, CarrierSupport
class CarrierSupportCreateView(viewsets.ViewSet):
    permission_classes = [AllowAny]
    def create(self,request):
        name = request.POST.get("name")
        job_position = request.POST.get("job_position")
        try:
            job_name = JobPositions.objects.get(id=job_position).job_name
        except:
            job_name = None
        print(job_name)
        email = request.POST.get("email")
        message = request.POST.get("message")
        phonenumber = request.POST.get('phonenumber')
        cv_file = request.FILES.get('cv_file')
        # time =datetime.now(pytz.timezone('Asia/Kolkata'))
        time = date.today()
        template = 'carrier_support_email.html'
        subject='Regarding Job Hiring'
        context = {'email': email,'name':name,'job_position':job_name,'phonenumber':phonenumber,'date':time,'message':message}
        serializer = CarrierSupportSerializer(data={**request.POST.dict(),'cv_file':cv_file})
        if serializer.is_valid():
            serializer.save()
            ins = CarrierSupport.objects.get(id=serializer.data.get('id'))
            if ins.cv_file:
                context.update({'file':ins.cv_file})
            send_email(subject,template,context)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GeneralSupportCreateView(viewsets.ViewSet):
    permission_classes = [AllowAny]
    def create(self,request):
        name = request.POST.get("name")
        topic = request.POST.get("topic")
        try:
            topic_name = SupportTopics.objects.get(id=topic).topic
        except:
            topic_name = None
        print(topic_name)
        email = request.POST.get("email")
        message = request.POST.get("message")
        phonenumber = request.POST.get('phonenumber')
        support_file = request.FILES.get('support_file')
        today = date.today()
        template = 'general_support_email.html'
        subject='Regarding General Support'
        context = {'email': email,'name':name,'topic':topic_name,'phonenumber':phonenumber,'date':today,'message':message}
        serializer = GeneralSupportSerializer(data={**request.POST.dict(),'support_file':support_file})
        if serializer.is_valid():
            serializer.save()
            ins = GeneralSupport.objects.get(id=serializer.data.get('id'))
            if ins.support_file:
                context.update({'file':ins.support_file})
            send_email(subject,template,context)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class VendorOnboardingCreateView(viewsets.ViewSet):

    def list(self, request):
        email = request.POST.get('email')
        try:
            queryset = VendorOnboarding.objects.get(email = email)
        except VendorOnboarding.DoesNotExist:
            return Response(status=204)

        serializer = VendorOnboardingSerializer(queryset)
        return Response(serializer.data)

    def create(self,request):
        from ai_vendor.models import VendorsInfo
        cv_file = request.FILES.get('cv_file')
        email = request.POST.get('email')
        serializer = VendorOnboardingSerializer(data={**request.POST.dict(),'cv_file':cv_file,'status':1})
        if serializer.is_valid():
            serializer.save()
            # user = AiUser.objects.get(email = email)
            # obj,created = VendorsInfo.objects.get_or_create(user=user,defaults = {"cv_file":cv_file})
            # if created == False:
            #     obj.cv_file = cv_file
            #     obj.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # def update(self, request, pk):
    #     cv_file=request.FILES.get('cv_file')
    #     try:
    #         queryset = VendorOnboarding.objects.get(id=pk)
    #     except VendorOnboarding.DoesNotExist:
    #         return Response(status=204)
    #     rejected_count = 1 if queryset.rejected_count==None else queryset.rejected_count+1
    #     serializer = VendorOnboardingSerializer(queryset,data={**request.POST.dict(),'cv_file':cv_file,'rejected_count':rejected_count,'status':1},partial=True)
    #     if serializer.is_valid():
    #         serializer.save()
    #         return Response(serializer.data)
    #     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# @api_view(['POST'])
# def vendor_invite_accept(request):
#     uid = request.POST.get('uid')
#     token = request.POST.get('token')
#     vendor_request_id = urlsafe_base64_decode(uid)
#     request = VendorOnboarding.objects.get(id=vendor_request_id )
#     if request is not None and invite_accept_token.check_token(request, token):
#         request.status = 2
#         request.save()
#         print("Request Accepted")
#         return JsonResponse({"msg":"Request Accepted"},safe=False)
#     else:
#         return JsonResponse({"msg":'Either link is already used or link is invalid!'},safe=False)



@api_view(['POST'])
@permission_classes([IsAuthenticated])
def account_deactivation(request):
    user_id = request.user.id
    user = AiUser.objects.get(id = user_id )
    present = datetime.now()
    six_mon_rel = relativedelta(months=6)
    user.deactivate = True
    user.deactivation_date = present.date()+six_mon_rel
    user.save()
    cancel_subscription(user)
    return JsonResponse({"msg":"user deactivated successfully"},safe = False)

@api_view(['POST'])
def account_activation(request):
    email = request.POST.get('email')
    try:
        user = AiUser.objects.get(email = email)
    except:
        return Response({"msg":"User Not Found"},status = 400)
    if user.deactivate == True:
        user.deactivate = False
        user.deactivation_date = None
        user.save()
        return JsonResponse({"msg":"user activated successfully"},safe = False)
    else:
        return JsonResponse({"msg":"no need to call activation.user is already active "})



def user_delete(user):
    cancel_subscription(user)
    dir = UserAttribute.objects.get(user_id=user.id).allocated_dir
    user.delete()
    os.system("rm -r " +dir)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def account_delete(request):
    from allauth.socialaccount.models import SocialAccount
    password_entered = request.POST.get('password')
    user = AiUser.objects.get(id =request.user.id)
    query = SocialAccount.objects.filter(user=user)
    if not query:
        match_check = check_password(password_entered,user.password)
        if match_check:
            present = datetime.now()
            three_mon_rel = relativedelta(months=3)
            user.is_active = False
            user.deactivation_date = present.date()+three_mon_rel
            user.save()
            #user_delete(user)
        else:
            return Response({"msg":"password didn't match"},status = 400)
    else:
        if query.filter(provider='proz'):
            ProzMessage.objects.filter(proz_uuid = query.last().uid).delete()
        user_delete(user)
    return JsonResponse({"msg":"user account deleted"},safe = False)


class TeamCreateView(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    def list(self, request):
        try:
            queryset =Team.objects.get(owner_id=request.user.id)
        except Team.DoesNotExist:
            return Response({'msg':'team not exists'},status=204)
        serializer = TeamSerializer(queryset)
        return Response(serializer.data)

    @integrity_error
    def create(self,request):
        name = request.POST.get('name')
        serializer =TeamSerializer(data={'name':name,'owner':request.user.id})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, pk):
        try:
            queryset = Team.objects.get(Q(id=pk) & Q(owner_id = request.user.id))
        except Team.DoesNotExist:
            return Response(status=204)
        serializer =TeamSerializer(queryset,data={**request.POST.dict()},partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


def send_email_user(subject,template,context,email):
    print(email)
    content = render_to_string(template, context)
    msg = EmailMessage(subject, content, settings.DEFAULT_FROM_EMAIL , to=[email,])
    msg.content_subtype = 'html'
    msg.send()

class TokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        print("USER-------->",user)
        return (
            six.text_type(user.pk) + six.text_type(timestamp) + six.text_type(user.status)
        )


invite_accept_token = TokenGenerator()

class InternalMemberCreateView(viewsets.ViewSet,PageNumberPagination):
    permission_classes = [IsAuthenticated]
    page_size = 10
    filter_backends = [DjangoFilterBackend,SearchFilter,OrderingFilter]
    ordering = ('id')
    search_fields = ['internal_member__fullname']

    def get_queryset(self):
        team = self.request.query_params.get('team')
        if team:
            queryset=InternalMember.objects.filter(team__name = team).exclude(role_id=4).distinct()
        else:
            queryset =InternalMember.objects.filter(team=self.request.user.team).exclude(role_id=4).distinct()
        return queryset

    def filter_queryset(self, queryset):
        filter_backends = (DjangoFilterBackend,SearchFilter,OrderingFilter )
        for backend in list(filter_backends):
            queryset = backend().filter_queryset(self.request, queryset, view=self)
        return queryset

    # def list(self, request):
    #     queryset_all = self.get_queryset()
    #     if not queryset_all.exists():
    #         return Response(status=204)
    #     queryset = self.filter_queryset(self.get_queryset())
    #     pagin_tc = self.paginate_queryset(queryset, request , view=self)
    #     serializer = InternalMemberSerializer(pagin_tc,many=True)
    #     response = self.get_paginated_response(serializer.data)
    #     return response

    def list(self, request):
        queryset = self.get_queryset()
        serializer = InternalMemberSerializer(queryset,many=True)
        return Response(serializer.data)

    def check_user(self,email,team_name):
        try:
            user = AiUser.objects.get(email = email)
            if user.is_internal_member == True:
                if user.team.name == team_name:
                    return {"msg":"Already team member"}
                else:
                    return {"msg":"Already Another team member"}
            else:
                return {"msg":"Ailaysa User"}
        except:
            return None

    def create_internal_user(self,name,email):
        password = AiUser.objects.make_random_password()
        print("randowm pass",password)
        hashed = make_password(password)
        user = AiUser.objects.create(fullname =name,email = email,password = hashed,is_internal_member=True)
        user_attribute = UserAttribute.objects.create(user=user)
        EmailAddress.objects.create(email = email, verified = True, primary = True, user = user)
        return user,password

    def create_thread(self,user,team):
        print("data--->",user,team)
        team_obj = Team.objects.get(id=team)
        from ai_marketplace.serializers import ThreadSerializer
        # data = [{'first_person':user.id,'second_person':i.internal_member_id} for i in team_obj.internal_member_team_info.all()]
        for i in team_obj.internal_member_team_info.all():
            thread_ser = ThreadSerializer(data={'first_person':user.id,'second_person':i.internal_member_id})
            if thread_ser.is_valid():
                thread_ser.save()
            else:
                print("Errors--->",thread_ser.errors)


    @integrity_error
    def create(self,request):
        data = request.POST.dict()
        email = data.get('email')
        team_name = Team.objects.get(id=data.get('team')).name
        role_name = Role.objects.get(id=data.get('role')).name
        enterprise_plans = os.getenv("ENTERPRISE_PLANS")
        existing = self.check_user(email,team_name)
        if existing:
            return Response(existing,status = status.HTTP_409_CONFLICT)
        print("plan_name----------->",get_plan_name(self.request.user.team.owner))
        if not get_plan_name(self.request.user.team.owner) in enterprise_plans:
            if InternalMember.objects.filter(team = self.request.user.team).count()>=20:
                return Response({'msg':'internal member count execeeded'},status=400)
        user,password = self.create_internal_user(data.get('name'),email)
        context = {'name':data.get('name'),'email': email,'team':team_name,'role':role_name,'password':password}
        serializer = InternalMemberSerializer(data={**request.POST.dict(),'internal_member':user.id,'status':1,\
                                              'added_by':request.user.id})
        if serializer.is_valid():
            serializer.save()
            auth_forms.internal_user_credential_mail(context)
            self.create_thread(request.user,data.get('team'))
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, pk):
        try:
            queryset = InternalMember.objects.get(Q(id=pk))
        except InternalMember.DoesNotExist:
            return Response(status=204)
        serializer =InternalMemberSerializer(queryset,data={**request.POST.dict()},partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self,request,pk):
        queryset = InternalMember.objects.all()
        internal_member = get_object_or_404(queryset, pk=pk)
        user = AiUser.objects.get(id = internal_member.internal_member_id)
        EmailAddress.objects.get(email = user.email).delete()
        user.is_active = False
        user.email = user.email+"_deleted_"+user.uid
        user.save()
        internal_member.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

def msg_send(user,vendor):
    from ai_marketplace.serializers import ThreadSerializer
    thread_ser = ThreadSerializer(data={'first_person':user.id,'second_person':vendor.id})
    if thread_ser.is_valid():
        thread_ser.save()
        thread_id = thread_ser.data.get('id')
    else:
        thread_id = thread_ser.errors.get('thread_id')
    print("Thread--->",thread_id)
    message = "You are invited as an editor by " + user.fullname + ".\n" + "An invitation has been sent to your registered email." + "\n" + "Click <b>Accept</b> to accept the invitation." + "\n" + "<i>Please note that the invitation is valid only for one week</i>"
    msg = ChatMessage.objects.create(message=message,user=user,thread_id=thread_id)
    notify.send(user, recipient=vendor, verb='Message', description=message,thread_id=int(thread_id))

from ai_workspace.models import Project,TaskAssign,TaskAssignInfo
class HiredEditorsCreateView(viewsets.ViewSet,PageNumberPagination):
    permission_classes = [IsAuthenticated]
    page_size = 10
    # filter_backends = [DjangoFilterBackend,SearchFilter,OrderingFilter]
    search_fields = ['hired_editor__fullname']

    def get_queryset(self):
        if self.request.user.team:
            queryset =HiredEditors.objects.filter(Q(user_id=self.request.user.team.owner.id))
        else:
            queryset =HiredEditors.objects.filter(Q(user_id=self.request.user.id))
        return queryset

    def filter_queryset(self, queryset):
        filter_backends = (DjangoFilterBackend,SearchFilter,OrderingFilter )
        for backend in list(filter_backends):
            queryset = backend().filter_queryset(self.request, queryset, view=self)
        return queryset

    def list(self, request):
        queryset_all = self.get_queryset()
        if not queryset_all.exists():
            return Response(status=204)
        queryset = self.filter_queryset(self.get_queryset())
        pagin_tc = self.paginate_queryset(queryset, request , view=self)
        serializer = HiredEditorSerializer(pagin_tc,many=True)
        response = self.get_paginated_response(serializer.data)
        return response

    @integrity_error
    def create(self,request):
        if request.user.team: user = request.user.team.owner
        else: user = request.user
        uid=request.POST.get('vendor_id')
        role = request.POST.get('role',2)
        vendor = AiUser.objects.get(uid=uid)
        own_agency_email = os.getenv("AILAYSA_AGENCY_EMAIL")
        existing = HiredEditors.objects.filter(user=user,hired_editor=vendor)
        if existing:
            return JsonResponse({"msg":"editor already existed in your hired_editors list.check his availability in chat and assign"},safe = False)
        else:
            role_name = Role.objects.get(id=role).name
            email = vendor.email
            if vendor.email == own_agency_email:
                serializer = HiredEditorSerializer(data={'user':user.id,'role':role,'hired_editor':vendor.id,'status':2,'added_by':request.user.id})
                if serializer.is_valid():
                    serializer.save()
                    return JsonResponse({"msg":"email and msg sent successfully"},safe = False)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            else:
                serializer = HiredEditorSerializer(data={'user':user.id,'role':role,'hired_editor':vendor.id,'status':1,'added_by':request.user.id})
                if serializer.is_valid():
                    serializer.save()
                    hired_editor_id = serializer.data.get('id')
                    ext = HiredEditors.objects.get(id = serializer.data.get('id'))
                    uid = urlsafe_base64_encode(force_bytes(hired_editor_id))
                    token = invite_accept_token.make_token(ext)
                    link = join(settings.TRANSEDITOR_BASE_URL,settings.EXTERNAL_MEMBER_ACCEPT_URL, uid,token)
                    context = {'name':vendor.fullname,'team':user.fullname,'role':role_name,'link':link}
                    auth_forms.external_member_invite_mail(context,email)
                    msg_send(user,vendor)
                    return JsonResponse({"msg":"email and msg sent successfully"},safe = False)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, pk):
        try:
            queryset = HiredEditors.objects.get(Q(id=pk))
        except HiredEditors.DoesNotExist:
            return Response(status=204)
        serializer =HiredEditorSerializer(queryset,data={**request.POST.dict()},partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self,request,pk):
        queryset = HiredEditors.objects.all()
        hr = get_object_or_404(queryset, pk=pk)
        pr = Project.objects.filter(ai_user = hr.user).filter(project_jobs_set__job_tasks_set__task_info__assign_to = hr.hired_editor)
        for obj in pr:
            rr = TaskAssign.objects.filter(task__job__project=obj).filter(assign_to = hr.hired_editor)
            for i in rr:
                TaskAssignInfo.objects.filter(task_assign=i).delete()
                i.assign_to = hr.user
                i.save()
        hr.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)



def invite_accept_notify_send(user,vendor):
    from ai_marketplace.serializers import ThreadSerializer
    receivers =  user.team.get_project_manager_only if user.team else []
    receivers.append(user)
    print("Receivers------------->",receivers)
    for i in receivers:
        thread_ser = ThreadSerializer(data={'first_person':i.id,'second_person':vendor.id})
        if thread_ser.is_valid():
            thread_ser.save()
            thread_id = thread_ser.data.get('id')
        else:
            thread_id = thread_ser.errors.get('thread_id')
        print("Thread--->",thread_id)
        if thread_id:
            message = "I am excited to accept your invitation, "+ vendor.fullname +". I eagerly anticipate our collaboration."
            msg = ChatMessage.objects.create(message=message,user=vendor,thread_id=thread_id)
            print("Msg obj-------------->",msg)
            notify.send(vendor, recipient=user, verb='Message', description=message,thread_id=int(thread_id))

@api_view(['POST'])
@permission_classes([AllowAny])
def invite_accept(request):#,uid,token):
    uid = request.POST.get('uid')
    token = request.POST.get('token')
    vendor_id = urlsafe_base64_decode(uid)
    obj = HiredEditors.objects.get(id=vendor_id)
    if obj is not None and invite_accept_token.check_token(obj, token):
        obj.status = 2
        obj.save()
        try:invite_accept_notify_send(obj.user,obj.hired_editor)
        except:pass
        print("success & updated")
        return JsonResponse({"type":"success","msg":"You have successfully accepted the invite"},safe=False)
    else:
        return JsonResponse({"type":"failure","msg":'Either link is already used or link is invalid!'},safe=False)
    # return JsonResponse({"msg":"Failed"},safe=False)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def teams_list(request):
    teams =[]
    try:
        my_team = Team.objects.get(owner_id = request.user.id)
        teams.append({'team_id':my_team.id,'team':my_team.name+'(self)'})
    except:
        print('No self team')
    ext =HiredEditors.objects.filter(Q(hired_editor = request.user.id)&Q(status=2))#.distinct('user_id')
    print(ext)
    for j in ext:
        try:
            team = Team.objects.get(owner_id = j.user_id)
            teams.append(({'team_id':team.id,'team':team.name,'role':j.role.name}))
        except:
            print("No team")
    return JsonResponse({'team_list':teams})


# @api_view(['POST'])
# @permission_classes([IsAuthenticated])
# def TransactionSessionInfo(request):
#     session_id = request.POST.get('session_id')
#     if settings.STRIPE_LIVE_MODE == True :
#         api_key = settings.STRIPE_LIVE_SECRET_KEY
#     else:
#         api_key = settings.STRIPE_TEST_SECRET_KEY

#     stripe.api_key = api_key

#     response = stripe.checkout.Session.retrieve(
#                  session_id
#                     )
#     # print("Bank Details")
#     # print()
#     # print(response)
#     if response.mode == "subscription":
#         try:
#             invoice =Invoice.objects.get(subscription=response.subscription)
#         except Invoice.DoesNotExist:
#              return JsonResponse({"msg":"unable to find related data"},status=204,safe = False)
#         charge = invoice.charge
#         # if invoice == None:

#         #     return JsonResponse({"msg":"unable to find related data"},status=204,safe = False)
#         pack = CreditPack.objects.get(product__prices__id=invoice.plan.id,type="Subscription")
#         return JsonResponse({"email":charge.receipt_email,"purchased_plan":pack.name,"paid_date":charge.created,"amount":charge.amount,"plan_duration_start":invoice.subscription.current_period_start,"plan_duration_end":invoice.subscription.current_period_end,"paid":charge.paid,"payment_type":charge.payment_method.type,"txn_id":charge.balance_transaction_id},status=200,safe = False)

#     elif response.mode == "payment":
#         try:
#             charge = Charge.objects.get(payment_intent=response.payment_intent)
#         except Charge.DoesNotExist:
#              return JsonResponse({"msg":"unable to find related data"},status=204,safe = False)
#         pack = CreditPack.objects.get(product__prices__id=charge.metadata.get("price"),type="Addon")
#         return JsonResponse({"email":charge.receipt_email,"purchased_plan":pack.name,"paid_date":charge.created,"amount":charge.amount, "paid":charge.paid ,"payment_type":charge.payment_method.type, "txn_id":charge.balance_transaction_id},status=200,safe = False)
#     else:
#         return JsonResponse({"msg":"unable to find related data"},status=204,safe = False)



@api_view(['POST'])
def referral_users(request):
    ref_email = request.POST.get('email')
    try:
        user = AiUser.objects.get(email =ref_email)
        return Response({"msg":"User Already Exists"},status = 400)
    except AiUser.DoesNotExist:
        ref =ReferredUsers.objects.create(email=ref_email)
    return Response({"msg":"Successfully Added"},status = 201)

class GetTeamMemberView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class_External = HiredEditorSerializer
    serializer_class_Internal = InternalMemberSerializer

    def get_queryset_Internal(self):
        team = self.request.query_params.get('team')
        if team:
            queryset=InternalMember.objects.filter(team__name = team)
        else:
            queryset =InternalMember.objects.filter(team__owner_id=self.request.user.id)
        return queryset

    def get_queryset_External(self):
        team = self.request.query_params.get('team')
        if team:
            team_obj = Team.objects.get(name=team)
            queryset=HiredEditors.objects.filter(user= team_obj.owner)
        else:
            queryset =HiredEditors.objects.filter(Q(user_id=self.request.user.id))
        return queryset

    def list(self, request, *args, **kwargs):
        internal = self.serializer_class_Internal(self.get_queryset_Internal(), many=True)
        external = self.serializer_class_External(self.get_queryset_External(), many=True)
        return Response({
            "Internal_list": internal.data,
            "External_list": external.data
        })

@api_view(['GET',])
def get_team_name(request):
    user = AiUser.objects.get(id = request.user.id)
    try:
        name = user.ai_profile_info.organisation_name
    except:
        name = None
    return JsonResponse({"name":name})


def vendor_onboard_check(email,user):
    from ai_vendor.models import VendorsInfo
    from ai_vendor.models import VendorsInfo,VendorOnboardingInfo
    try:
        obj = VendorOnboarding.objects.get(email = email)
        current = "verified" if obj.get_status_display() == "Accepted" else "unverified"
        return JsonResponse({'id':obj.id,'email':email,'status':current})
    except:
        try:
            obj1 = VendorOnboardingInfo.objects.get(user = user)
            if obj1.onboarded_as_vendor == True:
                return JsonResponse({'msg':'onboarded_as_vendor and profile incomplete'})
        except:
            return Response(status=204)


@api_view(['POST',])
def vendor_form_filling_status(request):
    email = request.POST.get('email')
    try:
        user = AiUser.objects.get(email=email)
        if user.is_vendor == True:
            res = vendor_onboard_check(email,user)
            return res
        else:
            return Response(status=204)
    except:
        res = vendor_onboard_check(email,None)
        return res

class VendorRenewalTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        return (
            six.text_type(user.pk) + six.text_type(timestamp) + six.text_type(user.is_vendor)
        )


vendor_renewal_accept_token = VendorRenewalTokenGenerator()

@api_view(['POST',])
def vendor_renewal(request):
    email = request.POST.get('email')
    print(email)
    user = AiUser.objects.get(email=email)
    uid = urlsafe_base64_encode(force_bytes(user.id))
    token = vendor_renewal_accept_token.make_token(user)
    link = join(settings.TRANSEDITOR_BASE_URL,settings.VENDOR_RENEWAL_ACCEPT_URL, uid,token)
    auth_forms.vendor_renewal_mail(link,email)
    return JsonResponse({"msg":"email sent successfully"},safe = False)



@api_view(['POST'])
def vendor_renewal_invite_accept(request):
    uid = request.POST.get('uid')
    token = request.POST.get('token')
    user_id = urlsafe_base64_decode(uid)
    user = AiUser.objects.get(id=user_id)
    if user is not None and vendor_renewal_accept_token.check_token(user, token):
        user.is_vendor=True
        user.save()
        sub = subscribe_vendor(user)
        auth_forms.vendor_accepted_freelancer_mail(user)
        print("success & updated")
        return JsonResponse({"type":"success","msg":"Thank you for joining Ailaysa's freelancer marketplace"},safe=False)
    else:
        return JsonResponse({"type":"failure","msg":'Link expired. Please contact at support@ailaysa.com'},safe=False)

@api_view(['GET', ])
def change_old_password(request):
    for vendor_email in VENDORS_TO_ONBOARD:
        try:
            user = AiUser.objects.get(email=vendor_email)
            old_password = OldVendorPasswords.objects.get(email=vendor_email).password
            user.password = old_password
            user.from_mysql = True
            user.save()
        except Exception as e:
            print(e)
            continue
    return JsonResponse({"msg" : "Passwords successfully changed"})


@api_view(['GET'])
def vendor_renewal_change(request):
    data = request.GET.get('data')
    for vendor_email in VENDORS_TO_ONBOARD:
        user = AiUser.objects.get(email = vendor_email)
        user.is_vendor = data
        user.save()
    return JsonResponse({"msg": "changed successfully"})


import re
def striphtml(data):
    p = re.compile(r'<.*?>')
    return p.sub('', data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def vendor_onboard_complete(request):#######while using social signups################
    from ai_vendor.models import VendorsInfo,VendorLanguagePair
    source_lang = request.POST.get('source_language')
    target_lang = request.POST.get('target_language')
    cv_file = request.FILES.get('cv_file')
    if source_lang and target_lang:
        VendorLanguagePair.objects.create(user=request.user,source_lang_id = source_lang,target_lang_id =target_lang,primary_pair=True)
    if cv_file:
        VendorsInfo.objects.create(user=request.user,cv_file = cv_file )
        VendorOnboarding.objects.get_or_create(name=request.user.fullname,email=request.user.email,cv_file=cv_file,status=1)
    return JsonResponse({"msg": "Onboarding completed successfully"})


import quickemailverification
API_KEY = os.getenv('EMAIL_VERIFY_API_KEY')
client = quickemailverification.Client(API_KEY)

@api_view(['POST'])
@permission_classes([AllowAny])
def get_user(request):
    email = request.POST.get('email')
    email_str = email.split('@')[0]
    print("RR------------->",email_str)
    if email_str.split('+')[0] not in company_members_list:
        if "+" in email_str:
            return Response({"msg":"Invalid"})
        queryset = AiUser.objects.filter(Q(email__contains = email)|Q(email__icontains=email.split('+')[0]))
        if queryset:
            return Response({'user_exist':True})
        elif queryset.filter(email__contains='+'):
            return Response({'user_exist':True})
        else:
            quickemailverification = client.quickemailverification()
            try:
                response = quickemailverification.verify(email)
                print(response.body)
                if response.code == 200:
                    if response.body.get('result') == "invalid" or response.body.get('disposable') == 'true':
                        return Response({'msg':'Invalid'})
                    else:
                        return Response({'user_exist':False})
                else:
                    print(response.code)
                    return Response({'user_exist':False})
            except:
                return Response({'user_exist':False})
    else:
        try:
            user = AiUser.objects.get(email=email)
            return Response({'user_exist':True})
        except:
            return Response({'user_exist':False})
    
    # queryset = AiUser.objects.filter(Q(email__contains = email)|Q(email__icontains=email.split('+')[0])).filter(email__contains='+')
    # if queryset:
    #     return Response({'user_exist':True})
    # else:
    #     email_str = email.split('@')[0]
    #     if "+" in email_str:
    #         return Response({"msg":"Invalid Email"})
    #     return Response({'user_exist':False})
    # try:
    #     user = AiUser.objects.get(email=email)
    #     return Response({'user_exist':True})
    # except:
    #     return Response({'user_exist':False})

def get_soc_adapter(provider_id):
    match provider_id:
        case "google":
            return GoogleOAuth2Adapter
        case "proz":
            return ProzAdapter
        case default:
            return GoogleOAuth2Adapter
  

@api_view(['POST'])
@permission_classes([AllowAny])
def ai_social_login(request):
    provider_id = request.POST.get('provider')
    is_vendor = request.POST.get('is_vendor',None)
    product_id =request.POST.get('product_id',None)
    price_id =request.POST.get('price_id',None)
    process = request.POST.get('process',None)

    # base_url="http://127.0.0.1:8089"
    # print(reverse(provider_id +'_login'))
    # url=base_url+reverse(provider_id +'_login')

    # req = RequestFactory().get(
    #         reverse(provider_id + "_login"), dict(process="login")
    #     )
    state_data=dict()
    state_data["socialaccount_user_product"]=product_id
    state_data["socialaccount_user_price"]=price_id
    state_data["socialaccount_process"]=process
    state_data["socialaccount_provider"]=provider_id.upper()

    if is_vendor=='True' or  provider_id.upper() == "PROZ":
        #request.session['socialaccount_user_state']='vendor'
        state_data["socialaccount_user_state"]="vendor"

    else:
        #request.session['socialaccount_user_state']='customer'
        state_data["socialaccount_user_state"]="customer"
    adapter= get_soc_adapter(provider_id)

    # adapter = GoogleOAuth2Adapter(request)

    print("adapter",adapter)
    print("request",request)
    # adapter(request)
    provider=adapter(request).get_provider()

    print('provider>>',provider)
    print('requests>>',request)

    oauth2_login = OAuth2LoginView.adapter_view(adapter)

    # req = requests.get(url,params={'process':'login'}, headers={'Connection':'close'},allow_redirects=False)
    rs=oauth2_login(request)
    print(rs.url)
    print(rs)
    url =rs.url
    parsed = urlsplit(url)
    query_dict = parse_qs(parsed.query)
    query_dict['redirect_uri'][0] = getattr(settings,f"{provider_id.upper()}_CALLBACK_URL")
    state = query_dict['state'][0]
    query_new = urlencode(query_dict, doseq=True)
    parsed=parsed._replace(query=query_new)
    url_new = (parsed.geturl())

    soc_state = SocStates.objects.create(state=state,data=json.dumps(state_data))
    if soc_state == None:
        logger.warning(f"state not created {state}")

    # VendorOnboardingInfo.objects.get_or_create(user=user,onboarded_as_vendor=True)
    # req.close()

    # with requests.get(url, stream=True) as r:
    #     print(r.content)


    #ses = requests.Session()
    # ses.config['keep_alive'] = False

    #res = ses.get("http://127.0.0.1:8089/accounts/google/login/",params={'process':'login'},allow_redirects=False)
    #r = ses.get("http://127.0.0.1:8089/accounts/google/login/",params={'process':'login'},allow_redirects=False)
    # client = requests.session()

    # auth_redirect_url=req.headers['Location']
    return JsonResponse({"msg": "redirect","url":url_new},status=302)

def load_state(state_id,key=None):
    user_state=None
    try:
        soc_state=SocStates.objects.get(state=state_id)
        user_state = json.loads(soc_state.data)
    except SocStates.DoesNotExist:
        logger.error(f"invalid_state : {state_id}")
        return None
    except AttributeError:
        logger.error(f"key error user_state_not_found : {state_id}")
        return None
    return user_state

@api_view(['POST'])
@permission_classes([AllowAny])
def ai_social_callback(request):
    state = request.POST.get('state')
    # try:
    #     ses_id= request.COOKIES.get('sessionid')
    #     session=Session.objects.get(session_key=ses_id)
    # except BaseException as e:
    #     logger.warning("session not found ",str(e))
    #     return JsonResponse({"msg": "session expired or not found"},status=440)
    # #session=Session.objects.get(session_key="9helhig4y4izzshs93wtzj7ow9yjydi5")

    # print(session.get_decoded())
    # print(session.get_decoded().get('socialaccount_user_state',None))
    user_state=load_state(state)
    if user_state == None:
        logger.error(f"on social login state none {state}")
        return JsonResponse({"error": "invalid_state"},status=440)

    # request.session['socialaccount_state']=session.get_decoded().get('socialaccount_state')
    # # print("session print",request.session['socialaccount_state'])
    # print("code an data",request.GET.dict())
    # adapter = GoogleOAuth2Adapter(request)
    # oauth2_callback = OAuth2CallbackView.adapter_view(GoogleOAuth2Adapter)

    # rs = oauth2_callback(request)

    # print(rs)
    # print("content",rs.content)

    # code = request.GET.get('code')
    # data = {"code":code}
    # print("code",code)
    # request.method = 'POST'
    #request._request.data['code']=code
    print("request data",request.data)
    print("request in",request._request)
    print("request post dict",request._request.POST.dict())

    # data = request.POST.copy()

    # # remember old state
    # _mutable = data._mutable

    # # set to mutable
    # data._mutable = True

    # # сhange the values you want
    # data.update({'code':code})

    # # set mutable flag back
    # data._mutable = _mutable

    # request.POST = data

    #request._request.method = 'POST'

    # mutable = request.POST._mutable
    # request.POST._mutable = True
    # request.POST['code'] = code
    # request.POST._mutable = mutable


    #                    request._request.POST['code']=code
    # print("request post dict",request._request.POST.dict())
    # print("request data",request.data)
    # #url = "http://127.0.0.1:8089/auth/dj-rest-auth/google/"
    # #res= requests.post(url,data)
    # #print(res)
    # try:
    print(user_state)
    try:
        provider = user_state.get("socialaccount_provider")
        if provider=="GOOGLE":
            response = GoogleLogin.as_view()(request=request._request).data
        elif provider=="PROZ":
            response = ProzLogin.as_view()(request=request._request).data
        else:
            raise ValueError("no login view found")
    except BaseException as e:
        logger.error("on social login",str(e))
        return JsonResponse({"error":str(e)},status=400)

    required=[]
    try:
        response.get('access_token')
        resp_data =response
    except ValueError as e:
        logger.info("on social login",str(e))
        return JsonResponse({"error":f"{str(e)}"},status=400)

    process = user_state.get('socialaccount_process',None)

    try:
        if response.get('user').get('country')!=None:
            logger.info(f"user-{response.get('user').get('pk')} already registerd")
            process='login'
        else:
            process='signup'
    except AttributeError as e:
        logger.warning(f"user key not found in response {str(e)}")
        return JsonResponse({"error":"user_already_exist"},status=409)

    if process == 'signup':
        required.append('country')

        user_type = user_state.get('socialaccount_user_state',None)
        if user_type!=None:
                if user_type == 'vendor':
                    required.append('service_provider_type')


        resp_data.update({"required_details":required})
    else:
        resp_data.update({"required_details":None})

    user_product = user_state.get('socialaccount_user_product',None)
    user_price = user_state.get('socialaccount_user_price',None)


    if user_price and user_product :
        user_email=resp_data.get('user').get('email')
        try:
            temp_price=TempPricingPreference.objects.create(product_id=user_product,
                                            price_id=user_price,email=user_email)
        except BaseException as e:
            logger.error(f"unable to create temp pricing data for {user_email} :  {str(e)}")



    # except BaseException as e:
    #     return JsonResponse({"msg": "success"},status=200)

    #ss=SocialLoginSerializer(data={"code":code},context={"request":request,"view":GoogleLogin.as_view()})
    #response = GoogleLogin.post(request=request._request)
    #response = reverse("google_login",request)


    # r = requests.post(
    #         request.build_absolute_uri(reverse('google_login')),
    #         data = {'code':code}
    # )
    # print(r.content)


    return JsonResponse(resp_data,status=200)
    #return HttpResponseRedirect(reverse('google_login'))


class UserDetailView(viewsets.ViewSet):
    permission_classes=[IsAuthenticated]

    def get_object(self, pk):
        try:
            return AiUser.objects.get(user_id=pk)
        except AiUser.DoesNotExist:
            raise Http404

    def create(self,request):
        country = request.POST.get('country',None)
        # source_lang = request.POST.get('source_language',None)
        # target_lang = request.POST.get('target_language',None)
        service_provider_type = request.POST.get('service_provider_type',None)
        # cv_file = request.FILES.get('cv_file',None)
        state = request.POST.get('state',None)
        user = request.user

        user_state=load_state(state)


        if user_state == None:
            return Response({"error": "invalid_state_or_state_not_found"},status=440)

        if country==None and request.user.country==None:
            return Response({"error": "country_required"},status=400)

        user_type = user_state.get('socialaccount_user_state',None)
        if user_type == 'vendor':
            if not (service_provider_type):
                return Response({"error": "language_pair_required"},status=400)

        #user_pricing = user_state.get('socialaccount_user_state',None)


        # serializer = UserRegistrationSerializer(obj,data={**request.POST.dict()},partial=True)
        # if serializer.is_valid():
        #     serializer.save()
        #     return Response(serializer.data,status=200)
        # else:
        #     return Response(serializer.errors,status=400)
        try:
            with transaction.atomic():
                user_obj = AiUser.objects.get(id=user.id)
                if country:
                    if user_obj.country==None:
                        user_obj.country_id= country
                        queryset = CurrencyBasedOnCountry.objects.filter(country_id =user_obj.country_id)
                        if queryset:
                            user_obj.currency_based_on_country_id = queryset.first().currency_id
                        user_obj.save()
                        current_site = get_current_site(request)
                        auth_forms.send_welcome_mail(current_site,user_obj)
                        email_confirmed.send(
                        sender=user_obj.__class__,
                        request=request,
                        email_address=user_obj.email,
                        user=user_obj,
                        )
                    else:
                        logger.error(f"user_country_already_updated : {user_obj.uid}")
                        raise ValueError

                # if source_lang and target_lang:
                #     VendorLanguagePair.objects.create(user=user_obj,source_lang_id = source_lang,target_lang_id =target_lang,primary_pair=True)
                #     user_obj.is_vendor=True
                #     user_obj.save()
                #     sub=subscribe_vendor(user_obj)

                if service_provider_type:
                    if service_provider_type == 'agency':
                        sub = subscribe_lsp(user_obj)
                        user_obj.is_agency = True
                    elif service_provider_type == 'freelancer':
                        sub = subscribe_vendor(user_obj)
                    user_obj.is_vendor = True
                    user_obj.save() 
                    VendorOnboardingInfo.objects.create(user=user_obj,onboarded_as_vendor=True)


                # if cv_file:
                #     VendorsInfo.objects.create(user=user_obj,cv_file = cv_file )
                #     VendorOnboarding.objects.create(name=request.user.fullname,email=request.user.email,cv_file=cv_file,status=1)

            return Response({'msg':'details_updated_successsfully'},status=200)
        except BaseException as e:
            return Response({'error':f'updation failed {str(e)}'},status=400)


def get_lang_code(lang_code):
    if lang_code == "zh-CN" or lang_code == "zh":
        return "zh-Hans"
    elif lang_code == "zh-TW":
        return "zh-Hant"
    elif lang_code == "iw":
        return "he"
    else:
        return lang_code




from googletrans import Translator
@api_view(['GET'])
#@permission_classes([IsAuthenticated])
@permission_classes([AllowAny])
def lang_detect(request):
    from ai_staff.models import Languages
    text = request.GET.get('text')
    detector = Translator()
    lang = detector.detect(text).lang
    if isinstance(lang,list):
        lang = lang[0]
    lang_code = get_lang_code(lang)
    try:lang_obj = Languages.objects.get(locale__locale_code = lang_code)
    except:lang_obj = Languages.objects.get(locale__locale_code = 'en')
    return Response({'lang_id':lang_obj.id,'language':lang_obj.language})



def resync_instances(queryset):
## cloned from djstripe.admin.views
    for instance in queryset:
        api_key = instance.default_api_key
        try:
            if instance.djstripe_owner_account:
                stripe_data = instance.api_retrieve(
                    stripe_account=instance.djstripe_owner_account.id,
                    api_key=api_key,
                )
            else:
                stripe_data = instance.api_retrieve()
            instance.__class__.sync_from_stripe_data(stripe_data, api_key=api_key)
            print(f"Successfully Synced: {instance}")
        except stripe.error.PermissionError as error:
            print(error)
        except stripe.error.InvalidRequestError as error:
            print(f"Sync failed: {instance} error :{error}")
        except stripe.error.StripeErrorWithParamCode:
            print(f"Sync failed: {instance}")

def stripe_resync_instance(instance):
## cloned from djstripe.admin.views removed queryset
    api_key = instance.default_api_key
    try:
        if instance.djstripe_owner_account:
            stripe_data = instance.api_retrieve(
                stripe_account=instance.djstripe_owner_account.id,
                api_key=api_key,
            )
        else:
            stripe_data = instance.api_retrieve()
        instance.__class__.sync_from_stripe_data(stripe_data, api_key=api_key)
        print(f"Successfully Synced: {instance}")
    except stripe.error.PermissionError as error:
        print(error)
    except stripe.error.InvalidRequestError as error:
        print(f"Sync failed: {instance} error :{error}")
    except stripe.error.StripeErrorWithParamCode:
        print(f"Sync failed: {instance}")


@api_view(['GET'])
#@authorize_request
def oso_test(request):
    from ai_workspace.models import Task
    from ai_workspace_okapi.models import Document
    usr_attr = UserAttribute.objects.get(user= request.user)
    authorize(request, resource=usr_attr, actor=request.user, action="read")
    print("authorized user attribute")
    tsk = Task.objects.get(id=2867)
    doc = Document.objects.get(id=1684)
    authorize(request, resource=doc, actor=request.user, action="read")
    return JsonResponse({"msg":"sucess"},status=200)



@api_view(['GET'])
#@authorize_request
def oso_test_querys(request):
    from ai_workspace.models import Task
    from ai_workspace_okapi.models import Document
    usr_attr = UserAttribute.objects.get(user= request.user)
    authorize(request, resource=usr_attr, actor=request.user, action="read")
    print("authorized user attribute")
    # tsk = Task.objects.get(id=2867)
    #doc = Document.objects.filter(id=1684)
    repo_filter = authorize_model(request, Project, action="read")
    # fil = Document.objects.authorize(request, actor=request.user, action="read")
    pros =  Project.objects.filter(repo_filter)
    print("pros",pros)
    print("test")
    #Document.objects.authorize(request, actor=request.user, action="read")
    # print(fil)
    return JsonResponse({"msg":"sucess"},status=200)



from .models import CoCreateForm
from .serializers import AiUserDetailsSerializer, CoCreateFormSerializer,CampaignRegisterSerializer

class CampaignRegistrationView(viewsets.ViewSet):
    permission_classes = [AllowAny,]
    def create(self,request):
        # email = request.POST.get('email')
        try:
            serializer = CampaignRegisterSerializer(data={**request.POST.dict()})
            if serializer.is_valid():
                serializer.save()
            return Response({"msg":"User registerd successfully"},status=201)
        except ValueError as e:
            return Response({"msg":str(e)},status=409)
    
class CoCreateView(viewsets.ViewSet):
    permission_classes = [AllowAny]
    def create(self,request):
        name = request.POST.get("name")
        suggestion_type = request.POST.get("suggestion_type")
        suggestion = request.POST.get("suggestion")
        try:sug_type = SuggestionType.objects.get(id=suggestion_type).type_of_suggestion
        except:sug_type = None
        try:sug = Suggestion.objects.get(id=suggestion).suggestion
        except: sug = None
        email = request.POST.get("email")
        description = request.POST.get("description")
        app_suggestion_file = request.FILES.getlist('app_suggestion_file')
        # time =datetime.now(pytz.timezone('Asia/Kolkata'))
        time = date.today()
        template = 'cocreate_email.html'
        subject='Regarding App Suggestion'
        context = {'email': email,'name':name,'suggestion_type':sug_type,'suggestion':sug,'date':time,'description':description}
        serializer = CoCreateFormSerializer(data={**request.POST.dict(),'cocreate_file':app_suggestion_file})
        if serializer.is_valid():
            serializer.save()
            ins = CoCreateForm.objects.get(id=serializer.data.get('id'))
            if ins.cocreate_file.all():
                context.update({'files':ins.cocreate_file.all()})
            send_email_with_multiple_files(subject,template,context)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAdminUser])
def reports_dashboard(request):
    repo = AilaysaReport()
    users = repo.get_users()
    countries = repo.user_and_countries(users)
    paid_users = repo.paid_users(users)
    subs_info = repo.user_subscription_plans(users)
    data = {}
    data_sub = dict()
    data["total_users"] = users.count()
    data["total_languages"]=len(repo.total_languages_used())
    data["total_countries"] =len(countries)
    data["paid_users"]=paid_users.count()
    print(subs_info)
    for sub in subs_info[0]:
        data_sub[sub.get('plan__product__name')]=sub.get('plan__product__name__count')
        # data_sub[f"{sub[1].get('plan__product__name')} Trial" ]=sub[1].get('plan__product__name__count')

    for sub in subs_info[1]:
        data_sub[f"{sub.get('plan__product__name')} Trial"]=sub.get('plan__product__name__count')
    data["subscriptions"] = data_sub

    return JsonResponse(data,status=200)


def subscription_order(plan=None,trial=False):
    if plan!=None:
        current_plan = SubscriptionOrder.objects.get(plan__name=plan).id
        ls = list(SubscriptionOrder.objects.all().order_by('id').values_list('id',flat=True))
        ind = ls.index(current_plan)
        if trial:
            ind = ind-1
        return ls[ind+1:]
    else:
        return list(SubscriptionOrder.objects.all().order_by('id').values_list('id',flat=True))



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def subscription_customer_portal(request):

    user = request.user
    # if user.internal_member:
    #     user = user.team.owner,user
    try:
        sub = user.djstripe_customers.last().subscription 
        # if sub.status!='active':
        #     sub = None
    except:
        logger.error(f"too many subscriptions returned {user.id}")
        sub = user.djstripe_customers.last().subscriptions.last()
        # return JsonResponse({'msg':'something went wrong'},status=400)

    if sub!=None:
        if sub.status != 'active':
            invoice = None
        else:
            invoice = sub.invoices.last()

        current_plan = {
            'plan_name':sub.plan.product.name ,
            'plan_status':sub.status,
            'plan_sub_total':invoice.subtotal if invoice!=None else 0,
            'plan_tax':invoice.tax if invoice!=None else 0,
            'plan_total':invoice.total if invoice!=None else 0
        }
        if sub.status=='active':
            plan = sub.plan.product.name
            trial = False
        elif sub.status=='trialing':
            plan = sub.plan.product.name
            trial = True
        else:
            plan = None
            trial = False
        sub_order = subscription_order(plan,trial)
    else:
        current_plan = None
        sub_order = subscription_order()

    
    data = {
        'current_plan':current_plan,
        'upgrades':[SubscriptionOrder.objects.get(id= order_id).plan.id for order_id in sub_order],
        'downgrades':[]

    }
    return JsonResponse(data,status=200)




@api_view(['POST',])
@permission_classes([IsAuthenticated,])
def account_troubleshoot(request):
    user = request.user
    check_obj = AilaysaTroubleShoot(user)
    check_obj.account_signup_check()
    issues = check_obj.issues_found
    for issue in issues:
        AiTroubleshootData.objects.create(user=user,issue=issue)
    return Response({"msg":"troubleshoot_done","issues_found":[issue.issue for issue in issues]},status=200)


@api_view(['PUT',])
@permission_classes([IsAuthenticated,])
def user_info_update(request):
    user = request.user
    country_id = request.POST.get('country')
    if user.is_internal_member: # country should not be updated for internal member
         return Response({"msg":"updation failed"},status=400)
    cust = user.djstripe_customers.last()

    if country_id not in ['',None]:
        return Response({"msg":"updation failed"},status=400)
    elif cust:
        return Response({"msg":"updation failed"},status=400)
    else:
        ser = AiUserDetailsSerializer(user,data={'country':country_id},partial=True)
        if ser.is_valid():
            ser.save()
            return Response(ser.data)
        return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)

from django.db.models import Sum

class AilaysaPurchasedUnits:
    def __init__(self,user):
        if user.is_internal_member == True:
            self.user = getattr(user.team, 'owner', None) if user.team is not None else None
        else:
            self.user = user

    def get_units_objs(self,service_name):
        current_time = timezone.now()
        units_objs = PurchasedUnitsCount.objects.filter(user=self.user).filter(Q(expires_at__gte=current_time)|Q(expires_at=None)).filter(
            ailaysa_service=service_name).order_by('created_at')
        return units_objs

    def get_units(self,service_name): #total_units_left
        units_objs= self.get_units_objs(service_name=service_name)
        units_left = units_objs.aggregate(Sum('units_left'))['units_left__sum']
        units_buyed = units_objs.aggregate(Sum('intial_units'))['intial_units__sum']
        return {"total_intial_units":units_buyed if units_buyed!=None else 0  ,
                "total_units_left":units_left if units_left!=None else 0 }

    def deduct_units(self,service_name,to_deduct_units):
        units_objs= self.get_units_objs(service_name)
        if to_deduct_units > self.get_units(service_name)['total_units_left']:
             raise ValueError ('deducting more than available credits')
        carry_units = 0
        print("objs" , units_objs)
        print("to_deduct_units-->out" , to_deduct_units)
        with transaction.atomic():
            for i in units_objs:
                if to_deduct_units <= i.units_left:
                    units = i.units_left - to_deduct_units
                    i.units_left = units
                    i.save()
                    to_deduct_units = 0
                    print("inside detect")
                elif to_deduct_units > i.units_left:
                    carry_units = to_deduct_units - i.units_left
                    i.units_left = 0
                    i.save()
                    print("carry units",carry_units)
                    print("inside non detect")
                if carry_units == 0:
                    print("inside carry")
                    print("to_de",to_deduct_units)
                    to_deduct_units = 0
                    break
                else:
                    to_deduct_units = carry_units
                    carry_units = 0
            if to_deduct_units != 0:
                raise ValueError ('deducting more than available credits')
            

 




class MarketingBootcampViewset(viewsets.ViewSet):
    permission_classes = [AllowAny]
    def get_object(self, pk):
        try:
            return MarketingBootcamp.objects.get(id=pk)
        except MarketingBootcamp.DoesNotExist:
            raise Http404

    def create(self,request):
        from .tasks import send_bootcamp_mail
        file = request.FILES.get('file')
        if file and str(file).split('.')[-1] not in ['docx','pdf','doc']: 
            return Response({'msg':'only docx .pdf .doc suppported file'},status=400)
        serializer = MarketingBootcampSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            instance = self.get_object(serializer.data.get('id',None))
            send_bootcamp_mail.apply_async((instance.id,),queue='low-priority')
            return Response(serializer.data)
            # if instance.file:
            #     file_path = instance.file.path
            # else:
            #     file_path = None
            # sent = auth_forms.bootcamp_marketing_ack_mail(user_name = instance.name,
            #                                        user_email=instance.email,
            #                                        file_path=file_path)
            # auth_forms.bootcamp_marketing_response_mail(user_name=instance.name,
            #                                             user_email=instance.email)
            # if sent:

            #     return Response({'msg':'Mail sent Successfully'})
            # else:
            #     return Response({'msg':'Mail Not sent'})
        return Response(serializer.errors)
    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def internal_editors_list(request):
    user = request.user
    owner = request.user.team.owner if request.user.team else None
    if owner:
        team_obj = Team.objects.get(owner = owner)
        queryset = InternalMember.objects.filter(team=owner.team,role_id=2).order_by('internal_member__fullname')
        serializer = InternalMemberSerializer(queryset,many=True)
        return Response(serializer.data)
    else:
        return JsonResponse({'msg':'you are having no team'},status=400)