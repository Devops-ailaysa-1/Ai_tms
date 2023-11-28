import ai_staff,json
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status,viewsets
from django.shortcuts import get_object_or_404
from django.db.models.functions import Lower
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly,AllowAny
from rest_framework.authentication import SessionAuthentication, BasicAuthentication, TokenAuthentication
from django.http import Http404,JsonResponse
from .models import (ContentTypes, Countries, Currencies, Languages,
                    LanguagesLocale, MtpeEngines, ServiceTypes, StripeTaxId, SubjectFields, SubscriptionPricingPrices,
                    SupportFiles, Timezones,Billingunits,ServiceTypeunits,AilaysaSupportedMtpeEngines,
                    SupportType,SubscriptionPricing,SubscriptionFeatures,CreditsAddons,
                    IndianStates,SupportTopics,JobPositions,Role,MTLanguageSupport,AilaysaSupportedMtpeEngines,
                    ProjectType,ProjectTypeDetail ,PromptCategories,PromptTones,AiCustomize ,FontData,FontFamily,
                    FontLanguage,SocialMediaSize,ImageGeneratorResolution,DesignShape,SuggestionType,Suggestion,
                    FontCatagoryList,DesignerOrientation,FrontMatter,BackMatter,BodyMatter,Levels,Genre)
from .serializer import (ContentTypesSerializer, LanguagesSerializer, LocaleSerializer,
                         MtpeEnginesSerializer, ServiceTypesSerializer,CurrenciesSerializer,
                         CountriesSerializer, StripeTaxIdSerializer, SubjectFieldsSerializer, SubscriptionPricingPageSerializer, SupportFilesSerializer,
                         TimezonesSerializer,BillingunitsSerializer,ServiceTypeUnitsSerializer,
                         SupportTypeSerializer,SubscriptionPricingSerializer,
                         SubscriptionFeatureSerializer,CreditsAddonSerializer,IndianStatesSerializer,
                         SupportTopicSerializer,JobPositionSerializer,TeamRoleSerializer,MTLanguageSupportSerializer,
                         GetLanguagesSerializer,AiSupportedMtpeEnginesSerializer,ProjectTypeSerializer,ProjectTypeDetailSerializer,LanguagesSerializerNew,PromptCategoriesSerializer,
                         PromptTonesSerializer,AiCustomizeSerializer,AiCustomizeGroupingSerializer,FontLanguageSerializer,FontDataSerializer,FontFamilySerializer,
                         SocialMediaSizeSerializer,ImageGeneratorResolutionSerializer,DesignShapeSerializer,DesignerOrientationSerializer,
                         ImageCategoriesSerializer,SuggestionTypeSerializer,SuggestionSerializer,FontCatagoryListSerializer,
                         FrontMatterSerializer,BackMatterSerializer,BodyMatterSerializer,LevelSerializer,GenreSerializer)
from rest_framework import renderers
from django.http import FileResponse
from django.conf import settings
from rest_framework.pagination import PageNumberPagination 
from rest_framework import filters
from django_filters.rest_framework import DjangoFilterBackend

from cacheops import cached

