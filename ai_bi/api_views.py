from django.http import JsonResponse
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from ai_auth.reports import AilaysaReport
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from rest_framework import viewsets
from collections import Counter,OrderedDict
from ai_auth.models import AiUser,UserAttribute   
from ai_staff.models import Countries
from django.db.models import Count,Q
from django.utils import timezone
from datetime import timedelta
from ai_bi.serializers import AiUserSerializer,DjStripeUserSerializer,StipeCustomerSerialiizer,ChargeSerialiizer
from ai_bi.permissions import IsBiUser,IsBiAdmin
from rest_framework import response
from rest_framework.decorators import permission_classes
from ai_auth.utils import company_members_list
from functools import reduce
from operator import or_

def get_users(is_vendor=False,period=None,test=False):
        if test:
            users= AiUser.objects.filter(~Q(email__icontains='deleted')&~Q(email='AnonymousUser')&~Q(is_staff=True) \
                    &~Q(is_internal_member=True)&Q(is_vendor=is_vendor)&~reduce(or_,[Q(email__icontains=mail)for mail in company_members_list]))
        else:
            users= AiUser.objects.filter(~Q(email__icontains='deleted')&~Q(email='AnonymousUser')&~Q(is_staff=True) \
                    &~Q(is_internal_member=True)&Q(is_vendor=is_vendor)&~Q(email__icontains="+")&~reduce(or_,[Q(email__icontains=mail)for mail in company_members_list]))
        if period != None:
            start_date = timezone.now()
            end_date =start_date + timedelta(period)
            users = users.filter(date_joined__range=[start_date,end_date])
        return users


@api_view(['GET'])
@permission_classes([IsBiUser])
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

class Countries_listview(viewsets.ModelViewSet):
    permission_classes = [IsBiUser]
    paginator = PageNumberPagination()
    paginator.page_size = 20
    filter_backends = [DjangoFilterBackend,SearchFilter,OrderingFilter]
    ordering_fields = ['id']
    search_fields = ['name',]

    def get_queryset(self):
        queryset=Countries.objects.all()
        return queryset

    def list(self,request):
        users=get_users()
        coun=self.filter_queryset(self.get_queryset())
        # coun=users.values("country__name",).annotate(count=Count("country")).order_by("-count")
        country = coun.values("name",).annotate(count=Count('aiuser_country',filter=Q(aiuser_country__in=users)))
        queryset=country.filter(Q(count__gte=0)).order_by("-count")
        pagin=self.paginator.paginate_queryset(queryset,request,view=self)
        response=self.get_paginated_response(pagin)
        return response
    
from ai_staff.models import Languages
from ai_workspace.models import Job,Task
from ai_workspace.models import Project

class language_listview(viewsets.ModelViewSet):
    permission_classes = [IsBiUser]
    paginator = PageNumberPagination()
    paginator.page_size = 20
    filter_backends = [DjangoFilterBackend,SearchFilter,OrderingFilter]
    ordering_fields = ['id']
    search_fields = ['language',]

    def get_queryset(self):
        queryset=Languages.objects.all()
        return queryset

    def list(self,request):
        users=get_users()
        lang=self.filter_queryset(self.get_queryset())
        pro=Project.objects.filter(ai_user__in=users)
        lang_list = lang.values("language",).annotate(count=Count('target_language__job_tasks_set',filter=Q(target_language__project__in=pro)))
        lang_count=lang_list.filter(Q(count__gte=0)).order_by("-count")
        # task=Task.objects.filter(job__target_language__in=lang)
        # lang_count=task.values("job__target_language","job__target_language__language").annotate(count=Count("id")).order_by("-count")
        pagin=self.paginator.paginate_queryset(lang_count,request,view=self)
        response=self.get_paginated_response(pagin)
        return response
    
import django_filters  

class AiDateFilter(django_filters.FilterSet):
 
    date_joined = django_filters.DateTimeFilter()
    # month_name = django_filters.CharFilter(method='filter_by_month_name')
    class Meta:
        model = AiUser
        fields = {"date_joined": ['exact', 'lt', 'lte', 'gt', 'gte']}

    # def filter_by_month_name(self, queryset, name, value):
    #     # Filter the queryset based on the month name
    #     month_number = timezone.datetime.strptime(value, '%B').month
    #     queryset = queryset.filter(date_joined__month=month_number)
    #     return queryset

