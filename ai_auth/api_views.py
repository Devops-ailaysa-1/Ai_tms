from djstripe.models.billing import Plan, TaxId
from rest_framework import response
from django.urls import reverse
from stripe.api_resources import subscription
from ai_auth.access_policies import MemberCreationAccess
from ai_auth.serializers import (BillingAddressSerializer, BillingInfoSerializer,
                                ProfessionalidentitySerializer,UserAttributeSerializer,
                                UserProfileSerializer,CustomerSupportSerializer,ContactPricingSerializer,
                                TempPricingPreferenceSerializer, UserTaxInfoSerializer,AiUserProfileSerializer,
                                CarrierSupportSerializer,VendorOnboardingSerializer,GeneralSupportSerializer,
                                TeamSerializer,InternalMemberSerializer,ExternalMemberSerializer)
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from django.shortcuts import get_object_or_404
#from ai_auth.serializers import RegisterSerializer,UserAttributeSerializer
from rest_framework import generics , viewsets
from ai_auth.models import (AiUser, BillingAddress, Professionalidentity,
                            UserAttribute,UserProfile,CustomerSupport,ContactPricing,
                            TempPricingPreference,CreditPack, UserTaxInfo,AiUserProfile,
                            Team,InternalMember,ExternalMember)
from django.http import Http404,JsonResponse
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_text
from django.contrib.auth.tokens import PasswordResetTokenGenerator
# from django.utils import six
from rest_framework import status
from django.db import IntegrityError
from django.contrib.auth.hashers import check_password,make_password
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import renderers
from rest_framework.decorators import api_view,permission_classes
from django.core.mail import EmailMessage
from django.template import Context
from django.template.loader import get_template
from django.template.loader import render_to_string
from datetime import datetime,date
from djstripe.models import Price,Subscription,InvoiceItem,PaymentIntent,Charge,Customer,Invoice,Product,TaxRate
import stripe
from django.conf import settings
from ai_staff.models import IndianStates, SupportType,JobPositions,SupportTopics,Role
from django.db.models import Q
from  django.utils import timezone
import time,pytz,six
from dateutil.relativedelta import relativedelta
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
    msg = EmailMessage(subject, content, settings.DEFAULT_FROM_EMAIL , to=['thenmozhivijay20@gmail.com',])#to emailaddress need to change
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
    return Response({'msg':'Payment Session Generated ','stripe_session_url':response.url}, status=307)


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
            return Response({'subscription_name':sub_name,'sub_status':subscriptions.status,'sub_price_id':subscriptions.plan.id,'interval':subscriptions.plan.interval,'sub_period_end':subscriptions.current_period_end,'sub_currency':subscriptions.plan.currency,'sub_amount':subscriptions.plan.amount,'trial':trial}, status=200)
        else:
            return Response({'subscription_name':None,'sub_status':None,'sub_price_id':None,'interval':None,'sub_period_end':None,'sub_currency':None,'sub_amount':None,'trial':None}, status=200)
    if is_active == (True,True):
        customer = Customer.objects.get(subscriber=request.user)
        #subscription = Subscription.objects.filter(customer=customer).last()
        subscription=customer.subscriptions.filter(Q(status='trialing')|Q(status='active')).last()
        trial = 'true' if subscription.metadata.get('type') == 'subscription_trial' else 'false'
       # sub_name = SubscriptionPricing.objects.get(stripe_price_id=subscription.plan.id).plan
        sub_name = CreditPack.objects.get(product__id=subscription.plan.product_id,type='Subscription').name
        return Response({'subscription_name':sub_name,'sub_status':subscription.status,'sub_price_id':subscription.plan.id,'interval':subscription.plan.interval,'sub_period_end':subscription.current_period_end,'sub_currency':subscription.plan.currency,'sub_amount':subscription.plan.amount,'trial':trial}, status=200)
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
    def create(self,request):
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
                pro=CreditPack.objects.get(name='Pro')
                if user.country.id == 101 :
                    currency = 'inr'
                else:
                    currency ='usd'
                price = Plan.objects.filter(product_id=pro.product,currency=currency,interval='month').last()
                response=subscribe_trial(price,customer)
                print(response)
                #customer.subscribe(price=price)
                return Response({'msg':'User Successfully created','subscription':'Pro_Trial'}, status=201)
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

    def create(self,request):
        name = request.POST.get("name")
        email = request.POST.get("email")
        cv_file = request.FILES.get('cv_file')
        today = date.today()
        template = 'vendor_onboarding_email.html'
        subject='Regarding Vendor Onboarding'
        context = {'email': email,'name':name,'file':cv_file,'date':today}
        serializer = VendorOnboardingSerializer(data={**request.POST.dict(),'cv_file':cv_file})
        if serializer.is_valid():
            serializer.save()
            send_email(subject,template,context)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

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
            return Response(status=204)
        serializer = TeamSerializer(queryset)
        return Response(serializer.data)

    @integrity_error
    def create(self,request):
        user_id = request.POST.get('user_id')
        username = AiUser.objects.get(id =user_id).fullname
        teamname = username + "'s team"
        serializer =TeamSerializer(data={'name':teamname,'owner':user_id})
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
        return (
            six.text_type(user.pk) + six.text_type(timestamp) + six.text_type(user.is_active)
        )


