from pickle import FALSE
from django.http import JsonResponse
from rest_framework.response import Response
import requests
import regex as re
from .models import Tbxfiles,Project,Job, TbxFile, TemplateTermsModel, TbxTemplateFiles
from ai_workspace_okapi.models import Document
from ai_staff.models import Languages,LanguagesLocale
from django.shortcuts import get_object_or_404
import xml.etree.ElementTree as ET
from django.http import QueryDict
from rest_framework.decorators import api_view
import nltk
import json
from nltk import word_tokenize
from nltk.util import ngrams
from django.db.models import F, Q
from tablib import Dataset
from django_oso.auth import authorize

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
                                if word.strip().casefold()==item.text.strip().casefold():
                                    match=1
                                    source=item.text
                                    # for j in term.iter(ls):
                                    #     lang = j.get('{http://www.w3.org/XML/1998/namespace}lang')
                                    #     if lang.split('-')[0]==code:
                                    #         for t in j.iter('term'):
                                    #             target.append(t.text)
                                    for j in term.iter('term'):
                                        if j.text != source:
                                            target.append(j.text)
                                    out=[{'source':source,'target':target}]
                                    res1.extend(out)
            #print(match)
            if match==1:
                break
    return({"res":res1})

# def getLanguageName(id):
#         job_id=Document.objects.get(id=id).job_id
#         src_id=Job.objects.get(id=job_id).source_language_id
#         src_name=Languages.objects.get(id=src_id).language
#         tar_id=Job.objects.get(id=job_id).target_language_id
#         tar_name=Languages.objects.get(id=tar_id).language
#         src_lang_code=LanguagesLocale.objects.get(language_locale_name=src_name).locale_code
#         tar_lang_code=LanguagesLocale.objects.get(language_locale_name=tar_name).locale_code
#         return ({"source_lang":src_name,"target_lang":tar_name,"src_code":src_lang_code,"tar_code":tar_lang_code})


@api_view(['POST',])
def TermSearch(request):
    punctuation = '''!"#$%&'()*+,./:;<=>?@[\]^`{|}~'''
    out1 = []
    data = request.POST.dict()
    user_input = data.get("user_input")
    doc_id = data.get("doc_id")
    doc = Document.objects.get(id = doc_id)
    if doc != None:
        authorize(request, resource=doc, actor=request.user, action="read")
    # LangName = getLanguageName(doc_id)
    codesrc = doc.source_language_code
    code = doc.target_language_code

    job_id = doc.job_id
    project_id = doc.job.project_id
    output=[]
    files =  TbxFile.objects.filter(Q(job_id=job_id) | Q(job_id=None) & Q(project_id=project_id)).all()
    if files:
        text_tokens = word_tokenize(user_input)
        tokens_new = [word for word in text_tokens if word not in punctuation]
        unigram = ngrams(tokens_new,1)
        single_words = list(" ".join(i) for i in unigram)
        bigrams = ngrams(tokens_new,2)
        double_words = list(" ".join(i) for i in bigrams)
        trigrams = ngrams(tokens_new,3)
        triple_words=list(" ".join(i) for i in trigrams)
        fourgrams = ngrams(tokens_new,4)
        four_words=list(" ".join(i) for i in fourgrams)
    

        for i in range(len(files)):
            file_id=files[i].id

            queryset = TbxFile.objects.all()
            file = get_object_or_404(queryset, pk=file_id)

            tree = ET.parse(file.tbx_file.path)
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
            result2=termIdentify(root,t1,ls,triple_words,codesrc,code).get("res")
            result3=termIdentify(root,t1,ls,four_words,codesrc,code).get("res")
            out1.extend(result)
            out1.extend(result1)
            out1.extend(result2)
            out1.extend(result3)

        
        [output.append(x) for x in out1 if x not in output]

    return JsonResponse({"out":output},safe = False,json_dumps_params={'ensure_ascii':False})

