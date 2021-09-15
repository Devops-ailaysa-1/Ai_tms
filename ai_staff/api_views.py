import ai_staff
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status,viewsets
from django.shortcuts import get_object_or_404
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.authentication import SessionAuthentication, BasicAuthentication, TokenAuthentication
from django.http import Http404,JsonResponse
from .models import (ContentTypes, Countries, Currencies, Languages,
                    LanguagesLocale, MtpeEngines, ServiceTypes, SubjectFields, SubscriptionPricingPrices,
                    SupportFiles, Timezones,Billingunits,ServiceTypeunits,
                    SupportType,SubscriptionPricing,SubscriptionFeatures,CreditsAddons,IndianStates)
from .serializer import (ContentTypesSerializer, LanguagesSerializer, LocaleSerializer,
                         MtpeEnginesSerializer, ServiceTypesSerializer,CurrenciesSerializer,
                         CountriesSerializer, SubjectFieldsSerializer, SubscriptionPricingPageSerializer, SupportFilesSerializer,
                         TimezonesSerializer,BillingunitsSerializer,ServiceTypeUnitsSerializer,
                         SupportTypeSerializer,SubscriptionPricingSerializer,
                         SubscriptionFeatureSerializer,CreditsAddonSerializer)


class ServiceTypesView(APIView):
    permission_classes = [IsAuthenticated]
    #authentication_classes = [TokenAuthentication]
    #permission_classes = [IsAuthenticated]
    def get(self, request, format=None):
        queryset = ServiceTypes.objects.all()
        serializer = ServiceTypesSerializer(queryset, many=True)
        return Response(serializer.data)

    def get_object(self, pk):
        try:
            return ServiceTypes.objects.get(pk=pk)
        except ServiceTypes.DoesNotExist:
            raise Http404

    def post(self, request):
        data = request.data
        data['user'] = self.request.user.id
        serializer = ServiceTypesSerializer(data=data, context={'request':request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)


    def patch(self, request, pk, format=None):
        service_t = self.get_object(pk)
        serializer = ServiceTypesSerializer(service_t,
                                           data=request.data,
                                           partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        service_t = self.get_object(pk)
        service_t.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class CountriesView(APIView):
    #permission_classes = [IsAuthenticated]
    #authentication_classes = [TokenAuthentication]
    #permission_classes = [IsAuthenticated]
    def get(self, request, format=None):
        queryset = Countries.objects.all()
        serializer = CountriesSerializer(queryset, many=True)
        return Response(serializer.data)


    def get_object(self, pk):
        try:
            return Countries.objects.get(pk=pk)
        except Countries.DoesNotExist:
            raise Http404

    def post(self, request):
        data = request.data
        data['user'] = self.request.user.id
        serializer = CountriesSerializer(data=data, context={'request':request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)


    def patch(self, request, pk, format=None):
        countrie = self.get_object(pk)
        serializer = CountriesSerializer(countrie,
                                           data=request.data,
                                           partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        countrie = self.get_object(pk)
        countrie.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)





class CurrenciesView(APIView):
    permission_classes = [IsAuthenticated]
    #authentication_classes = [TokenAuthentication]
    #permission_classes = [IsAuthenticated]

    def get_object(self, pk):
        try:
            return Currencies.objects.get(pk=pk)
        except Currencies.DoesNotExist:
            raise Http404

    def get(self, request, format=None):
        queryset = Currencies.objects.all()
        serializer = CurrenciesSerializer(queryset, many=True)
        return Response(serializer.data)

    def post(self, request):
        data = request.data
        data['user'] = self.request.user.id
        serializer = CurrenciesSerializer(data=data, context={'request':request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)


    def patch(self, request, pk, format=None):
        currency = self.get_object(pk)
        serializer = CurrenciesSerializer(currency,
                                           data=request.data,
                                           partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        currency = self.get_object(pk)
        currency.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)



class SubjectFieldsView(APIView):
    permission_classes = [IsAuthenticated]
    #authentication_classes = [TokenAuthentication]
    #permission_classes = [IsAuthenticated]

    def get_object(self, pk):
        try:
            return SubjectFields.objects.get(pk=pk)
        except SubjectFields.DoesNotExist:
            raise Http404

    def get(self, request, format=None):
        queryset = SubjectFields.objects.all()
        serializer = SubjectFieldsSerializer(queryset, many=True)
        return Response(serializer.data)

    def post(self, request):
        permission_classes = [IsAuthenticated]
        data = request.data
        print(data)
        #data['user'] = self.request.user.id
        #print(">>>>>>>AFTER",data)
        serializer = SubjectFieldsSerializer(data=data, context={'request':request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)


    def patch(self, request, pk, format=None):
        subject = self.get_object(pk)
        serializer = SubjectFieldsSerializer(subject,
                                           data=request.data,
                                           partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        subject = self.get_object(pk)
        subject.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ContentTypesView(APIView):
    permission_classes = [IsAuthenticated]
    #authentication_classes = [TokenAuthentication]
    #permission_classes = [IsAuthenticated]

    def get_object(self, pk):
        try:
            return ContentTypes.objects.get(pk=pk)
        except ContentTypes.DoesNotExist:
            raise Http404

    def get(self, request, format=None):
        queryset = ContentTypes.objects.all()
        serializer = ContentTypesSerializer(queryset, many=True)
        return Response(serializer.data)

    def post(self, request):
        data = request.data
        print(data)
        #data['user'] = self.request.user.id
        #print(">>>>>>>AFTER",data)
        serializer = ContentTypesSerializer(data=data, context={'request':request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)


    def patch(self, request, pk, format=None):
        content = self.get_object(pk)
        serializer = ContentTypesSerializer(content,
                                           data=request.data,
                                           partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        content = self.get_object(pk)
        content.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)



class MtpeEnginesView(APIView):
    permission_classes = [IsAuthenticated]
    #authentication_classes = [TokenAuthentication]
    #permission_classes = [IsAuthenticated]

    def get_object(self, pk):
        try:
            return MtpeEngines.objects.get(pk=pk)
        except MtpeEngines.DoesNotExist:
            raise Http404

    def get(self, request, format=None):
        queryset = MtpeEngines.objects.all()
        serializer = MtpeEnginesSerializer(queryset, many=True)
        return Response(serializer.data)

    def post(self, request):
        data = request.data
        #data['user'] = self.request.user.id
        #print(">>>>>>>AFTER",data)
        serializer = MtpeEnginesSerializer(data=data, context={'request':request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)


    def patch(self, request, pk, format=None):
        engine = self.get_object(pk)
        serializer = MtpeEnginesSerializer(engine,
                                           data=request.data,
                                           partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        engine = self.get_object(pk)
        engine.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)



class SupportFilesView(APIView):
    permission_classes = [IsAuthenticated]
    #authentication_classes = [TokenAuthentication]
    #permission_classes = [IsAuthenticated]

    def get_object(self, pk):
        try:
            return SupportFiles.objects.get(pk=pk)
        except SupportFiles.DoesNotExist:
            raise Http404

    def get(self, request, format=None):
        queryset = SupportFiles.objects.all()
        serializer = SupportFilesSerializer(queryset, many=True)
        return Response(serializer.data)

    def post(self, request):
        data = request.data

        #data['user'] = self.request.user.id
        #print(">>>>>>>AFTER",data)
        serializer = SupportFilesSerializer(data=data, context={'request':request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)


    def patch(self, request, pk, format=None):
        format = self.get_object(pk)
        serializer = SupportFilesSerializer(format,
                                           data=request.data,
                                           partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        format = self.get_object(pk)
        format.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)



class TimezonesView(APIView):
    permission_classes = [IsAuthenticated]
    #authentication_classes = [TokenAuthentication]
    #permission_classes = [IsAuthenticated]

    def get_object(self, pk):
        try:
            return Timezones.objects.get(pk=pk)
        except Timezones.DoesNotExist:
            raise Http404

    def get(self, request, format=None):
        queryset = Timezones.objects.all()
        serializer = TimezonesSerializer(queryset, many=True)
        return Response(serializer.data)

    def post(self, request):
        data = request.data

        #data['user'] = self.request.user.id
        #print(">>>>>>>AFTER",data)
        serializer = TimezonesSerializer(data=data, context={'request':request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)


    def patch(self, request, pk, format=None):
        t_zone = self.get_object(pk)
        serializer = TimezonesSerializer(t_zone, data=request.data,partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        t_zone = self.get_object(pk)
        t_zone.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class LanguagesView(APIView):

    #authentication_classes = [TokenAuthentication]
    #permission_classes = [IsAuthenticated]

    def get_object(self, pk):
        try:
            return Languages.objects.get(pk=pk)
        except Languages.DoesNotExist:
            raise Http404

    def get(self, request, format=None):
        queryset = Languages.objects.all()
        serializer = LanguagesSerializer(queryset, many=True)
        return Response(serializer.data)

    def post(self, request):
        data = request.data
        #data['user'] = self.request.user.id
        #print(">>>>>>>AFTER",data)
        serializer = LanguagesSerializer(data=data, context={'request':request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)


    def patch(self, request, pk, format=None):
        lang = self.get_object(pk)
        serializer = LanguagesSerializer(lang, data=request.data,partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        lang = self.get_object(pk)
        lang.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)



class LanguagesLocaleView(APIView):
    permission_classes = [IsAuthenticated]
    #authentication_classes = [TokenAuthentication]
    #permission_classes = [IsAuthenticated]

    def get_object(self, pk):
        try:
            return LanguagesLocale.objects.get(pk=pk)
        except LanguagesLocale.DoesNotExist:
            raise Http404

    def get(self, request, langid=None ,format=None):
        if langid :
            queryset = LanguagesLocale.objects.filter(language_id=langid)
        else:
            queryset = LanguagesLocale.objects.all()
        serializer = LocaleSerializer(queryset, many=True)
        return Response(serializer.data)

    def post(self, request):
        data = request.data
        #data['user'] = self.request.user.id
        #print(">>>>>>>AFTER",data)
        serializer = LocaleSerializer(data=data, context={'request':request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)


    def patch(self, request, pk, format=None):
        locale = self.get_object(pk)
        serializer = LocaleSerializer(locale, data=request.data,partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        locale = self.get_object(pk)
        locale.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class BillingunitsView(APIView):
    permission_classes = [IsAuthenticated]
    #authentication_classes = [TokenAuthentication]
    #permission_classes = [IsAuthenticated]

    def get_object(self, pk):
        try:
            return Billingunits.objects.get(pk=pk)
        except Billingunits.DoesNotExist:
            raise Http404

    def get(self, request, format=None):
        queryset = Billingunits.objects.all()
        serializer = BillingunitsSerializer(queryset, many=True)
        return Response(serializer.data)

    def post(self, request):
        data = request.data
        #data['user'] = self.request.user.id
        #print(">>>>>>>AFTER",data)
        serializer = BillingunitsSerializer(data=data, context={'request':request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)


    def patch(self, request, pk, format=None):
        unit = self.get_object(pk)
        serializer = BillingunitsSerializer(unit, data=request.data,partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        unit = self.get_object(pk)
        unit.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class ServiceTypeunitsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        queryset = ServiceTypeunits.objects.all()
        serializer = ServiceTypeUnitsSerializer(queryset, many=True)
        return Response(serializer.data)

class SupportTypeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        queryset = SupportType.objects.all()
        serializer = SupportTypeSerializer(queryset, many=True)
        return Response(serializer.data)

for klass in [LanguagesView]:
    klass.permission_classes = [IsAuthenticatedOrReadOnly]


class SubscriptionPricingCreateView(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    def list(self,request):
        queryset = SubscriptionPricing.objects.all()
        serializer = SubscriptionPricingSerializer(queryset,many=True)
        return Response(serializer.data)

    def create(self,request):
        serializer = SubscriptionPricingSerializer(data={**request.POST.dict()})
        print(serializer.is_valid())
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self,request,pk):
        queryset = SubscriptionPricing.objects.all()
        plan = get_object_or_404(queryset, pk=pk)
        serializer= SubscriptionPricingSerializer(plan,data={**request.POST.dict()},partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors)

    def delete(self,request,pk):
        queryset = SubscriptionPricing.objects.all()
        plan = get_object_or_404(queryset, pk=pk)
        plan.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class SubscriptionFeaturesCreateView(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    def list(self,request):
        queryset = SubscriptionFeatures.objects.all()
        serializer = SubscriptionFeatureSerializer(queryset,many=True)
        return Response(serializer.data)

    def create(self,request):
        serializer = SubscriptionFeatureSerializer(data={**request.POST.dict()})
        print(serializer.is_valid())
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self,request,pk):
        queryset = SubscriptionFeatures.objects.all()
        feature = get_object_or_404(queryset, pk=pk)
        serializer= SubscriptionFeatureSerializer(feature,data={**request.POST.dict()},partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors)

    def delete(self,request,pk):
        queryset = SubscriptionFeatures.objects.all()
        plan = get_object_or_404(queryset, pk=pk)
        plan.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET',])
def get_plan_details(request):
    plans = SubscriptionPricing.objects.all()
    out=[]
    for plan in plans:
         result={}
         output=[]
         serializer = SubscriptionPricingSerializer(plan)
         result["subscription"]=serializer.data
         features =  SubscriptionFeatures.objects.filter(subscriptionplan_id=plan.id).all()
         for feature in features:
             serializer2 = SubscriptionFeatureSerializer(feature)
             feature = serializer2.data
             output.append(feature)
         result["features"]=output
         out.append(result)
    return JsonResponse({"plans":out},safe=False)


@api_view(['GET',])
def get_pricing_details(request):
    plans = SubscriptionPricing.objects.all()
    serializer = SubscriptionPricingPageSerializer(plans,many=True)
    return JsonResponse({"plans":serializer.data},safe=False,status=200)

@api_view(['GET',])
def get_addons_details(request):
    addons = CreditsAddons.objects.all()
    serializer = CreditsAddonSerializer(addons,many=True)
    return JsonResponse({"addons":serializer.data},safe=False,status=200)

class CreditsAddonsCreateView(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    def list(self,request):
        queryset = CreditsAddons.objects.all()
        serializer = CreditsAddonSerializer(queryset,many=True)
        return Response(serializer.data)

    def create(self,request):
        serializer = CreditsAddonSerializer(data={**request.POST.dict()})
        print(serializer.is_valid())
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self,request,pk):
        queryset = CreditsAddons.objects.all()
        pack = get_object_or_404(queryset, pk=pk)
        serializer= CreditsAddonSerializer(pack,data={**request.POST.dict()},partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors)

    def delete(self,request,pk):
        queryset = CreditsAddons.objects.all()
        pack = get_object_or_404(queryset, pk=pk)
        pack.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)



class IndianStatesView(viewsets.ViewSet):
    def list(self,request):
        queryset = IndianStates.objects.all()
        serializer = CreditsAddonSerializer(queryset,many=True)
        return Response(serializer.data)