class ServiceTypesView(APIView):
    permission_classes = [IsAuthenticated]
    #authentication_classes = [TokenAuthentication]
    #permission_classes = [IsAuthenticated]
    
    @cached
    def get_queryset(self):
        queryset = ServiceTypes.objects.all()
        return queryset

    def get(self, request, format=None):
        queryset = self.get_queryset()
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
    permission_classes = [AllowAny,]
    #authentication_classes = [TokenAuthentication]
    #permission_classes = [IsAuthenticated]

    @cached
    def get_queryset(self):
        queryset = Countries.objects.all()
        return queryset


    def get(self, request, format=None):
        queryset = self.get_queryset()
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

    @cached
    def get_queryset(self):
        queryset = Currencies.objects.all()
        return queryset

    def get(self, request, format=None):
        queryset = self.get_queryset()
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
    permission_classes = [
        # IsAuthenticated
    ]
    #authentication_classes = [TokenAuthentication]
    #permission_classes = [IsAuthenticated]

    def get_object(self, pk):
        try:
            return SubjectFields.objects.get(pk=pk)
        except SubjectFields.DoesNotExist:
            raise Http404

    @cached
    def get_queryset(self):
        queryset = SubjectFields.objects.all()
        return queryset

    def get(self, request, format=None):
        queryset = self.get_queryset()
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
    permission_classes = [
        # IsAuthenticated
    ]
    #authentication_classes = [TokenAuthentication]
    #permission_classes = [IsAuthenticated]

    def get_object(self, pk):
        try:
            return ContentTypes.objects.get(pk=pk)
        except ContentTypes.DoesNotExist:
            raise Http404

    @cached
    def get_queryset(self):
        queryset = ContentTypes.objects.all().order_by(Lower('name'))
        return queryset

    def get(self, request, format=None):
        queryset = self.get_queryset()
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

    @cached
    def get_queryset(self):
        queryset = MtpeEngines.objects.all()
        return queryset

    def get(self, request, format=None):
        queryset = self.get_queryset()
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
    permission_classes = [AllowAny,]
    #authentication_classes = [TokenAuthentication]
    #permission_classes = [IsAuthenticated]

    def get_object(self, pk):
        try:
            return SupportFiles.objects.get(pk=pk)
        except SupportFiles.DoesNotExist:
            raise Http404


    @cached
    def get_queryset(self):
        queryset = SupportFiles.objects.all()
        return queryset

    def get(self, request, format=None):
        queryset = self.get_queryset()
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


    @cached
    def get_queryset(self):
        queryset = Timezones.objects.all()
        return queryset

    def get(self, request, format=None):
        queryset = self.get_queryset()
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
    permission_classes = [AllowAny,]
    #authentication_classes = [TokenAuthentication]
    #permission_classes = [IsAuthenticated]

    def get_object(self, pk):
        try:
            return Languages.objects.get(pk=pk)
        except Languages.DoesNotExist:
            raise Http404

    @cached
    def get_queryset(self):
        queryset = Languages.objects.all().order_by('language')
        return queryset

    def get(self, request, format=None):
        queryset = self.get_queryset()
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

    @cached
    def get_queryset(self):
        queryset = Billingunits.objects.all()
        return queryset

    def get(self, request, format=None):
        queryset = self.get_queryset()
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


    @cached
    def get_queryset(self):
        queryset = ServiceTypeunits.objects.all()
        return queryset

    def get(self, request, format=None):
        queryset = self.get_queryset()
        serializer = ServiceTypeUnitsSerializer(queryset, many=True)
        return Response(serializer.data)

# class AilaysaSupportedMtpeEnginesView(APIView):
#     permission_classes = [IsAuthenticated]
#
#     def get(self, request, format=None):
#         queryset = AilaysaSupportedMtpeEngines.objects.all().order_by('id')
#         serializer = AiSupportedMtpeEnginesSerializer(queryset, many=True)
#         return Response(serializer.data)

class SupportTypeView(APIView):
    permission_classes = []

    @cached
    def get_queryset(self):
        queryset = SupportType.objects.all()
        return queryset

    def get(self, request, format=None):
        queryset = self.get_queryset()
        serializer = SupportTypeSerializer(queryset, many=True)
        return Response(serializer.data)

for klass in [LanguagesView]:
    klass.permission_classes = [IsAuthenticatedOrReadOnly]


