from djstripe.models.billing import Plan, TaxId
from rest_framework import response
from stripe.api_resources import subscription
from ai_auth.serializers import (BillingAddressSerializer, BillingInfoSerializer, OfficialInformationSerializer, PersonalInformationSerializer,
                                ProfessionalidentitySerializer,UserAttributeSerializer,
                                UserProfileSerializer,CustomerSupportSerializer,ContactPricingSerializer,
                                TempPricingPreferenceSerializer, UserTaxInfoSerializer,AiUserProfileSerializer)
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from django.shortcuts import get_object_or_404
#from ai_auth.serializers import RegisterSerializer,UserAttributeSerializer
from rest_framework import generics , viewsets
from ai_auth.models import (AiUser, BillingAddress, OfficialInformation, PersonalInformation, Professionalidentity,
                            UserAttribute,UserProfile,CustomerSupport,ContactPricing,
                            TempPricingPreference,CreditPack, UserTaxInfo,AiUserProfile)
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
from djstripe.models import Price,Subscription,InvoiceItem,PaymentIntent,Charge,Customer,Invoice,Product,TaxRate
import stripe
from django.conf import settings
from ai_staff.models import IndianStates, SupportType
from django.db.models import Q
from ai_auth.signals import update_billing_address
from  django.utils import timezone
import time
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
    msg = EmailMessage(subject, content, settings.DEFAULT_FROM_EMAIL , to=['support@ailaysa.com',])#to emailaddress need to change
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
    domain_url = settings.CLIENT_BASE_URL
    if settings.STRIPE_LIVE_MODE == True :
        api_key = settings.STRIPE_LIVE_SECRET_KEY
    else:
        api_key = settings.STRIPE_TEST_SECRET_KEY

    stripe.api_key = api_key

    tax_rate =[]

    if trial == True :
        date_time = timezone.now()
        trial_end = int(time.mktime(date_time.timetuple()))
        print("trial_end>>>",trial_end)
    else:
        trial_end = None

    if user.country.sortname == 'IN':
        addr=BillingAddress.objects.get(user=user)
        print(addr.state)
        state = IndianStates.objects.filter(state_name__icontains=addr.state)
        if state.exists() and state.first().state_code == 'TN':
            tax_rate=[TaxRate.objects.get(display_name = 'CGST').id,TaxRate.objects.get(display_name = 'SGST').id]
        elif state.exists():
            tax_rate=[TaxRate.objects.get(display_name = 'IGST').id,]
    else:
        tax_rate=None
    #if user.billing
    # print("tax_rate",tax_rate)
    # print("user country>>",user.country.sortname)
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
                tax_rate=[TaxRate.objects.get(display_name = 'CGST').id,TaxRate.objects.get(display_name = 'SGST').id]
            elif state.exists():
                tax_rate=[TaxRate.objects.get(display_name = 'IGST').id,]
        else:
            tax_rate=None
    return tax_rate


