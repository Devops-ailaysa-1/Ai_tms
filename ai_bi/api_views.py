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
from ai_bi.serializers import AiUserSerializer
from ai_bi.permissions import IsBiUser,IsBiAdmin
from rest_framework import response
from rest_framework.decorators import permission_classes


def get_users(is_vendor=False,period=None,test=False):
        if test:
            users= AiUser.objects.filter(~Q(email__icontains='deleted')&~Q(email='AnonymousUser')&~Q(is_staff=True) \
                    &~Q(is_internal_member=True)&Q(is_vendor=is_vendor))
        else:
            users= AiUser.objects.filter(~Q(email__icontains='deleted')&~Q(email='AnonymousUser')&~Q(is_staff=True) \
                    &~Q(is_internal_member=True)&Q(is_vendor=is_vendor)&~Q(email__icontains="+"))
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
    data["total_coutries"] =len(countries)
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
    search_fields = ['country__name',]

    def get_queryset(self):
        queryset=get_users()
        return queryset

    def list(self,request):
        users=self.filter_queryset(self.get_queryset())
        # coun=Countries.objects.all()
        coun=users.values("country__name",).annotate(count=Count("country")).order_by("-count")
        pagin=self.paginator.paginate_queryset(coun,request,view=self)
        response=self.get_paginated_response(pagin)
        return response
    
from ai_staff.models import Languages
from ai_workspace.models import Job,Task

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
        # users=get_users()
        lang=self.filter_queryset(self.get_queryset())
        task=Task.objects.filter(job__target_language__in=lang)
        lang_count=task.values("job__target_language","job__target_language__language").annotate(count=Count("id")).order_by("-count")
        pagin=self.paginator.paginate_queryset(lang_count,request,view=self)
        response=self.get_paginated_response(pagin)
        return response
    
class AiUserListview(viewsets.ModelViewSet):
    # queryset=AiUser.objects.all()
    permission_classes = [IsBiUser]
    serializer_class = AiUserSerializer
    filter_backends = [DjangoFilterBackend,SearchFilter,OrderingFilter]
    ordering_fields = ['id',"date_joined"]
    search_fields = ['country__name','fullname',"id"]
    ordering = ('-date_joined')
    paginator = PageNumberPagination()
    paginator.page_size = 20

    def get_queryset(self):
        queryset=get_users()
        return queryset
  
    def list(self,request):
        users= self.filter_queryset(self.get_queryset())
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
    print("randowm pass",password)
    try:
        user = AiUser.objects.create(fullname =name,email = email,country_id=country,password = hashed)
        UserAttribute.objects.create(user=user)
        # BiUser.objects.create(bi_user=user,bi_role=1)
        EmailAddress.objects.create(email = email, verified = True, primary = True, user = user)
    except IntegrityError as e:
        print("Intergrity error",str(e))
        return None
    return email, user,password


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
        users= self.filter_queryset(self.get_queryset())
        pagin=self.paginator.paginate_queryset(users,request,view=self)
        ser=BiUserSerializer(pagin,many=True)
        response=self.get_paginated_response(ser.data)
        return response

    def create(self,request):
        name=request.POST.get("name",None)
        country=request.POST.get("country",101)
        email=request.POST.get("email",None)
        password=request.POST.get("password",None)
        role=request.POST.get("role",1)
        with transaction.atomic():
            try:
                email, user,password=create_user(name,email,country,password)
                user_data={"bi_user":user.id,"bi_role":role}
                serializer=BiUserSerializer(data=user_data,many=False)
                if serializer.is_valid():
                    serializer.save()
                    bi_user_invite_mail(email, user,password)
                    return Response(serializer.data,status=200)
            except IntegrityError as e:
                print("Intergrity error",str(e))
                return Response(status=400)
        return Response( serializer.errors)

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
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