class AilaysaSupportedMtpeEnginesView(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @cached
    def get_queryset(self):
        queryset = AilaysaSupportedMtpeEngines.objects.all().order_by('id')
        return queryset


    def list(self,request):
        queryset = self.get_queryset()
        serializer = AiSupportedMtpeEnginesSerializer(queryset, many=True)
        return Response(serializer.data)



class SubscriptionPricingCreateView(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @cached
    def get_queryset(self):
        queryset = SubscriptionPricing.objects.all()
        return queryset

    def list(self,request):
        queryset = self.get_queryset()
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

    @cached
    def get_queryset(self):
        queryset = SubscriptionFeatures.objects.all()
        return queryset


    def list(self,request):
        queryset = self.get_queryset()
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


class StripeTaxIdView(viewsets.ViewSet):
    permission_classes = [IsAuthenticated,]

    @cached
    def get_queryset(self):
        queryset = StripeTaxId.objects.all()
        return queryset

    def list(self,request):
        queryset = self.get_queryset()
        serializer = StripeTaxIdSerializer(queryset,many=True)
        return Response(serializer.data)


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
@permission_classes([AllowAny])
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

    @cached
    def get_queryset(self):
        queryset = CreditsAddons.objects.all()
        return queryset

    def list(self,request):
        queryset = self.get_queryset()
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

# class AilaysaSupportedMtpeEnginesView(APIView):
#     permission_classes = [IsAuthenticated]
#
#     def get(self, request, format=None):
#         queryset = AilaysaSupportedMtpeEngines.objects.all()
#         serializer = AiSupportedMtpeEnginesSerializer(queryset, many=True)
#         return Response(serializer.data)

class IndianStatesView(viewsets.ViewSet):
    permission_classes = [AllowAny,]

    @cached
    def get_queryset(self):
        queryset = IndianStates.objects.all()
        return queryset

    def list(self,request):
        queryset = self.get_queryset()
        serializer = IndianStatesSerializer(queryset,many=True)
        return Response(serializer.data)


class SupportTopicsView(viewsets.ViewSet):
    permission_classes = [AllowAny,]

    @cached
    def get_queryset(self):
        queryset = SupportTopics.objects.all()
        return queryset


    def list(self,request):
        queryset = self.get_queryset()
        serializer = SupportTopicSerializer(queryset,many=True)
        return Response(serializer.data)

    def create(self,request):
        serializer = SupportTopicSerializer(data={**request.POST.dict()})
        print(serializer.is_valid())
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self,request,pk):
        queryset = SupportTopics.objects.all()
        topic = get_object_or_404(queryset, pk=pk)
        serializer= SupportTopicSerializer(topic,data={**request.POST.dict()},partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors)

    def delete(self,request,pk):
        queryset = SupportTopics.objects.all()
        topic = get_object_or_404(queryset, pk=pk)
        topic.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)




class SuggestionTypeView(viewsets.ViewSet):
    permission_classes = [AllowAny,]

    @cached
    def get_queryset(self):
        queryset = SuggestionType.objects.all()
        return queryset

    def list(self,request):
        queryset = self.get_queryset()
        serializer = SuggestionTypeSerializer(queryset,many=True)
        return Response(serializer.data)

    def create(self,request):
        serializer = SuggestionTypeSerializer(data={**request.POST.dict()})
        print(serializer.is_valid())
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self,request,pk):
        queryset = SuggestionType.objects.all()
        topic = get_object_or_404(queryset, pk=pk)
        serializer= SuggestionTypeSerializer(topic,data={**request.POST.dict()},partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors)

    def delete(self,request,pk):
        queryset = SuggestionType.objects.all()
        suggestion_type = get_object_or_404(queryset, pk=pk)
        suggestion_type.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class SuggestionView(viewsets.ViewSet):
    permission_classes = [AllowAny,]

    @cached
    def get_queryset(self):
        queryset = Suggestion.objects.all()
        return queryset

    def list(self,request):
        queryset = self.get_queryset()
        serializer = SuggestionSerializer(queryset,many=True)
        return Response(serializer.data)

    def create(self,request):
        serializer = SuggestionSerializer(data={**request.POST.dict()})
        print(serializer.is_valid())
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self,request,pk):
        queryset = Suggestion.objects.all()
        topic = get_object_or_404(queryset, pk=pk)
        serializer= SuggestionSerializer(topic,data={**request.POST.dict()},partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors)

    def delete(self,request,pk):
        queryset = Suggestion.objects.all()
        suggestion = get_object_or_404(queryset, pk=pk)
        suggestion.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class JobPositionsView(viewsets.ViewSet):
    permission_classes = [AllowAny,]

    @cached
    def get_queryset(self):
        queryset = JobPositions.objects.all()
        return queryset

    def list(self,request):
        queryset = self.get_queryset()
        serializer = JobPositionSerializer(queryset,many=True)
        return Response(serializer.data)

    def create(self,request):
        serializer = JobPositionSerializer(data={**request.POST.dict()})
        print(serializer.is_valid())
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self,request,pk):
        queryset = JobPositions.objects.all()
        jobname = get_object_or_404(queryset, pk=pk)
        serializer= JobPositionSerializer(jobname,data={**request.POST.dict()},partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors)

    def delete(self,request,pk):
        queryset = JobPositions.objects.all()
        jobname = get_object_or_404(queryset, pk=pk)
        jobname.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class TeamRoleView(viewsets.ViewSet):
    permission_classes = [AllowAny,]


    @cached
    def get_queryset(self):
        queryset = Role.objects.all()
        return queryset

    def list(self,request):
        queryset = self.get_queryset()
        serializer = TeamRoleSerializer(queryset,many=True)
        return Response(serializer.data)

    def create(self,request):
        serializer = TeamRoleSerializer(data={**request.POST.dict()})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self,request,pk):
        queryset = Role.objects.all()
        role = get_object_or_404(queryset, pk=pk)
        serializer= TeamRoleSerializer(role,data={**request.POST.dict()},partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors)

    def delete(self,request,pk):
        queryset = Role.objects.all()
        role = get_object_or_404(queryset, pk=pk)
        role.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)