def is_tbx_template_file_empty(file_id, job_id):
    template_file =TbxTemplateFiles.objects.get(id=file_id).tbx_template_file
    import pandas as pd
    df = pd.read_excel(template_file)
    if 'Source language term' in df.columns and 'Target language term' in df.columns:
        df = df[['Source language term' , 'Target language term']]
        df=df.replace('\\*','',regex=True)
        df=df.replace(r'\n','', regex=True)
        df = df.dropna()
        return df.empty
    else:
        return True

def upload_template_data_to_db(file_id, job_id):
    template_file =TbxTemplateFiles.objects.get(id=file_id).tbx_template_file
    dataset = Dataset()
    if is_tbx_template_file_empty(file_id, job_id):
        return False
    else:
        imported_data = dataset.load(template_file.read(), format='xlsx')
        try:
            for data in imported_data:
                if data[2]:
                    value = TemplateTermsModel(
                            # data[0],          #Blank column
                            data[1],            #Autoincremented in the model
                            sl_term = data[2].strip(),    #SL term column
                            tl_term = data[3].strip()     #TL term column
                    )
                    value.job_id = job_id
                    value.file_id = file_id
                    value.save()
            return True
        except Exception as e:
            print("Exception in uploading terms ----> ", e)
            return False

def user_tbx_write(job_id,project_id):
    try:
        project = Project.objects.get(id = project_id)
        sl_lang = Job.objects.select_related('locale').filter(id=job_id).values('source_language__locale__locale_code')
        ta_lang = Job.objects.select_related('locale').filter(id=job_id).values('target_language__locale__locale_code')
        sl_code = sl_lang[0].get('source_language__locale__locale_code')
        tl_code = ta_lang[0].get('target_language__locale__locale_code')
        objs = TemplateTermsModel.objects.filter(job_id = job_id)
        # objs = UserTerms.objects.filter(user_id=id)
        root = ET.Element("tbx",type='TBX-Core',style='dca',**{"{http://www.w3.org/XML/1998/namespace}lang": sl_code},xmlns="urn:iso:std:iso:30042:ed-2",
                                nsmap={"xml":"http://www.w3.org/XML/1998/namespace"})
        tbxHeader = ET.Element("tbxHeader")
        root.append (tbxHeader)
        Filedesc=ET.SubElement(tbxHeader,"fileDesc")
        TitleStmt=ET.SubElement(Filedesc,"titleStmt")
        Title=ET.SubElement(TitleStmt,"title")
        Title.text=Project.objects.get(id=project_id).project_name
        SourceDesc=ET.SubElement(Filedesc,"sourceDesc")
        Info=ET.SubElement(SourceDesc,"p")
        Info.text="TBX created from " + TemplateTermsModel.objects.filter(job_id=job_id).last().file.filename
        EncodingDesc=ET.SubElement(tbxHeader,"encodingDesc")
        EncodingInfo=ET.SubElement(EncodingDesc,"p",type="XCSURI")
        EncodingInfo.text="TBXXCSV02.xcs"
        Text= ET.Element("text")
        root.append(Text)
        Body=ET.SubElement(Text,"body")
        for i,obj in enumerate(objs):
            i=i+1
            conceptEntry    = ET.SubElement(Body,"conceptEntry",id="c"+str(i))
            langSec         = ET.SubElement(conceptEntry,"langSec",**{"{http://www.w3.org/XML/1998/namespace}lang": sl_code})
            Termsec         = ET.SubElement(langSec,"termSec")
            Term = ET.SubElement(Termsec,"term")
            Term.text = obj.sl_term.strip()
            langSec1 = ET.SubElement(conceptEntry,"langSec",**{"{http://www.w3.org/XML/1998/namespace}lang": tl_code})
            termSec1 = ET.SubElement(langSec1,"termSec")
            Term1 = ET.SubElement(termSec1,"term")
            Term1.text = obj.tl_term.strip()
        out_fileName = TemplateTermsModel.objects.filter(job_id=job_id).last().file.filename[:-5] + ".tbx"
        ET.ElementTree(root).write(out_fileName, encoding="utf-8",xml_declaration=True)
        print("out_fileName type--->", type(out_fileName))
        return out_fileName

    except Exception as e:
        print("Exception1-->", e)
        return Response(data={"Message":"Something wrong in TBX conversion"})
