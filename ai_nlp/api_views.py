import json

import spacy
from django.http import JsonResponse
from nltk import word_tokenize
from nltk.util import ngrams
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.http import HttpResponse
from ai_nlp.models import PdffileUpload,PdffileChatHistory
import django_filters
from django.http import JsonResponse, Http404, HttpResponse
from django.shortcuts import get_object_or_404
from ai_nlp.utils import load_embedding_vector
from rest_framework.response import Response
from ai_nlp.serializer import(  PdffileUploadSerializer, PdffileChatHistorySerializer,PdffileShowDetailsSerializer)
from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination 
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view,permission_classes
 



@api_view(['POST', ])
def named_entity(request):
    src_lang_code = request.POST.get('src_lang_code')
    target_lang_code = request.POST.get('target_lang_code')
    src_segment = request.POST.get('src_segment')
    if src_lang_code in ["en", "zh"]:
        lang_model = src_lang_code + '_core_web_sm'
    else:
        lang_model = src_lang_code + '_core_news_sm'

    nlp = spacy.load(lang_model)
    doc = nlp(src_segment)
    data = []
    for entity in doc.ents:
        # print(entity.text, entity.label_)
        # words={'text':entity.text,'label':entity.label_,'explanation':spacy.explain(entity.label_)}
        data.append(entity.text)
    return JsonResponse({"src_ner": data}, safe=False)


@api_view(['GET', 'POST'])
def wordapi_synonyms(request):
    words_file = open("wordsapi_sample.json")
    word_synonyms = words_file.read()
    res = json.loads(word_synonyms)

    punctuation = '''!"#$%&'()*+,./:;<=>?@[\]^`{|}~'''
    target_segment = request.POST.get("target_segment")
    words = word_tokenize(target_segment)
    tokens = [word for word in words if word not in punctuation]
    bigrams = ngrams(tokens, 2)
    double_words = list(" ".join(i) for i in bigrams)
    output = []

    def find_synonyms(tokens):
        for token in tokens:
            result = res.get(token.strip(), 0)
            try:
                if ((result != 0) and ("definitions" in result.keys()) and (
                        "synonyms" in result['definitions'][0].keys())):
                    output.append({token: result['definitions'][0]['synonyms']})
                else:
                    continue
            except Exception as e:
                print("Exception ---> ", e)
                continue

    find_synonyms(tokens)
    find_synonyms(double_words)

    return Response({"result": output}, status=status.HTTP_200_OK)