class MTLanguageSupportView(viewsets.ViewSet):
    permission_classes = [AllowAny,]


    @cached
    def get_queryset(self):
        queryset = MTLanguageSupport.objects.all()
        return queryset

    def list(self,request):
        queryset = self.get_queryset()
        serializer = MTLanguageSupportSerializer(queryset,many=True)
        return Response(serializer.data)

class ProjectTypeView(viewsets.ViewSet):
    permission_classes = [AllowAny,]

    @cached
    def get_queryset(self):
        queryset = ProjectType.objects.all()
        return queryset
    
    def list(self,request):
        queryset = self.get_queryset()
        serializer = ProjectTypeSerializer(queryset,many=True)
        return Response(serializer.data)

class ProjectTypeDetailView(viewsets.ViewSet):
    permission_classes = [AllowAny,]

    @cached
    def get_queryset(self):
        queryset = ProjectTypeDetail.objects.all()
        return queryset
    
    def list(self,request):
        queryset = self.get_queryset()
        serializer = ProjectTypeDetailSerializer(queryset,many=True)
        return Response(serializer.data)

class VoiceSupportLanguages(viewsets.ViewSet):
    permission_classes = [AllowAny,]
    def list(self,request):
        sub_category = request.GET.get('sub_category')
        project_type_detail = json.loads(sub_category)
        if project_type_detail == 1:           #speech-to-text
            queryset = MTLanguageSupport.objects.filter(speech_to_text = True)
            serializer = GetLanguagesSerializer(queryset,many=True)
            return Response({'source_lang_list':serializer.data})
        if project_type_detail == 2:           #text-to-speech
            queryset = MTLanguageSupport.objects.filter(text_to_speech = True)
            serializer = GetLanguagesSerializer(queryset,many=True)
            return Response({'target_lang_list':serializer.data})
        if project_type_detail == 3:           #speech-to-speech
            queryset = MTLanguageSupport.objects.filter(speech_to_text = True)
            serializer1 = GetLanguagesSerializer(queryset,many=True)
            queryset2 = MTLanguageSupport.objects.filter(text_to_speech = True)
            serializer2 = GetLanguagesSerializer(queryset2,many=True)
            return Response({'source_lang_list':serializer1.data,'target_lang_list':serializer2.data})
        return Response({"msg":"something went wrong"})




@api_view(['GET',])
def get_languages(request):
    queryset = Languages.objects.all().order_by('language')
    serializer = LanguagesSerializerNew(queryset, many=True)
    return Response(serializer.data)



@api_view(['GET',])
def vendor_language_pair_currency(request):
    queryset = Currencies.objects.filter(id__in = [48,45,63,144])
    serializer = CurrenciesSerializer(queryset, many=True)
    return Response(serializer.data)