class AiUserListview(viewsets.ModelViewSet):
    queryset=AiUser.objects.all()
    permission_classes = [IsBiUser]
    serializer_class = AiUserSerializer
    filter_backends = [DjangoFilterBackend,SearchFilter,OrderingFilter]
    ordering_fields = ['id',"date_joined","is_vendor"]
    search_fields = ['country__name','fullname',"id"]
    ordering = ('-date_joined')
    filterset_class = AiDateFilter
    paginator = PageNumberPagination()
    paginator.page_size = 20

    def get_queryset(self,days):
        queryset=get_users()
        if days:
            date = timezone.now() - timezone.timedelta(days=int(days))
            queryset = queryset.filter(date_joined__gte=date)
            return queryset
        else:
            return queryset
        

    def list(self,request):
        days=request.GET.get("days",None)
        users= self.filter_queryset(self.get_queryset(days))
        pagin=self.paginator.paginate_queryset(users,request,view=self)
        ser=AiUserSerializer(pagin,many=True)
        response=self.get_paginated_response(ser.data)
        return response
    
class VendorListview(viewsets.ModelViewSet):
    queryset=AiUser.objects.all()
    permission_classes = [IsBiUser]
    serializer_class = AiUserSerializer
    filter_backends = [DjangoFilterBackend,SearchFilter,OrderingFilter]
    ordering_fields = ['id',"date_joined"]
    search_fields = ['country__name','fullname',"id"]
    ordering = ('-date_joined')
    filterset_class = AiDateFilter
    paginator = PageNumberPagination()
    paginator.page_size = 20

    def get_queryset(self,days):
        queryset=get_users(is_vendor=True)
        print(queryset)
        if days:
            date= timezone.now() - timezone.timedelta(days=int(days))
            queryset = queryset.filter(date_joined__gte=date)
            return queryset
        else:
            return queryset
    
    def list(self,request):
        days=request.GET.get("days",None)
        users= self.filter_queryset(self.get_queryset(days))
        pagin=self.paginator.paginate_queryset(users,request,view=self)
        ser=AiUserSerializer(pagin,many=True)
        response=self.get_paginated_response(ser.data)
        return response


from ai_bi.serializers import BiUserSerializer
from django.http import Http404
from ai_bi.models import BiUser
from django.contrib.auth.hashers import make_password
from allauth.account.models import EmailAddress
from django.db import IntegrityError,transaction
from ai_bi.forms import bi_user_invite_mail


def create_user(name,email,country,password):
    hashed = make_password(password)
    print("random pass",password)
    try:
        user = AiUser.objects.create(fullname =name,email=email,country_id=country,password=hashed)
        UserAttribute.objects.create(user=user)
        # BiUser.objects.create(bi_user=user,bi_role=1)
        EmailAddress.objects.create(email = email, verified = True, primary = True, user = user)
        return {"email":email,"user":user,"password":password}
    except IntegrityError as e:
        print("Intergrity error",str(e))
        return None
    


class BiuserManagement(viewsets.ModelViewSet):
    permission_classes = [IsBiAdmin]
    serializer_class = BiUserSerializer
    filter_backends = [DjangoFilterBackend,SearchFilter,OrderingFilter]
    ordering_fields = ['id']
    search_fields = ['bi_user__fullname',"id"]
    ordering = ('-id')
    paginator = PageNumberPagination()
    paginator.page_size = 20

    def get_queryset(self):
        queryset=BiUser.objects.all()
        return queryset
    
    def get_object(self):
        pk = self.kwargs.get("pk", 0)
        print(pk)
        try:
            return BiUser.objects.get(pk=pk)
        except BiUser.DoesNotExist:
            raise Http404
  
    def list(self,request):
        users= self.filter_queryset(self.get_queryset().filter(~Q(bi_user=request.user)))
        pagin=self.paginator.paginate_queryset(users,request,view=self)
        ser=BiUserSerializer(pagin,many=True)
        response=self.get_paginated_response(ser.data)
        return response

    def create(self,request):
        name=request.POST.get("name",None)
        country=request.POST.get("country",101)
        email=request.POST.get("email",None)
        password=request.POST.get("password",None)
        role=request.POST.get("role","TECHNICAL")
        with transaction.atomic():
            try:
                user=create_user(name,email,country,password)
                if user !=None:
                    user_data={"bi_user":user["user"].id,"bi_role":role}
                    serializer=BiUserSerializer(data=user_data,many=False)
                    if serializer.is_valid():
                        serializer.save()
                        bi_user_invite_mail(user["email"], user["user"],user["password"])
                        return Response(serializer.data,status=200)
                    return Response( serializer.errors)
                else:
                    return Response( {"msg":"Email already exists"},status=400)
            except IntegrityError as e:
                print("Intergrity error",str(e))
                return Response(status=400)

    def retrieve(self, request, pk):
        user=self.get_object()
        print(user)
        userser=BiUserSerializer(user,many=False)
        return Response(userser.data,status=200)
    
    def update(self, request, pk):
        instance = self.get_object()
        serializer = BiUserSerializer(instance, data={**request.POST.dict()},partial=True)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data)
        return Response( serializer.errors)
    
    def destroy(self, request,pk):
        obj=self.get_object()
        obj=obj.bi_user
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
import logging

