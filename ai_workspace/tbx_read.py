from django.http import JsonResponse
import requests
import regex as re
from .models import Tbxfiles,Project,Job, TbxFile
from ai_workspace_okapi.models import Document
from ai_staff.models import Languages,LanguagesLocale
from django.shortcuts import get_object_or_404
import xml.etree.ElementTree as ET
from django.http import QueryDict
from rest_framework.decorators import api_view
import nltk
import json
nltk.download('punkt')
from nltk import word_tokenize
from nltk.util import ngrams


def remove_namespace(doc, namespace):
    """Remove namespace in the passed document in place."""
    ns = u'{%s}' % namespace
    nsl = len(ns)
    for elem in doc.iter():
        if elem.tag.startswith(ns):
            elem.tag = elem.tag[nsl:]


def termIdentify(root,t1,ls,datanew,codesrc,code):
    res1=[]
    source=""
    for word in datanew:
        match=0
        target=[]
        out=[]
        for term in root[1][0].iter(t1):
            for term_lang in term.iter(ls):
                    lang = term_lang.get('{http://www.w3.org/XML/1998/namespace}lang')
                    if lang.split('-')[0]==codesrc:
                            for item in term_lang.iter('term'):
                                #print("*****",item.text)
                                if word.strip()==item.text.strip():
                                    match=1
                                    source=item.text
                                    for j in term.iter(ls):
                                        lang = j.get('{http://www.w3.org/XML/1998/namespace}lang')
                                        if lang.split('-')[0]==code:
                                            for t in j.iter('term'):
                                                target.append(t.text)
                                    out=[{'source':source,'target':target}]
                                    res1.extend(out)
            #print(match)
            if match==1:
                break
    return({"res":res1})

def getLanguageName(id):
        job_id=Document.objects.get(id=id).job_id
        src_id=Job.objects.get(id=job_id).source_language_id
        src_name=Languages.objects.get(id=src_id).language
        tar_id=Job.objects.get(id=job_id).target_language_id
        tar_name=Languages.objects.get(id=tar_id).language
        src_lang_code=LanguagesLocale.objects.get(language_locale_name=src_name).locale_code
        tar_lang_code=LanguagesLocale.objects.get(language_locale_name=tar_name).locale_code
        return ({"source_lang":src_name,"target_lang":tar_name,"src_code":src_lang_code,"tar_code":tar_lang_code})


@api_view(['POST',])
def TermSearch(request):
    punctuation = '''!"#$%&'()*+,./:;<=>?@[\]^`{|}~'''
    out1 = []
    data = request.POST.dict()
    user_input = data.get("user_input")
    text_tokens = word_tokenize(user_input)
    tokens_new = [word for word in text_tokens if word not in punctuation]
    unigram = ngrams(tokens_new,1)
    single_words = list(" ".join(i) for i in unigram)
    bigrams = ngrams(tokens_new,2)
    double_words = list(" ".join(i) for i in bigrams)
    doc_id = data.get("doc_id")
    LangName = getLanguageName(doc_id)
    codesrc = LangName.get("src_code")
    code = LangName.get("tar_code")
    # print(codesrc)
    # print(code)
    job_id = Document.objects.get(id=doc_id).job_id
    project_id = Job.objects.get(id=job_id).project_id
    try:
        files = TbxFile.objects.filter(job_id=job_id).all()
    except Exception as e:
        print("ASSIGNED FOR ALL JOBS", e)
        files = TbxFile.objects.filter(project_id=project_id).all()
    # print(files)
    for i in range(len(files)):
        file_id=files[i].id
        print("****",file_id)
        queryset = Tbxfile.objects.all()
        file = get_object_or_404(queryset, pk=file_id)
        # print(file.tbx_files)
        tree = ET.parse(file.tbx_files.path)
        root=tree.getroot()
        remove_namespace(root, u"iso.org/ns/tbx/2016")
        remove_namespace(root, u"urn:iso:std:iso:30042:ed-2")
        remove_namespace(root, u"http://www.tbxinfo.net/ns/min")
        remove_namespace(root, u"http://www.tbxinfo.net/ns/basic")
        if root.tag=="martif":
            t1='termEntry'
            ls='langSet'
        elif root.tag=='tbx':
            t1='conceptEntry'
            ls='langSec'
        result=termIdentify(root,t1,ls,single_words,codesrc,code).get("res")
        result1=termIdentify(root,t1,ls,double_words,codesrc,code).get("res")
        out1.extend(result)
        out1.extend(result1)
    print("^^^^^",out1)
    output=[]
    [output.append(x) for x in out1 if x not in output]
    print("@@@@@@@@@@@@@",output)
    return JsonResponse({"out":output},safe = False,json_dumps_params={'ensure_ascii':False})