class FileExtensionImage(APIView):
    permission_classes = [AllowAny,]
    renderer_classes = [renderers.JSONRenderer]

    """
    Get the image for the specific extension
    """
    def get(self, request, extension):
        image_formats = ('JPEG', 'PNG', 'GIF', 'TIFF','BMP')
        music_formats = ('AAC', 'MP3', 'WAV', 'WMA', 'DTS', 'AIFF', 'ASF', 'FLAC', 'ADPCM', 'DSD', 'LPCM', 'OGG')
        excel_formats = ('xlsx', 'xlsm', 'xlsb', 'xltx', 'xltm', 'xls', 'xlt', 'xlam', 'xla', 'xlw', 'xlr', 'csv')
        video_formats = ('MP4', 'MOV', 'WMV', 'AVI', 'MKV')
        word_formats = ('doc', 'docm', 'docx', 'dot', 'dotx')
        presentation_formats = ('ppt', 'pptm', 'pptx')
        if extension.upper() in image_formats:
            extension = 'image'
        elif extension.upper() in music_formats:
            extension = 'audio'
        elif extension.lower() in excel_formats:
            extension = 'csv'
        elif extension.upper() in video_formats:
            extension = 'video'
        elif extension.lower() in word_formats:
            extension = 'docx'
        elif extension.lower() in presentation_formats:
            extension = 'pptx'
        try:
            img = open(f'{settings.MEDIA_ROOT}/file_extension_images/' + extension + '.svg', 'rb')
        except OSError:
            try:
                img = open(f'{settings.MEDIA_ROOT}/file_extension_images/default.svg', 'rb')
            except OSError:
                response = {'error': 'extension not found'}
                response_code = 422
                return Response(response, response_code)
        response = FileResponse(img)
        return response
    


class PromptCategoriesViewset(viewsets.ViewSet):
    # permission_classes = [AllowAny,]

    @cached
    def get_queryset(self):
        queryset = PromptCategories.objects.all().exclude(id__in = [9,11]) 
        return queryset


    def list(self,request):
        query_set = self.get_queryset()
        serializer = PromptCategoriesSerializer(query_set,many=True)
        return Response(serializer.data)  

class NewsCategoriesViewset(viewsets.ViewSet):
    # permission_classes = [AllowAny,]

    @cached
    def get_queryset(self):
        queryset = PromptCategories.objects.filter(category__icontains="News")
        return queryset


    def list(self,request):
        query_set = self.get_queryset()
        serializer = PromptCategoriesSerializer(query_set,many=True)
        return Response(serializer.data)  

    
class PromptTonesViewset(viewsets.ViewSet):
    # permission_classes = [AllowAny,]

    @cached
    def get_queryset(self):
        queryset = PromptTones.objects.all()
        return queryset

    def list(self,request):
        query_set = self.get_queryset()
        serializer = PromptTonesSerializer(query_set,many=True)
        return Response(serializer.data)  


class AiCustomizeViewset(viewsets.ViewSet):
    
    @cached
    def get_queryset(self):
        queryset = AiCustomize.objects.all()
        return queryset
    
    def list(self, request):
        query_set = self.get_queryset()
        serializer = AiCustomizeGroupingSerializer(query_set)
        return Response(serializer.data)



# class PromptSubCategoriesViewset(viewsets.ViewSet):
#     # permission_classes = [AllowAny,]
#     def list(self,request,id):
#         query_set = PromptSubCategories.objects.filter(category_id = id)
#         serializer = PromptSubCategoriesSerializer(query_set,many=True)
#         return Response(serializer.data) 

class FontCatagoryListViewset(viewsets.ViewSet):
    def list(self, request):
        queryset = FontCatagoryList.objects.all()
        serializer = FontCatagoryListSerializer(queryset,many=True)
        return Response(serializer.data)
 

 
class FontLanguageViewset(viewsets.ViewSet):
    def list(self, request):
        queryset = FontLanguage.objects.all()
        serializer = FontLanguageSerializer(queryset,many=True)
        return Response(serializer.data)
    
class FontDataViewset(viewsets.ViewSet):
    def list(self, request):
        font_lang = request.query_params.get('font_lang')
        catagory=request.query_params.get('catagory')
        if font_lang:
            queryset = FontLanguage.objects.get(id=font_lang)
            queryset = FontData.objects.filter(font_lang=queryset)
            serializer = FontDataSerializer(queryset,many=True)
            font_data = []
            for i in serializer.data:
                if i['font_family']:
                    font_data.append(i['font_family']['font_family_name'])
            return Response({'font_list':font_data})
        # elif catagory:
        #     fnt_cat=FontCatagoryList.objects.get(id=catagory)
        #     fnt_fam=FontFamily.objects.filter(catagory=fnt_cat)
        #     ids=[]
        #     for i in fnt_fam:
        #         ids.extend(list(i.font_data_family.all().values_list('id',flat=True)))

        #     queryset = FontData.objects.filter(id__in=ids)
        #     serializer = FontDataSerializer(queryset,many=True)
        #     font_data = []
        #     for i in serializer.data:
        #         if i['font_family']:
        #             font_data.append(i['font_family']['font_family_name'])
        #     return Response({'font_list':font_data})
        else:
            queryset = FontData.objects.all()
            serializer = FontDataSerializer(queryset,many=True)
            return Response(serializer.data)
        