logger = logging.getLogger(__name__)
from ai_bi.reports import AilaysaReport
from djstripe.models import Subscription,Charge,Customer

class SubscriptionDateFilter(django_filters.FilterSet):
    created = django_filters.DateTimeFilter()
    # month_name = django_filters.CharFilter(method='filter_by_month_name')
    class Meta:
        model = Subscription
        fields = {"created": ['exact', 'lt', 'lte', 'gt', 'gte']}


class SubscriptionListView(viewsets.ModelViewSet):
    permission_classes=[IsBiAdmin]
    serializer_class = DjStripeUserSerializer
    filter_backends = [DjangoFilterBackend,SearchFilter,OrderingFilter]
    ordering_fields = ['id',"customer__email","livemode","created","plan__product__name","customer__id","customer__subscriber","customer__currency","status"]
    search_fields = ["customer__email","plan__product__name","id","customer__id","customer__currency","status"]
    filterset_fields = ["plan__product__name","status","customer__currency",'id',"customer__subscriber","customer__id","livemode"]
    ordering = ("-created")
    # filterset_class = SubscriptionDateFilter
    paginator = PageNumberPagination()
    paginator.page_size = 20
    
    def get_queryset(self,days):
        queryset=get_users()
        queryset=Subscription.objects.filter(Q(customer__subscriber__in=queryset)&Q(status__in=['trialing','active','past_due']))
        if days:
            date= timezone.now() - timezone.timedelta(days=int(days))
            queryset = queryset.filter(created_gte=date)
            return queryset
        else:
            return queryset
        
    def list(self,request):
        days=request.GET.get("days",None)
        queryset=self.filter_queryset(self.get_queryset(days))
        pagin=self.paginator.paginate_queryset(queryset,request,view=self)
        serializer=DjStripeUserSerializer(pagin,many=True)
        response=self.get_paginated_response(serializer.data)
        return response   



def get_paid_user(user,paid=False,):
    if paid:
        queryset=Charge.objects.filter(Q(customer__subscriber__in=user)&Q(status="succeeded"))
    else:
        queryset=Charge.objects.filter(Q(customer__subscriber__in=user))

    return queryset

class PaidUserView(viewsets.ModelViewSet):
    permission_classes=[IsBiAdmin]
    paginator=PageNumberPagination()
    serializer_class=ChargeSerialiizer
    paginator.page_size=20
    filter_backends = [DjangoFilterBackend,SearchFilter,OrderingFilter]
    # ordering_fields = []]
    search_fields = ["customer__email"]
    # filterset_fields = []
    # ordering = ()

    def get_queryset(self,days,paid):
        user=get_users()
        # customer=Customer.objects.filter(Q(subscriber__in=queryset))
        queryset=get_paid_user(user,paid)
        if days:
            date= timezone.now() - timezone.timedelta(days=int(days))
            queryset = queryset.filter(date_joined__gte=date)
            return queryset
        else:
            return queryset
        
    def list(self,request):
        days=request.GET.get("days",None)
        paid=request.GET.get("paid",False)
        paid_user=self.filter_queryset(self.get_queryset(days,paid))
        pagin=self.paginator.paginate_queryset(paid_user,request,view=self)
        serializer=ChargeSerialiizer(pagin,many=True)
        response=self.get_paginated_response(serializer.data)
        return response  