from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
class PdffileUploadViewset(viewsets.ViewSet,PageNumberPagination):
    permission_classes = [IsAuthenticated,]
    filter_backends = [DjangoFilterBackend]
    filterset_fields =['file_name','status']
    search_fields =['file_name','status']
    page_size=20


    def get_object(self, pk):
        try:
            user = self.request.user.team.owner if self.request.user.team else self.request.user
            return PdffileUpload.objects.get(user=user,id=pk)
        except PdffileUpload.DoesNotExist:
            raise Http404

    def get_user(self):
        project_managers = self.request.user.team.get_project_manager if self.request.user.team else []
        user = self.request.user.team.owner if self.request.user.team and self.request.user in project_managers else self.request.user
        #project_managers.append(user)
        print("Pms----------->",project_managers)
        return user,project_managers


    def create(self,request):

        file=request.FILES.get('file',None)
        if not file:
            return Response({'msg':'no file attached'})
        user,pr_managers = self.get_user() 
        data = {'user':user.id,'managers':pr_managers,'file':file}
        serializer = PdffileUploadSerializer(data={**data},context={'request':request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors)
    
    def list(self, request):
        user = request.user.team.owner if request.user.team else request.user
        queryset = PdffileUpload.objects.filter(user=user).order_by("-id")
        queryset = self.filter_queryset(queryset)
        pagin_tc = self.paginate_queryset(queryset, request , view=self)
        serializer = PdffileUploadSerializer(pagin_tc,many=True)
        response = self.get_paginated_response(serializer.data)
        return response
    
    def retrieve(self,request,pk):
        obj =self.get_object(pk)
        serializer = PdffileShowDetailsSerializer(obj)
        return Response(serializer.data)
    
    def filter_queryset(self, queryset):
        filter_backends = (DjangoFilterBackend,filters.SearchFilter,filters.OrderingFilter )
        for backend in list(filter_backends):
            queryset = backend().filter_queryset(self.request, queryset, view=self)
        return queryset

    def destroy(self,request,pk):
        try:
            obj =self.get_object(pk)
            obj.delete()
            return Response({'msg':'deleted successfully'},status=200)
        except:
            return Response({'msg':'deletion unsuccessfull'},status=400)


from ai_auth.api_views import AilaysaPurchasedUnits
from rest_framework import serializers
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def pdf_chat(request):
    # user = request.user
    file_id=request.query_params.get('file_id',None)
    chat_text=request.query_params.get('chat_text',None)
    pdf_file=PdffileUpload.objects.get(id=int(file_id))
    chat_unit_obj = AilaysaPurchasedUnits(user=pdf_file.user)
    unit_chk = chat_unit_obj.get_units(service_name="pdf-chat")
    if chat_text:
        unit_chk['total_units_left'] =90
        if unit_chk['total_units_left']>0: 
            chat_QA_res = load_embedding_vector(instance = pdf_file ,query=chat_text)
            pdf_chat_instance=PdffileChatHistory.objects.create(pdf_file=pdf_file,question=chat_text)
            pdf_chat_instance.answer=chat_QA_res
            pdf_chat_instance.save()
            serializer = PdffileChatHistorySerializer(pdf_chat_instance)
            # total_message_unit_bal = total_message_unit_bal-1 ## credit detection
            # chat_unit_obj.deduct_units(service_name="pdf-chat",to_deduct_units=1)
            return Response(serializer.data)
        else:
            raise serializers.ValidationError({'msg':'Need to buy add-on pack reached question limit'}, code=400) #Insufficient Credits
 
    serializer = PdffileShowDetailsSerializer(pdf_file)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def pdf_chat_remaining_units(request):
    chat_unit_obj = AilaysaPurchasedUnits(user=request.user)
    unit_msg = chat_unit_obj.get_units(service_name="pdf-chat")
    unit_files = chat_unit_obj.get_units(service_name="pdf-chat-files")
    return Response({"total_msgs_left":unit_msg["total_units_left"],"total_files_left":unit_files["total_units_left"]})

############ wiktionary quick lookup ##################
# @api_view(['GET', 'POST',])
# def WiktionaryParse(request):
#     user_input=request.POST.get("term")
#     term_type=request.POST.get("term_type")
#     doc_id=request.POST.get("doc_id")
#     user_input=user_input.strip()
#     user_input=user_input.strip('0123456789')
#     doc = Document.objects.get(id=doc_id)
#     sourceLanguage=doc.source_language
#     targetLanguage=doc.target_language
#     if term_type=="source":
#         src_lang=sourceLanguage
#         tar_lang=targetLanguage
#     elif term_type=="target":
#         src_lang=targetLanguage
#         tar_lang=sourceLanguage
#     parser = WiktionaryParser()
#     parser.set_default_language(src_lang)
#     parser.include_relation('Translations')
#     word = parser.fetch(user_input)
#     if word:
#         if word[0].get('definitions')==[]:
#             word=parser.fetch(user_input.lower())
#     res=[]
#     tar=""
#     for i in word:
#         defin=i.get("definitions")
#         for j,k in enumerate(defin):
#             out=[]
#             pos=k.get("partOfSpeech")
#             text=k.get("text")
#             rel=k.get('relatedWords')
#             # for n in rel:
#             #     if n.get('relationshipType')=='translations':
#             #         for l in n.get('words'):
#             #             if tar_lang in l:
#             #                 tar=l
#             out=[{'pos':pos,'definitions':text,'target':tar}]
#             res.extend(out)
#
#     return JsonResponse({"Output":res},safe=False)
#
#
# def wikipedia_ws(code,codesrc,user_input):
#     S = requests.Session()
#     URL = f"https://{codesrc}.wikipedia.org/w/api.php"
#     PARAMS = {
#         "action": "query",
#         "format": "json",
#         "prop": "langlinks",
#         "llinlanguagecode":codesrc,
#         "titles": user_input,
#         "redirects": 1,
#         "llprop": "url",
#         "lllang": code,
#     }
#     R = S.get(url=URL, params=PARAMS)
#     DATA = R.json()
#     res=DATA["query"]["pages"]
#     srcURL=f"https://{codesrc}.wikipedia.org/wiki/{user_input}"
#     for i in res:
#         lang=DATA["query"]["pages"][i]
#         if 'missing' in lang:
#             return {"source":'',"target":'',"targeturl":'',"srcURL":''}
#     if (lang.get("langlinks"))!=None:
#         for j in lang.get("langlinks"):
#             output=j.get("*")
#             url=j.get("url")
#         return {"source":user_input,"target":output,"targeturl":url,"srcURL":srcURL}
#     else:
#         output=""
#     return {"source":user_input,"target":output,"targeturl":"","srcURL":srcURL}
#
#
#
#
# ########  Workspace WIKI OPTIONS  ##########################
# #WIKIPEDIA
# @api_view(['GET',])
# # @permission_classes((HasToken,))
# def WikipediaWorkspace(request,doc_id):
#     data=request.GET.dict()
#     lang_list = ["zh-Hans","zh-Hant"]
#     user_input=data.get("term")
#     term_type=data.get("term_type","source")
#     user_input=user_input.strip()
#     user_input=user_input.strip('0123456789')
#     doc = Document.objects.get(id=doc_id)
#     src = doc.source_language_code if doc.source_language_code not in lang_list else "zh"
#     tar = doc.target_language_code if doc.target_language_code not in lang_list else "zh"
#     if term_type=="source":
#         codesrc = src
#         code = tar
#     elif term_type=="target":
#         codesrc = tar
#         code = src
#     res=wikipedia_ws(code,codesrc,user_input)
#     return JsonResponse({"out":res}, safe = False,json_dumps_params={'ensure_ascii':False})
#
#
#
# def wiktionary_ws(code,codesrc,user_input):
#     S = requests.Session()
#     URL =f" https://{codesrc}.wiktionary.org/w/api.php?"
#     PARAMS={
#         "action": "query",
#         "format": "json",
#         "prop": "iwlinks",
#         "iwprop": "url",
#         "iwprefix":code,
#         "titles": user_input,
#         "iwlocal":codesrc,
#     }
#     response = S.get(url=URL, params=PARAMS)
#     try:
#         data = response.json()
#     except JSONDecodeError:
#         return {"source":'',"source-url":''}
#     srcURL=f"https://{codesrc}.wiktionary.org/wiki/{user_input}"
#     res=data["query"]["pages"]
#     if "-1" in res:
#         PARAMS.update({'titles':user_input.lower()})
#         data = S.get(url=URL, params=PARAMS).json()
#         srcURL=f"https://{codesrc}.wiktionary.org/wiki/{user_input.lower()}"
#         res =data['query']['pages']
#     for i in res:
#        lang=data["query"]["pages"][i]
#        if 'missing' in lang:
#            return {"source":'',"source-url":''}
#     output=[]
#     out=[]
#     if (lang.get("iwlinks"))!=None:
#          for j in lang.get("iwlinks"):
#                 out=[{'target':j.get("*"),'target-url':j.get("url")}]
#                 output.extend(out)
#          return {"source":user_input,"source-url":srcURL,"targets":output}
#     return {"source":user_input,"source-url":srcURL}
#
# #WIKTIONARY
# @api_view(['GET',])
# # @permission_classes((HasToken,))
# def WiktionaryWorkSpace(request,doc_id):
#     data=request.GET.dict()
#     lang_list = ["zh-Hans","zh-Hant"]
#     user_input=data.get("term")
#     term_type=data.get("term_type")
#     user_input=user_input.strip()
#     user_input=user_input.strip('0123456789')
#     doc = Document.objects.get(id=doc_id)
#     src = doc.source_language_code if doc.source_language_code not in lang_list else "zh"
#     tar = doc.target_language_code if doc.target_language_code not in lang_list else "zh"
#     if term_type=="source":
#         codesrc =src
#         code = tar
#     elif term_type=="target":
#         codesrc = tar
#         code = src
#     res=wiktionary_ws(code,codesrc,user_input)
#     return JsonResponse({"out":res}, safe = False,json_dumps_params={'ensure_ascii':False})
#
#
# ######  USING PY SPELLCHECKER  ######
# @api_view(['GET', 'POST',])
# def spellcheck(request):
#     tar = request.POST.get('target')
#     doc_id = request.POST.get('doc_id')
#     doc = Document.objects.get(id=doc_id)
#     out,res = [],[]
#     try:
#         spellchecker=SpellcheckerLanguages.objects.get(language_id=doc.target_language_id).spellchecker.spellchecker_name
#         if spellchecker=="pyspellchecker":
#             code = doc.target_language_code
#             spell = SpellChecker(code)
#             words=spell.split_words(tar)#list
#             misspelled=spell.unknown(words)#set
#             for word in misspelled:
#                 suggestion=list(spell.candidates(word))
#                 for k in words:
#                     if k==word.capitalize():
#                         out=[{"word":k,"Suggested Words":suggestion}]
#                         break
#                     else:
#                         out=[{"word":word,"Suggested Words":suggestion}]
#                 res.extend(out)
#             return JsonResponse({"result":res},safe=False)
#     except:
#         return JsonResponse({"message":"Spellcheck not available"},safe=False)