class ImageGeneratorResolutionViewset(viewsets.ViewSet):
    def list(self,request):
        queryset=ImageGeneratorResolution.objects.all()
        serializer=ImageGeneratorResolutionSerializer(queryset,many=True)
        return Response(serializer.data)

class DesignShapePagination(PageNumberPagination):
    page_size = 30 
    page_size_query_param = 'page_size'


class DesignShapeViewset(viewsets.ViewSet,PageNumberPagination):
    page_size = 30
    pagination_class = DesignShapePagination
    search_fields =['shape_name']

    def list(self,request):
        queryset = DesignShape.objects.all().order_by("created_at")
        queryset = self.filter_queryset(queryset)
        pagin_tc = self.paginate_queryset(queryset, request , view=self)
        serializer = DesignShapeSerializer(pagin_tc,many=True)
        response = self.get_paginated_response(serializer.data)
        if response.data["next"]:
            response.data["next"] = response.data["next"].replace("http://", "https://")
        if response.data["previous"]:
                response.data["previous"] = response.data["previous"].replace("http://", "https://")
        return response
        
    def update(self,request,pk):
        shape=request.FILES.get('shape')
        queryset = DesignShape.objects.get(id=pk)
        serializer = DesignShapeSerializer(queryset ,data=request.data,partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors,status=400)
    
    def filter_queryset(self, queryset):
        filter_backends = (DjangoFilterBackend,filters.SearchFilter,filters.OrderingFilter )
        for backend in list(filter_backends):
            queryset = backend().filter_queryset(self.request, queryset, view=self)
        return queryset   
    
    def create(self,request):
        shape=request.FILES.get('shape')
        serializer = DesignShapeSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors)
    


class ImageCategoriesViewset(viewsets.ViewSet):
    def create(self,request):
        serializer = ImageCategoriesSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors)




class DesignerOrientationViewset(viewsets.ViewSet):
    # page_size = 30
    # pagination_class = DesignerOrientation
    # search_fields =['shape_name']

    def list(self,request):
        queryset = DesignerOrientation.objects.all().order_by("created_at")
        # queryset = self.filter_queryset(queryset)
        # pagin_tc = self.paginate_queryset(queryset, request , view=self)
        serializer = DesignerOrientationSerializer(queryset,many=True)
        return Response(serializer.data)


class FrontMatterView(viewsets.ViewSet):
    permission_classes = [AllowAny,]

    @cached
    def get_queryset(self):
        queryset = FrontMatter.objects.all().order_by('id')
        return queryset
    
    def list(self,request):
        queryset = self.get_queryset()
        serializer = FrontMatterSerializer(queryset,many=True)
        return Response(serializer.data)


class BackMatterView(viewsets.ViewSet):
    permission_classes = [AllowAny,]

    @cached
    def get_queryset(self):
        queryset = BackMatter.objects.all().order_by('id')
        return queryset
    
    def list(self,request):
        queryset = self.get_queryset()
        serializer = BackMatterSerializer(queryset,many=True)
        return Response(serializer.data)

class BodyMatterView(viewsets.ViewSet):
    permission_classes = [AllowAny,]

    @cached
    def get_queryset(self):
        queryset = BodyMatter.objects.all().order_by('id')
        return queryset
    
    def list(self,request):
        queryset = self.get_queryset()
        serializer = BodyMatterSerializer(queryset,many=True)
        return Response(serializer.data)


class GenreView(viewsets.ViewSet):
    permission_classes = [AllowAny,]

    @cached
    def get_queryset(self):
        queryset = Genre.objects.all().order_by('id')
        return queryset
    
    def list(self,request):
        queryset = self.get_queryset()
        serializer = GenreSerializer(queryset,many=True)
        return Response(serializer.data)


class LevelView(viewsets.ViewSet):
    permission_classes = [AllowAny,]

    @cached
    def get_queryset(self):
        queryset = Levels.objects.all().order_by('id')
        return queryset
    
    def list(self,request):
        queryset = self.get_queryset()
        serializer = LevelSerializer(queryset,many=True)
        return Response(serializer.data)