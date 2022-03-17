from logging import INFO
import re , requests
from django.core.mail import send_mail
from ai_auth import forms as auth_forms
from allauth.account.models import EmailAddress
from djstripe.models.billing import Plan, TaxId
from rest_framework import response
from django.urls import reverse
from os.path import join
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from stripe.api_resources import subscription
from ai_auth.access_policies import MemberCreationAccess,InternalTeamAccess,TeamAccess
from ai_auth.serializers import (BillingAddressSerializer, BillingInfoSerializer,
                                ProfessionalidentitySerializer,UserAttributeSerializer,
                                UserProfileSerializer,CustomerSupportSerializer,ContactPricingSerializer,
                                TempPricingPreferenceSerializer, UserTaxInfoSerializer,AiUserProfileSerializer,
                                CarrierSupportSerializer,VendorOnboardingSerializer,GeneralSupportSerializer,
                                TeamSerializer,InternalMemberSerializer,HiredEditorSerializer)
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from django.shortcuts import get_object_or_404
#from ai_auth.serializers import RegisterSerializer,UserAttributeSerializer
from rest_framework import generics , viewsets
from ai_auth.models import (AiUser, BillingAddress, Professionalidentity, ReferredUsers,
                            UserAttribute,UserProfile,CustomerSupport,ContactPricing,
                            TempPricingPreference,CreditPack, UserTaxInfo,AiUserProfile,
                            Team,InternalMember,HiredEditors,VendorOnboarding)
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
from djstripe.models import Price,Subscription,InvoiceItem,PaymentIntent,Charge,Customer,Invoice,Product,TaxRate
import stripe
from django.conf import settings
from ai_staff.models import IndianStates, SupportType,JobPositions,SupportTopics,Role, OldVendorPasswords
from django.db.models import Q
from  django.utils import timezone
import time,pytz,six
from dateutil.relativedelta import relativedelta
from ai_marketplace.models import Thread,ChatMessage
from ai_auth.utils import get_plan_name
from ai_auth.vendor_onboard_list import VENDORS_TO_ONBOARD


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
    file =context.get('file')
    msg = EmailMessage(subject, content, settings.DEFAULT_FROM_EMAIL , to=['support@ailaysa.com',])#to emailaddress need to change
    if file:
        msg.attach(file.name, file.read(), file.content_type)
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
        user = Customer.objects.get(subscriber_id = request.user.id).id
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
            name = Price.objects.get(id=i.metadata["price"]).product.name
            output ={"Name":name,"Quantity":i.metadata["quantity"],"Amount": (i.amount)/100,"Currency":i.currency,"Date":i.created.date(),"Receipt":add_on.receipt_url if add_on else None,"Status":"succeeded" if add_on else "incomplete"}
            out.append(output)
    else:
        out = []
    return JsonResponse({"out":out},safe=False)

def create_checkout_session(user,price,customer=None,trial=False):
    product_name = Price.objects.get(id = price).product.name
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

    checkout_session = stripe.checkout.Session.create(
        client_reference_id=user.id,
        success_url=domain_url + 'success?session_id={CHECKOUT_SESSION_ID}',
        cancel_url=domain_url + 'cancel/',
        payment_method_types=['card'],
        customer =customer.id,
        #customer_email=user.email,
        mode='subscription',
        line_items=[
            {
                'price': price,
                'quantity': 1,
                'tax_rates':tax_rate,
            }
        ],
        #billing_address_collection=addr_collect,
        customer_update={'address':'never','name':'never'},
        #tax_id_collection={'enabled':'True'},
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
            state = IndianStates.objects.filter(state_name__icontains=addr.state)
            if state.exists() and state.first().state_code == 'TN':
                tax_rate=[TaxRate.objects.filter(display_name = 'CGST').last().id,TaxRate.objects.filter(display_name = 'SGST').last().id]
            elif state.exists():
                tax_rate=[TaxRate.objects.filter(display_name = 'IGST').last().id,]
            #tax_rate=[TaxRate.objects.get(display_name = 'GST',description='IN GST').id,]
        else:
            tax_rate=None
    return tax_rate


def subscribe_trial(price,customer=None):
    product_name = Price.objects.get(id = price).product.name
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
        'price': price,
    },
    ],
    default_tax_rates=tax_rate,
    trial_period_days=14,

    metadata={'price':price.id,'product':product_name,'type':'subscription_trial'}
    )

    return subscription

def subscribe_vendor(user):
    plan = get_plan_name(user)
    cust = Customer.objects.get(subscriber=user)
    price = Price.objects.get(product__name="Pro - V",currency=cust.currency)
    if plan!= None and (plan != "Pro - V" and plan.startswith('Pro')):
        sub=subscribe(price=price,customer=cust)
        return sub