invite_accept_token = TokenGenerator()

class InternalMemberCreateView(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    def list(self, request):
        print(request.user.id)
        queryset =InternalMember.objects.filter(team__owner_id=request.user.id)
        if not queryset.exists():
            return Response(status=204)
        serializer = InternalMemberSerializer(queryset,many=True)
        return Response(serializer.data)

    @integrity_error
    def create(self,request):
        data = request.POST.dict()
        team = data.get('team')
        email = data.get('email')
        role = data.get('role')
        role_name = Role.objects.get(id=role).name
        today = date.today()
        team_name = Team.objects.get(id=team).name
        functional_identity = request.POST.get('functional_identity')
        password = AiUser.objects.make_random_password()
        print("randowm pass",password)
        hashed = make_password(password)
        template = 'Internal_member_credential_email.html'
        subject='Regarding Login credentials'
        context = {'name':data.get('name'),'email': email,'team':team_name,'role':role_name,'password':password,'date':today}
        user = AiUser.objects.create(fullname =data.get('name'),email = email,password = hashed,is_internal_member=True)
        serializer = InternalMemberSerializer(data={'team':team,'role':role,'internal_member':user.id,'functional_identity':functional_identity})
        if serializer.is_valid():
            serializer.save()
            send_email_user(subject,template,context,email)
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
        internal_member.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)



class ExternalMemberCreateView(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    def list(self, request):
        print(request.user.id)
        queryset =ExternalMember.objects.filter(Q(team__owner_id=request.user.id) & Q(status = 2))
        if not queryset.exists():
            return Response(status=204)
        serializer = ExternalMemberSerializer(queryset,many=True)
        return Response(serializer.data)

    @integrity_error
    def create(self,request):
        team = request.POST.get('team')
        if team == None:
            team = Team.objects.get(owner_id=request.user.id).id
            team_name = request.user.fullname
            template = 'External_member_pro_invite_email.html'
        else:
            template = 'External_member_business_invite_email.html'
            team_name = Team.objects.get(id=team).name
        uid=request.POST.get('vendor_id')
        role = request.POST.get('role')
        vendor = AiUser.objects.get(uid=uid)
        # team_name = Team.objects.get(id=team).name
        role_name = Role.objects.get(id=role).name
        email = vendor.email
        serializer = ExternalMemberSerializer(data={'team':team,'role':role,'external_member':vendor.id,'status':1})
        if serializer.is_valid():
            serializer.save()
            external_member_id = serializer.data.get('id')
            link = request.build_absolute_uri(reverse('accept', kwargs={'uid':urlsafe_base64_encode(force_bytes(external_member_id)),'token':invite_accept_token.make_token(vendor)}))
            # template = 'External_member_invite_email.html'
            subject='Ailaysa MarketPlace Invite'
            context = {'name':vendor.fullname,'team':team_name,'role':role_name,'link':link}
            send_email_user(subject,template,context,email)
            return JsonResponse({"msg":"email sent successfully"},safe = False)
        # # link = request.build_absolute_uri('/team/external_member/accept/'+urlsafe_base64_encode(force_bytes(vendor.id))+'/'+urlsafe_base64_encode(force_bytes(team.id))+'/'+invite_accept_token.make_token(user)+'/')
        # # link = request.build_absolute_uri(reverse('accept', kwargs={'uid':urlsafe_base64_encode(force_bytes(vendor.id)),'teamid':urlsafe_base64_encode(force_bytes(team)),'roleid':urlsafe_base64_encode(force_bytes(role)),'token':invite_accept_token.make_token(vendor)}))
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, pk):
        try:
            queryset = ExternalMember.objects.get(Q(id=pk))
        except ExternalMember.DoesNotExist:
            return Response(status=204)
        serializer =ExternalMemberSerializer(queryset,data={**request.POST.dict()},partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self,request,pk):
        queryset = ExternalMember.objects.all()
        external_member = get_object_or_404(queryset, pk=pk)
        external_member.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

@permission_classes([IsAuthenticated])
def invite_accept(request,uid,token):
    vendor_id = urlsafe_base64_decode(uid)
    vendor = ExternalMember.objects.get(id=vendor_id)
    user = AiUser.objects.get(id=vendor.external_member_id)
    if user is not None and invite_accept_token.check_token(user, token):
        vendor.status = 2
        vendor.save()
        print("success & updated")
        return JsonResponse({"msg":"success"},safe=False)
    return JsonResponse({"msg":"Failed"},safe=False)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def teams_list(request):
    teams =[]
    my_team = Team.objects.get(owner_id = request.user.id).id
    teams.append({'team_id':my_team,'team':'self'})
    ext = ExternalMember.objects.filter(external_member = request.user.id)
    for j in ext:
        teams.append(({'team_id':j.team.id,'team':j.team.name,'role':j.role.name}))
    return JsonResponse({'My_external_team':teams})