def subscribe_trial(price,customer=None):
    product_name = Price.objects.get(id = price).product.name
    domain_url = settings.CLIENT_BASE_URL
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
    domain_url = settings.CLIENT_BASE_URL
    if settings.STRIPE_LIVE_MODE == True :
        api_key = settings.STRIPE_LIVE_SECRET_KEY
    else:
        api_key = settings.STRIPE_TEST_SECRET_KEY

    stripe.api_key = api_key

    checkout_session = stripe.checkout.Session.create(
        client_reference_id=Aicustomer.subscriber,
        success_url=domain_url + 'success?session_id={CHECKOUT_SESSION_ID}',
        cancel_url=domain_url + 'cancel/',
        payment_method_types=['card'],
        mode='payment',
        customer = Aicustomer.id,
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
    domain_url = settings.CLIENT_BASE_URL
    if settings.STRIPE_LIVE_MODE == True :
        api_key = settings.STRIPE_LIVE_SECRET_KEY
    else:
        api_key = settings.STRIPE_TEST_SECRET_KEY

    stripe.api_key = api_key
    session = stripe.billing_portal.Session.create(
        customer=customer.id,
        return_url=domain_url+'dashboard',
    )
    return session


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
    quantity=request.POST.get('quantity',1)
    try:
        price = Price.objects.get(id=request.POST.get('price'))
    except (KeyError,Price.DoesNotExist) :
         return Response({'msg':'Invalid price'}, status=406)

    cust=Customer.objects.get(subscriber=user)
    if user.country.sortname == 'IN':
        try:
            addr=BillingAddress.objects.get(user=user)
        except BillingAddress.DoesNotExist:
            return Response({'Error':'Billing Address Not Found'}, status=412)
        state = IndianStates.objects.filter(state_name__icontains=addr.state)
        if state.exists() and state.first().state_code == 'TN':
            tax_rate=[TaxRate.objects.get(display_name = 'CGST').id,TaxRate.objects.get(display_name = 'SGST').id]
        elif state.exists():
            tax_rate=[TaxRate.objects.get(display_name = 'IGST').id,]
    else:
        tax_rate=None
    response = create_checkout_session_addon(price,cust,tax_rate,quantity)

    #request.POST.get('')
    return Response({'msg':'Payment Session Generated ','stripe_session_url':response.url}, status=307)


def subscriptin_modify_default_tax_rate(customer,addr):
    if settings.STRIPE_LIVE_MODE == True :
        api_key = settings.STRIPE_LIVE_SECRET_KEY
    else:
        api_key = settings.STRIPE_TEST_SECRET_KEY

    stripe.api_key = api_key

    if customer.subscriber.country.sortname == 'IN' and addr.country.sortname == 'IN':
        state = IndianStates.objects.filter(state_name__icontains=addr.state)
        if state.exists() and state.first().state_code == 'TN':
            tax_rates=[TaxRate.objects.get(display_name = 'CGST').id,TaxRate.objects.get(display_name = 'SGST').id]
        elif state.exists():
            tax_rates=[TaxRate.objects.get(display_name = 'IGST').id,]
    else:
        tax_rates=None

    if tax_rates != None:
        response = stripe.Subscription.modify(
        customer.subscriptions.last().id,
        default_tax_rates=tax_rates
        )
        print(response)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def customer_portal_session(request):
    user = request.user
    try:
        customer = Customer.objects.get(subscriber=user)
        addr = BillingAddress.objects.get(user=request.user)
        session=generate_portal_session(customer)
        if not customer.subscriptions.exists():
             return Response({'msg':'User has No Active Subscription'}, status=402)
        subscriptin_modify_default_tax_rate(customer,addr)
    except Customer.DoesNotExist:
        return Response({'msg':'Unable to Generate Customer Portal Session'}, status=400)
    except BillingAddress.DoesNotExist:
        return Response({'Error':'Billing Address Not Found'}, status=412)
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
            sub_name = CreditPack.objects.get(product__id=subscriptions.plan.product_id,type='Subscription').name
            return Response({'msg':'User have No Active Subscription','prev_subscription':sub_name,'prev_sub_price_id':subscriptions.plan.id,'prev_sub_status':subscriptions.status}, status=402)
        else:
            return Response({'msg':'User have No Active Subscription','prev_subscription':None,'prev_sub_price_id':None,'prev_sub_status':None}, status=402)
    if is_active == (True,True):
        customer = Customer.objects.get(subscriber=request.user)
        #subscription = Subscription.objects.filter(customer=customer).last()
        subscription=customer.subscriptions.filter(Q(status='trialing')|Q(status='active')).last()
       # sub_name = SubscriptionPricing.objects.get(stripe_price_id=subscription.plan.id).plan
        sub_name = CreditPack.objects.get(product__id=subscription.plan.product_id,type='Subscription').name
        return Response({'subscription_name':sub_name,'sub_status':subscription.status,'sub_price_id':subscription.plan.id,'interval':subscription.plan.interval,'sub_period_end':subscription.current_period_end,'sub_currency':subscription.plan.currency,'sub_amount':subscription.plan.amount}, status=200)
    if is_active == (False,False):
        return Response({'msg':'Not a Stripe Customer'}, status=206)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def buy_subscription(request):
    user = request.user
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
        if customer.subscription.status == "trialing":
            session= create_checkout_session(user=user,price=price,customer=customer,trial=True)
        else:
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
                try:
                    address = BillingAddress.objects.get(user=user)
                    session = create_checkout_session(user=user,price=price,customer=customer)
                except BillingAddress.DoesNotExist:
                   return Response({'Error':'Billing Address Not Found'}, status=412)
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
        serializer = BillingAddressSerializer(data={**request.POST.dict()})
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
        serializer = BillingAddressSerializer(queryset,data={**request.POST.dict()},partial=True)
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


class UserTaxInfoView(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    def list(self, request):
        queryset = UserTaxInfo.objects.filter(user=request.user)
        if not queryset.exists():
            return Response(status=204)
        serializer = UserTaxInfoSerializer(queryset,many=True)
        return Response(serializer.data)

    def create(self,request):
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
            if request.POST.get('stripe_tax_id') == None and request.POST.get('tax_id') == None:
                taxid = TaxId.objects.filter(customer__subscriber=request.user,value=queryset.tax_id,type=queryset.stripe_tax_id.tax_code).first()
                user_taxid_delete(taxid)
                queryset.delete()
                return Response({'msg':'Successfully Deleted'}, status=200)
            if request.POST.get('stripe_tax_id') == queryset.stripe_tax_id and request.POST.get('tax_id') == queryset.tax_id:
                return Response({'msg':'Successfully Updated'}, status=200)
            else:
                taxid = TaxId.objects.filter(customer__subscriber=request.user,value=queryset.tax_id,type=queryset.stripe_tax_id.tax_code).first()
                user_taxid_delete(taxid)
                queryset.delete()
        except UserTaxInfo.DoesNotExist:
            return Response(status=204)
        #queryset = BillingAddress.objects.get(id=pk)
        #if queryset
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

    def update(self, request, pk=None):
        try:
            queryset = AiUserProfile.objects.get(id=pk)
        except UserTaxInfo.DoesNotExist:
            return Response(status=204)
        serializer =AiUserProfileSerializer(queryset,data={**request.POST.dict()},partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"Msg":"Profile Updated"})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