def subscribe(price,customer=None):
    product_name = Price.objects.get(id = price).product.name
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
        'price': price,
    },
    ],
    #default_tax_rates=tax_rate,
    #trial_period_days=14,

    metadata={'price':price.id,'product':product_name,'type':'subscription'}
    )

    return subscription



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
    checkout_session = stripe.checkout.Session.create(
        client_reference_id=Aicustomer.subscriber,
        success_url=domain_url + 'success?session_id={CHECKOUT_SESSION_ID}',
        cancel_url=domain_url + 'cancel/',
        payment_method_types=['card'],
        mode='payment',
        customer = Aicustomer.id,
        #billing_address_collection=addr_collect,
        customer_update={'address':'never','name':'never'},
        #tax_id_collection={'enabled':'True'},
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


def create_invoice_one_time(price_id,Aicustomer,tax_rate,quantity=1):
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
        customer = Customer.objects.get(subscriber=user)
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
        price = Price.objects.get(id=request.POST.get('price'))
    except (KeyError,Price.DoesNotExist) :
         return Response({'msg':'Invalid price'}, status=406)

    cust=Customer.objects.get(subscriber=user)
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
    if tax_rate != None:
        response = stripe.Subscription.modify(
        customer.subscriptions.last().id,
        default_tax_rates=tax_rate
        )
        print(response)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def customer_portal_session(request):
    user = request.user
    try:
        customer = Customer.objects.get(subscriber=user)
        #addr = BillingAddress.objects.get(user=request.user)
        session=generate_portal_session(customer)
        if not customer.subscriptions.exists():
             return Response({'msg':'User has No Active Subscription'}, status=402)
        subscriptin_modify_default_tax_rate(customer)
    except Customer.DoesNotExist:
        return Response({'msg':'Unable to Generate Customer Portal Session'}, status=400)
    # except BillingAddress.DoesNotExist:
    #     return Response({'Error':'Billing Address Not Found'}, status=412)
    # except Subscription:
    #     customer.
    return Response({'msg':'Customer Portal Session Generated','stripe_session_url':session.url,'strip_session_id':session.id}, status=307)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def check_subscription(request):
    is_active = is_active_subscription(request.user)
    if is_active == (False,True):
        customer = Customer.objects.get(subscriber=request.user)
        subscriptions = Subscription.objects.filter(customer=customer).last()
        if subscriptions is not None:
            trial = 'true' if subscriptions.metadata.get('type') == 'subscription_trial' else 'false'
            sub_name = CreditPack.objects.get(product__id=subscriptions.plan.product_id,type='Subscription').name
            return Response({'subscription_name':sub_name,'sub_status':subscriptions.status,'sub_price_id':subscriptions.plan.id,
                            'interval':subscriptions.plan.interval,'sub_period_end':subscriptions.current_period_end,'sub_currency':subscriptions.plan.currency,'sub_amount':subscriptions.plan.amount,'trial':trial,'canceled_at':subscriptions.canceled_at}, status=200)
        else:
            return Response({'subscription_name':None,'sub_status':None,'sub_price_id':None,'interval':None,'sub_period_end':None,'sub_currency':None,'sub_amount':None,'trial':None,'canceled_at':None}, status=200)
    if is_active == (True,True):
        customer = Customer.objects.get(subscriber=request.user)
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
        price = Price.objects.get(id=request.POST.get('price'))
        addr = BillingAddress.objects.get(user=request.user)
    except (KeyError,Price.DoesNotExist) :
        return Response({'msg':'Invalid price'}, status=406)
    except BillingAddress.DoesNotExist:
        return Response({'Error':'Billing Address Not Found'}, status=412)
    is_active = is_active_subscription(user)
    if not is_active == (False,False):
        customer= Customer.objects.get(subscriber=user)
        session=create_checkout_session(user=user,price=price,customer=customer)
        return Response({'msg':'Payment Session Generated ','stripe_session_url':session.url,'strip_session_id':session.id}, status=307)
    else:
        return Response({'msg':'No Stripe Account Found'}, status=404)




@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_currency(request):
    curr=Customer.objects.get(subscriber=request.user).currency
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
                customer = Customer.objects.get(subscriber=request.user)
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

                if price_id:
                    price = Plan.objects.get(id=price_id)
                    if (price.currency != currency) or (price.interval != 'month'):
                        price = Plan.objects.get(product=price.product,interval='month',currency=currency,livemode=livemode)

                else:
                    price = Plan.objects.filter(product_id=pro.product,currency=currency,interval='month',livemode=livemode).last()
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
    cust=Customer.objects.get(subscriber=user)
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
    if response.mode == "subscription":
        try:
            invoice =Invoice.objects.get(subscription=response.subscription)
        except Invoice.DoesNotExist:
             return JsonResponse({"msg":"unable to find related data"},status=204,safe = False)
        charge = invoice.charge
        # if invoice == None:

        #     return JsonResponse({"msg":"unable to find related data"},status=204,safe = False)
        pack = CreditPack.objects.get(product__prices__id=invoice.plan.id,type="Subscription")
        return JsonResponse({"email":charge.receipt_email,"purchased_plan":pack.name,"paid_date":charge.created,"currency":charge.currency,"amount":charge.amount,"plan_duration_start":invoice.subscription.current_period_start,"plan_duration_end":invoice.subscription.current_period_end,"plan_interval":invoice.subscription.plan.interval,"paid":charge.paid,"payment_type":charge.payment_method.type,
                            "txn_id":charge.balance_transaction_id,"receipt_url":charge.receipt_url},status=200,safe = False)

    elif response.mode == "payment":
        try:
            charge = Charge.objects.get(payment_intent=response.payment_intent)
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




class CarrierSupportCreateView(viewsets.ViewSet):

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
        context = {'email': email,'name':name,'job_position':job_name,'phonenumber':phonenumber,'date':time,'file':cv_file,'message':message}
        serializer = CarrierSupportSerializer(data={**request.POST.dict(),'cv_file':cv_file})
        if serializer.is_valid():
            serializer.save()
            send_email(subject,template,context)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GeneralSupportCreateView(viewsets.ViewSet):

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
        context = {'email': email,'name':name,'topic':topic_name,'phonenumber':phonenumber,'date':today,'file':support_file,'message':message}
        serializer = GeneralSupportSerializer(data={**request.POST.dict(),'support_file':support_file})
        if serializer.is_valid():
            serializer.save()
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
        cv_file = request.FILES.get('cv_file')
        serializer = VendorOnboardingSerializer(data={**request.POST.dict(),'cv_file':cv_file,'status':1})
        if serializer.is_valid():
            serializer.save()
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


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def account_delete(request):
    password_entered = request.POST.get('password')
    user = AiUser.objects.get(id =request.user.id)
    match_check = check_password(password_entered,user.password)
    if match_check:
        present = datetime.now()
        three_mon_rel = relativedelta(months=3)
        user.is_active = False
        user.deactivation_date = present.date()+three_mon_rel
        user.save()
        cancel_subscription(user)
    else:
        return Response({"msg":"password didn't match"},status = 400)
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
            queryset=InternalMember.objects.filter(team__name = team)
        else:
            queryset =InternalMember.objects.filter(team=self.request.user.team)
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
        existing = self.check_user(email,team_name)
        if existing:
            return Response(existing,status = status.HTTP_409_CONFLICT)
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
    message = "You are invited as an editor by "+user.fullname+".\n"+ "An invitation has been sent to your registered email." + "\n" + "Click Accept to accept the invitation." + "\n" + "Please note that the invitation is valid only for one week"
    msg = ChatMessage.objects.create(message=message,user=user,thread_id=thread_id)
    notify.send(user, recipient=vendor, verb='Message', description=message,thread_id=int(thread_id))

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
        existing = HiredEditors.objects.filter(user=user,hired_editor=vendor)
        if existing:
            return JsonResponse({"msg":"editor already existed in your hired_editors list.check his availability in chat and assign"},safe = False)
        else:
            role_name = Role.objects.get(id=role).name
            email = vendor.email
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
        hired_editor = get_object_or_404(queryset, pk=pk)
        hired_editor.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
# @permission_classes([IsAuthenticated])
def invite_accept(request):#,uid,token):
    uid = request.POST.get('uid')
    token = request.POST.get('token')
    vendor_id = urlsafe_base64_decode(uid)
    vendor = HiredEditors.objects.get(id=vendor_id)
    # user = AiUser.objects.get(id=vendor.external_member_id)
    # if user is not None and invite_accept_token.check_token(user, token):
    if vendor is not None and invite_accept_token.check_token(vendor, token):
        vendor.status = 2
        vendor.save()
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


def vendor_onboard_check(email):
    try:
        obj = VendorOnboarding.objects.get(email = email)
        print(obj)
        return JsonResponse({'id':obj.id,'email':email,'status':obj.get_status_display()})
    except VendorOnboarding.DoesNotExist:
        return Response(status=204)


@api_view(['POST',])
def vendor_form_filling_status(request):
    email = request.POST.get('email')
    print("Email---->",email)
    try:
        user = AiUser.objects.get(email=email)
        if user.is_vendor == True:
            return JsonResponse({"msg":"Already a vendor"})
        else:
            res = vendor_onboard_check(email)
            return res
    except:
        res = vendor_onboard_check(email)
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
