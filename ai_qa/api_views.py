from django.http import JsonResponse
from rest_framework.response import Response
import requests, functools, string
import regex as re
from rest_framework.decorators import api_view, parser_classes
from .models import Forbidden,ForbiddenWords,Untranslatable,UntranslatableWords
from .serializers import ForbiddenSerializer, UntranslatableSerializer#, LetterCaseSerializer
from rest_framework.viewsets import ModelViewSet
from ai_workspace_okapi.models import Document
from nltk import word_tokenize
from nltk.util import ngrams
from nltk.corpus import stopwords
from rest_framework.views import APIView
from rest_framework import viewsets, status
from ai_workspace.models import Job
from django.db.models import Q
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view,permission_classes
from ai_workspace_okapi.utils import download_file
from ai_auth.tasks import update_untranslatable_words,update_forbidden_words

#from host_details.host_details import doclang

def Letters_Numbers(user_input):
    data=[]
    out=re.finditer(r'([0-9]+\.?\-?\_?[0-9]*?[\p{Ll}\p{Lu}]+)|([\p{Ll}\p{Lu}]+[-_]*\d+)',user_input,re.MULTILINE)
    for i in out:
        data.append(i.group(0))
    print(data)
    return data

def UppercaseLatinWords(user_input):
    data=[]
    datanew=user_input.split()
    for i in datanew:
        if i.isupper():
            data.append(i)
    print(data)
    return data

def MixedcaseLatinWords(user_input):
    data=[]
    out=re.finditer(r'([\p{Lu}|\p{Ll}]+\p{Lu}\p{Ll}+)|([\p{Lu}|\p{Ll}]+\p{Ll}\p{Lu}+)',user_input,re.MULTILINE)
    for i in out:
        data.append(i.group(0))
    return data

# def findwords(wordlist):
#     data1=[]
#     for word in wordlist:
#         if Untranslatables.objects.filter(untranslatables=word):
#             data1.append(word)
#     return data1
#
# def Default_Untranslatables_list(source):
#     punctuation='''!"#$%&'``()*+,-./:;<=>?@[\]^`{|}~_'''
#     text_tokens = word_tokenize(source)
#     stop_words=stopwords.words('english')
#     tokens_new = [word for word in text_tokens if word not in punctuation and word not in stop_words]
#     # print("Tokens--->",tokens_new)
#     unigram=ngrams(tokens_new,1)
#     # print(unigram)
#     single_words=list(" ".join(i) for i in unigram)
#     # print(single_words)
#     bigrams = ngrams(tokens_new,2)
#     double_words=list(" ".join(i) for i in bigrams)
#     # print(double_words)
#     trigrams = ngrams(tokens_new,3)
#     triple_words=list(" ".join(i) for i in trigrams)
#     # print(triple_words)
#     fourgrams = ngrams(tokens_new,4)
#     four_words=list(" ".join(i) for i in fourgrams)
#     # print(four_words)
#     data=findwords(single_words)
#     data.extend(findwords(double_words))
#     data.extend(findwords(triple_words))
#     data.extend(findwords(four_words))
#     # print("********",data)
#     return data


def CapitalLetter(user_input,target):
    data=[]
    print(user_input)
    m1=re.findall(r'^\p{Lu}',user_input)
    m2=re.findall(r'^\p{Lu}',target)
    res=[i.istitle() for i in m1]
    res1=[i.istitle() for i in m2]
    if res==res1:
        data.append("No error")
    else:
        src_word=user_input.split()[0]
        tar_word=target.split()[0]
        data.append("Mismatch in letter case")
        return {'src_word':src_word,'tar_word':tar_word,'message':data}
    return{'message':data}

def Temperature_and_degree_signs(user_input,target):
    src=[]
    tar=[]
    message=[]
    degree=re.compile(r"(\d*\s*\°[^CÇĆĈĊČF]\s*)|(\d*\s*\°$)")
    out=degree.finditer(user_input)
    for i in out:
        src.append(i.group(0))
    out1=degree.finditer(target)
    for i in out1:
        tar.append(i.group(0))
    print(src,tar)
    if src==[] and tar==[]:
        return {'source':src, 'target':tar , 'ErrorNote':message}
    # This needs to be checked. As degree sign can also be used for angles
    message.append("Missing C(Celsius) or F(Fahrenheit) after degree sign")
    return {'source':src, 'target':tar , 'ErrorNote':message}


def find_userlist(wordlist,userlist):
    data1=[]
    for word in wordlist:
        if word in userlist:
            data1.append(word)
    return data1


# def User_Untranslatables_list(source,doc_id):
#     try:
#         data=[]
#         user_file = Untranslatable.objects.filter(doc_id=doc_id).last().file
#         userlist = user_file.readlines()
#         j = 0
#         for j in range(len(userlist)):
#             userlist[j] = str(userlist[j].strip(), 'utf-8')
#         punctuation='''!"#$%&'``()*+,-./:;<=>?@[\]^`{|}~_'''
#         text_tokens = word_tokenize(source)
#         stop_words=stopwords.words('english')
#         tokens_new = [word for word in text_tokens if word not in punctuation and word not in stop_words]
        # unigram=ngrams(tokens_new,1)
        # single_words=list(" ".join(i) for i in unigram)
        # bigrams = ngrams(tokens_new,2)
        # double_words=list(" ".join(i) for i in bigrams)
        # trigrams = ngrams(tokens_new,3)
        # triple_words=list(" ".join(i) for i in trigrams)
        # fourgrams = ngrams(tokens_new,4)
        # four_words=list(" ".join(i) for i in fourgrams)
        # data=find_userlist(single_words,userlist)
        # data.extend(find_userlist(double_words,userlist))
        # data.extend(find_userlist(triple_words,userlist))
        # data.extend(find_userlist(four_words,userlist))
        # return data
#     except:
#         return None

def Uppercase_After_Lowercase(user_input,target):
    data=[]
    src=re.findall(r'(\b\p{Ll}+\p{Lu}+\p{L}*\d*)',user_input)
    tar=re.findall(r'(\b\p{Ll}+\p{Lu}+\p{L}*\d*)',target)
    print(src,tar)
    return src,tar

def inconsistent_url(source,target):
    URLRegex = re.compile(r'(https?://(www\.)?(\w+)(\.\w+))|((https?://)?(www\.)(\w+)(\.\w+))')
    src= URLRegex.finditer(source)
    tar= URLRegex.finditer(target)
    src_url_list=[]
    for i in src:
        src_url_list.append(i.group(0))
    tar_url_list=[]
    for i in tar:
        tar_url_list.append(i.group(0))
    tar_missing = []
    src_missing = []
    ErrorNote=[]
    url_out = {'source':[],'target':[],'ErrorNote':[]}
    if len(src_url_list) != len(tar_url_list):
        ErrorNote.append('Number of URL(s) in source or target segment are unequal')
    else:
        for i in tar_url_list:
            if i not in src_url_list:
                tar_missing.append(i)
        for j in src_url_list:
            if j not in tar_url_list:
                src_missing.append(j)
        if src_missing==[] and tar_missing ==[]:
            ErrorNote=ErrorNote
        else:
            ErrorNote.append('URL(s) in source and target segment are different')
    url_out={'source':src_missing,'target':tar_missing,'ErrorNote':ErrorNote}
    if url_out.get('source')==[] and url_out.get('target')==[] and url_out.get('ErrorNote')==[]:
        return None
    else:
        return url_out

def inconsistent_email(source,target):
    EmailRegex = re.compile(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+')
    src_email_list= EmailRegex.findall(source)
    tar_email_list= EmailRegex.findall(target)
    tar_missing = []
    src_missing = []
    ErrorNote=[]
    email_out = {'source':[],'target':[],'ErrorNote':[]}
    if len(src_email_list) != len(tar_email_list):
        ErrorNote.append('Number of email id(s) in source or target segment are unequal')
    else:
        for i in tar_email_list:
            if i not in src_email_list:
                tar_missing.append(i)
        for j in src_email_list:
            if j not in tar_email_list:
                src_missing.append(j)
        if src_missing==[] and tar_missing ==[]:
            ErrorNote=ErrorNote
        else:
            ErrorNote.append('Email id(s) in source and target segment are different')
    email_out={'source':src_missing,'target':tar_missing,'ErrorNote':ErrorNote}
    if email_out.get('source')==[] and email_out.get('target')==[] and email_out.get('ErrorNote')==[]:
        return None
    else:
        return email_out

def is_matched(expr):
    expr = re.sub("[^][}{)(]+", "", expr)
    while expr:
        expr1 = re.sub(r"\(\)|\[\]|\{\}", "", expr)
        if expr1 == expr:
            return not expr1
        expr = expr1
    return True

def is_quote_matched(expr):
    import regex as re
    # sent = re.sub("(?<=[a-z])'(?=[a-z])", "", expr)###############to remove apostrophe
    sent = re.sub("(?<=\p{Ll})'(?=\p{Ll})", "", expr)###############to remove apostrophe
    print("Sent------------->",sent)
    expr = re.sub("[^\'\'\"\"\'''\''']+", "", sent)
    while expr:
        expr1 = re.sub(r"\'\'|\"\"|\'''\'''", "", expr)
        if expr1 == expr:
            return not expr1
        expr = expr1
    return True


##########  PUNC & SPACING  ##########
def punc_space_view(src,tgt):
    #openbracket     = re.compile(r'(\w+|\s)?(\(|\[|\{)(\w+|\s)?[^\]})](\\|\s|\.)')
    #closebracket     = re.compile(r'\([^()]*\)|\[[^][]*]|\{[^{}]*}|(\w+[])}]|[([{]\w+)')
    #space           = re.compile(r'(\s\s+|^(\s\s)|\s$|\s\.)')
    multispace       = re.compile(r'(\s\s+|^(\s\s+)|\s\s+$|\s\.)')
    #punc            = re.compile(r'(\.\.+$)|(\.\.+)')
    punc             = re.compile(r'(\.\.+|\?\?+|\!\!+|\,\,+)[^\.?!,+$]')#re.compile(r'(\.\.+)[^\.+$]')
    endpunc          = re.compile("[" + re.escape(string.punctuation) + "]$")
    #endpunc          = re.compile(r'((\.+|\!+|\?+)(</\d>)?)$')
    quotes           = re.compile(r'(\w+\s(\'|\")\w+(\s|\,))|(\w+(\'|\")\s\w(\s|\,))')
    #quotesmismatch   = re.compile(r'(\'\s?\w+\")|(\"\s?\w+\')')
    #brac1            = re.compile(r'\(\w+[.-/]?\w+?(\}|\])')
    #brac2            = re.compile(r'\{\w+[.-/]?\w+?(\)|\])')
    #brac3            = re.compile(r'\[\w+[.-/]?\w+?(\)|\})')
    list = []
    src_values = []
    tgt_values = []
    for i in range(2):
        seg = "source" if i == 0 else "target"
        content = src if seg == "source" else tgt
        values = src_values if seg == "source" else tgt_values

        if bool(multispace.findall(content)):
            content1 = content.strip()
            if not bool(multispace.findall(content1)):
                list.append("Multiple leading or trailing spaces in {seg} segment".format(seg=seg))
            elif content == content1 and bool(multispace.findall(content1)):
                list.append("Multiple spaces in {seg} segment".format(seg=seg))
            elif bool(multispace.findall(content)) and bool(multispace.findall(content1)):
                list.append("Multiple spaces in {seg} segment".format(seg=seg))
                list.append("Multiple leading or trailing spaces in {seg} segment".format(seg=seg))

        # if bool(multispace.findall(content)):
        #     # Error note needs to be customised
        #     list.append("Multiple spaces or spaces at start / end {seg} segment".format(seg=seg))
        if punc.findall(content):
            list.append("Duplicate punctuations in {seg} segment".format(seg=seg))

        ### BRACKET MISMATCH ##
        if not bool(is_matched(content)):
            list.append("Mismatched bracket(s) in {seg} segment".format(seg=seg))

        if not bool(is_quote_matched(content)):
            list.append("Mismatched quotes in {seg} segment".format(seg=seg))

    if endpunc.findall(src.strip()) !=  endpunc.findall(tgt.strip()):
        list.append("Source and target segments end with different punctuations")


    if list != []:
        punc_out = {}
        punc_out['source'] = src_values
        punc_out['target'] = tgt_values
        punc_out['ErrorNote'] = list
        return punc_out
    else:
        return None



class ForbiddenFileView(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        project_id = request.GET.get("project", None)
        job_id = request.GET.get('job',None)
        if project_id:
            files = Forbidden.objects.filter(project_id=project_id).order_by('id').all()
        else:
            files = Forbidden.objects.filter(job_id=job_id).all()
        serializer = ForbiddenSerializer(files, many=True)
        return Response(serializer.data)

    def create(self, request):
        files = request.FILES.getlist('forbidden_files')
        check = UntranslatableFileView.file_char_validation(files)
        new_files = check.get('valid')
        invalid = check.get('invalid')
        project_id = request.POST.get("project", None)
        job_id = request.POST.get('job',None)
        if job_id:
            obj = Job.objects.get(id=job_id)
            project_id = obj.project.id
        data = [{"project": project_id,"job":job_id, "forbidden_file": file} for file in new_files]
        ser = ForbiddenSerializer(data=data, many=True)
        if ser.is_valid(raise_exception=True):
            ser.save()
            if invalid:data={'Invalid':invalid,'res':ser.data}
            else:data={'Invalid':None,'res':ser.data}
            return Response(data, status=201)

    def update(self, request, pk):
        file_obj = Forbidden.objects.get(id=pk)
        project_id = request.POST.get("project", None)
        job_id = request.POST.get('job',None)
        ser = ForbiddenSerializer(file_obj,data={'job':job_id},partial=True)
        if ser.is_valid(raise_exception=True):
            ser.save()
            update_forbidden_words.apply_async((file_obj.id,),queue='low-priority')
            return Response(ser.data)

    def delete(self, request, pk):
        file_obj = Forbidden.objects.get(id=pk)
        file_obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)



class UntranslatableFileView(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        project_id = request.GET.get("project", None)
        job_id = request.GET.get('job',None)
        if project_id:
            files = Untranslatable.objects.filter(project_id=project_id).order_by('id').all()
        else:
            files = Untranslatable.objects.filter(job_id=job_id).all()
        serializer = UntranslatableSerializer(files, many=True)
        return Response(serializer.data)

    @staticmethod
    def file_char_validation(files):
        invalid_files,valid_files = [],[]
        for file in files:
            count = 0
            contents = file.readlines()
            for j in contents:
                if len(j.split())>4 or len(j)>500:
                    file_name = file.name.split('.')[0]
                    invalid_files.append(file_name+'.txt')
                    count=count+1
                    break
            if count == 0: valid_files.append(file)
        return {'invalid':invalid_files,'valid':valid_files}

    def create(self, request):
        files = request.FILES.getlist('untranslatable_files')
        check = self.file_char_validation(files)
        new_files = check.get('valid')
        invalid = check.get('invalid')
        project_id = request.POST.get("project", None)
        job_id = request.POST.get('job',None)
        if job_id:
            obj = Job.objects.get(id=job_id)
            project_id = obj.project.id
        data = [{"project": project_id,"job":job_id, "untranslatable_file": file} for file in new_files]
        ser = UntranslatableSerializer(data=data, many=True)
        if ser.is_valid(raise_exception=True):
            ser.save()
            if invalid:data={'Invalid':invalid,'res':ser.data}
            else:data={'Invalid':None,'res':ser.data}
            return Response(data, status=201)

    def update(self, request, pk):
        file_obj = Untranslatable.objects.get(id=pk)
        project_id = request.POST.get("project", None)
        job_id = request.POST.get('job',None)
        ser = UntranslatableSerializer(file_obj,data={'job':job_id},partial=True)
        if ser.is_valid(raise_exception=True):
            ser.save()
            update_untranslatable_words.apply_async((file_obj.id,),queue='low-priority')
            return Response(ser.data)


    def delete(self, request, pk):
        file_obj = Untranslatable.objects.get(id=pk)
        file_obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
# class UntranslatableFileUploadViewSet(ModelViewSet):
#     queryset = Untranslatable.objects.all()
#     serializer_class = UntranslatableSerializer
#     parser_classes = (MultiPartParser, FormParser,)
#
# class LetterCaseFileUploadViewSet(ModelViewSet):
#     queryset = LetterCase.objects.all()
#     serializer_class = LetterCaseSerializer
#     parser_classes = (MultiPartParser, FormParser,)


def forbidden_words_view(source, target, doc_id):
    forbidden_out = {}
    punctuation='''!"#$%&'``()*+,-./:;<=>?@[\]^`{|}~_'''
    #stop_words=stopwords.words('english')
    tgt_list = word_tokenize(target)
    search_words=[]
    tokens_new = [word for word in tgt_list if word not in punctuation]# and word not in stop_words]
    unigram=ngrams(tokens_new,1)
    search_words.extend(list(" ".join(i) for i in unigram))
    bigrams = ngrams(tokens_new,2)
    search_words.extend(list(" ".join(i) for i in bigrams))
    trigrams = ngrams(tokens_new,3)
    search_words.extend(list(" ".join(i) for i in trigrams))
    fourgrams = ngrams(tokens_new,4)
    search_words.extend(list(" ".join(i) for i in fourgrams))
    doc = Document.objects.get(id=doc_id)
    query = Q()
    for entry in search_words:
        query = query | Q(words__iexact=entry)
    query_set_1 = ForbiddenWords.objects.filter(job=doc.job)
    if query_set_1:queryset = ForbiddenWords.objects.filter(Q(job=doc.job)|(Q(job=None) & Q(project=doc.job.project))).filter(query).distinct('words')
    else:queryset = queryset = ForbiddenWords.objects.filter(Q(job=None) & Q(project=doc.job.project)).filter(query).distinct('words')
    #queryset = ForbiddenWords.objects.filter(job=doc.job).filter(Q(job=doc.job)|Q(project=doc.job.project)).filter(query).distinct('words')
    if queryset:
        forbidden_words = [i.words for i in queryset]
        forbidden_out['source'] = []
        forbidden_out['target'] = forbidden_words
        forbidden_out['ErrorNote'] = ["Forbidden word(s) in target segment"]
        return forbidden_out
    else:
        return None


def untranslatable_words_view(source, target, doc_id):
    untranslatable_out = {}
    punctuation='''!"#$%&'``()*+,-./:;<=>?@[\]^`{|}~_'''
    #stop_words=stopwords.words('english')
    src_list = word_tokenize(source)
    search_words=[]
    tokens_new = [word for word in src_list if word not in punctuation]# and word not in stop_words]
    unigram=ngrams(tokens_new,1)
    search_words.extend(list(" ".join(i) for i in unigram))
    bigrams = ngrams(tokens_new,2)
    search_words.extend(list(" ".join(i) for i in bigrams))
    trigrams = ngrams(tokens_new,3)
    search_words.extend(list(" ".join(i) for i in trigrams))
    fourgrams = ngrams(tokens_new,4)
    search_words.extend(list(" ".join(i) for i in fourgrams))
    doc = Document.objects.get(id=doc_id)
    query = Q()
    for entry in search_words:
        query = query | Q(words__iexact=entry)
    query_set_1 = UntranslatableWords.objects.filter(job=doc.job)
    if query_set_1:queryset = UntranslatableWords.objects.filter(Q(job=doc.job)|(Q(job=None) & Q(project=doc.job.project))).filter(query).distinct('words')
    else:queryset = UntranslatableWords.objects.filter(Q(job=None) & Q(project=doc.job.project)).filter(query).distinct('words')
    #queryset = UntranslatableWords.objects.filter(job=doc.job).filter(Q(job=doc.job)|Q(project=doc.job.project)).filter(query).distinct('words')
    #queryset = UntranslatableWords.objects.filter(words__in = search_words)
    if queryset:
        untranslatable_words = [i.words for i in queryset]
        untranslatable_out['source'] = untranslatable_words
        untranslatable_out['target'] = []
        untranslatable_out['ErrorNote'] = ["Untranslatable word(s) in source segment"]
        return untranslatable_out
    else:
        return None


###### NUMBERS VIEW  ##########
def stripNum(num):
    num_str = str(num)
    punc = '''!()-[]{};:'"\, <>./?@#$%^&*_~'''
    for ele in num_str:
        if ele in punc:
            num_str = num_str.replace(ele, "")
    return num_str

def numbers_view(source, target):
    URLEmailRegex = re.compile(r'(https?://(www\.)?(\w+)(\.\w+))|((https?://)?(www\.)(\w+)(\.\w+))|[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+')
    source_ = re.sub(URLEmailRegex,'',source)
    target_ = re.sub(URLEmailRegex,'',target)
    #number  = re.compile(r'[^</>][0-9]+[-,./]*[0-9]*[-,./]*[0-9]*[^<>]')
    src_list = re.findall('[0-9]+[-,./]*[0-9]*[-,./]*[0-9]*', source_)
    tar_list = re.findall('[0-9]+[-,./]*[0-9]*[-,./]*[0-9]*', target_)
    num_out = {}
    if src_list==[] and tar_list==[]:
        return None
    elif src_list==[] and tar_list!=[]:
        num_out['source'] = ["No numbers in source"]
        num_out['target'] = tar_list
        num_out['ErrorNote'] = ["Target segment contains number(s); No number(s) found in source segment"]
        return num_out
    elif tar_list==[] and src_list!=[]:
        num_out['source'] = src_list
        num_out['target'] = ['No numbers in target']
        num_out['ErrorNote'] = ["Source segment contains number(s); No number(s) found in target segment"]
        return num_out
    else:
        if len(src_list)!=len(tar_list):
            msg = ["Mismatch in number count between source and target segments"]

        else:
            #if functools.reduce(lambda x, y : x and y, map(lambda p, q: p == q,src_list,tar_list), True):
            if set(stripNum(src_list)) == set(stripNum(tar_list)):
                msg = []
            else:
                msg = ["Number(s) in source and target segments are different"]

        num_out['source'] = []
        num_out['target'] = []
        num_out['ErrorNote'] = msg
        return num_out if msg!=[] else None

# def stripNum(num):
#     num_str = str(num)
#     punc = '''!()-[]{};:'"\, <>./?@#$%^&*_~'''
#     for ele in num_str:
#         if ele in punc:
#             num_str = num_str.replace(ele, "")
#     return num_str

# def numbers_view(source, target):
#     #number = re.findall('[0-9]+', str)
#     number  = re.compile(r'[^</>][0-9]+[-,./]*[0-9]*[-,./]*[0-9]*[^<>]') # Better regex needs to be added
#     src_list = number.findall(source)
#     tar_list = number.findall(target)
#     src_numbers = []
#     tar_numbers = []
#     src_missing = []
#     tar_missing = []
#     num_out = {}
#     if src_list==[] and tar_list==[]:
#         return None
#     elif src_list==[] and tar_list!=[]:
#         num_out['source'] = ["No numbers in source"]
#         num_out['target'] = tar_list
#         num_out['ErrorNote'] = ["Numbers mismatch or missing"]
#         return num_out
#     else:
#         if tar_list:
#             for i in src_list:
#                 src_numbers.append(stripNum(i))
#             for i in tar_list:
#                 tar_numbers.append(stripNum(i))
#
#             for tar in tar_list:
#                 tar_str = stripNum(tar)
#                 if tar_str not in src_numbers:
#                     tar_missing.append(tar)
#             for src in src_list:
#                 src_str = stripNum(src)
#                 if src_str not in tar_numbers:
#                     src_missing.append(src)
#             msg = ["Numbers mismatch or missing"] if len(src_list)==len(tar_list) else ["Numbers mismatch or missing", "Numbers count mismatch"]
#             num_out['source'] = src_missing
#             num_out['target'] = tar_missing
#             num_out['ErrorNote'] = msg
#             if num_out['source']==[] and num_out['target']==[]:
#                 return None
#             else:
#                 return num_out
#         else:
#             num_out['source'] = src_list
#             num_out['target'] = ['No numbers in target']
#             num_out['ErrorNote'] = ["Numbers mismatch or missing"]
#             return num_out


#########  REPEATED WORDS  #######################
def repeated_words_view(source,target):
    src_words = source.split()
    print("SOURCE WORDS--->", src_words)
    tgt_words = target.split()
    i=0
    j=0
    src_repeated = []
    tgt_repeated = []
    output=[]
    for i in range(len(src_words)-1):
        if src_words[i] == src_words[i+1]:
            src_repeated.append(src_words[i])
    # if src_repeated:
    output.append(src_repeated)
    for j in range(len(tgt_words)-1):
        if tgt_words[j] == tgt_words[j+1]:
            tgt_repeated.append(tgt_words[j])
    # if tgt_repeated:
    output.append(tgt_repeated)

    if output != [[],[]]:
        repeat_out = {}
        repeat_out['source'] = output[0]
        repeat_out['target'] = output[1]
        repeat_out['ErrorNote'] = ["Target segment contains repeated words"]
        return repeat_out
    else:
        return None


###### LETTER CASE ########
# def letter_case_view(source,target,doc_id):
#     try:
#         data=[]
#         letter_case_file = LetterCase.objects.filter(doc_id=doc_id).last().file
#         userlist = letter_case_file.readlines()
#         j = 0
#         for j in range(len(userlist)):
#             userlist[j] = str(userlist[j].strip(), 'utf-8')
#         # print(userlist)
#         #wordgen=target.split()
#         punctuation='''!"#$%&'``()*+,-./:;<=>?@[\]^`{|}~_'''
#         text_tokens = word_tokenize(target)
#         stop_words=stopwords.words('english')
#         tokens_new = [word for word in text_tokens if word not in punctuation and word not in stop_words]
#         # print("Tokens_new---->",tokens_new)
#         for i in tokens_new:
#             for j in userlist:
#                 if i.upper()==j.upper():
#                     if i==j:
#                         print("No error",i)
#                     elif i.lower()==j:
#                         # print("Letter case mismatch",i)
#                         data.append(i)
#                     elif i.upper()==j:
#                         # print("Letter case mismatch",i)
#                         data.append(i)
#                     else:
#                         # print("Letter case mismatch",i)
#                         data.append(i)
#                     message=["Letter case mismatch"]
#         print("-----",data)
#         return data,message
#     except:
#         data=None
#         message=[]
#         return data,message

############TAGS#######################
def tags_check(source,target):
    Regex=re.compile(r'</*[0-9]+>')
    src_tags_list=Regex.findall(source)
    tar_tags_list=Regex.findall(target)
    tar_missing = []
    src_missing = []
    tags_out = {}
    for i in tar_tags_list:
        if i not in src_tags_list:
            tar_missing.append(i)
    for j in src_tags_list:
        if j not in tar_tags_list:
            src_missing.append(j)
    tags_out={'source':src_missing,'target':tar_missing,'ErrorNote':['Tag(s) missing in target segment']}
    if tags_out.get('source')==[] and tags_out.get('target')==[]:
        return None
    else:
        return tags_out

def word_check(source,target):
    src_limit = round( ( 0.4 * len(source.split()) ), 2 )
    if len(target.split()) < src_limit:
        return {'source':[],'target':[],"ErrorNote":["Length of translation seems shortened"]}

def character_check(source,target):
    src_limit = round( ( 0.4 * len(source.strip()) ), 2 )
    if len(target.strip()) < src_limit:
        return {'source':[],'target':[],"ErrorNote":["Length of translation seems shortened"]}

def general_check_view(source,target,doc):
    source_1 = source.replace('\xa0', ' ')
    lang_list = ['Chinese (Traditional)', 'Chinese (Simplified)', 'Japanese','Thai', 'Korean', 'Khmer']
    targetLanguage = doc.target_language
    target_1 = remove_tags(target)
    if not target or target.isspace() or not target_1:
        return {'source':[],'target':[],"ErrorNote":["Target segment is empty"]}
    elif source_1.strip()==target.strip():
        return {'source':[],'target':[],"ErrorNote":["Source and target segments are identical"]}
    else:
        if targetLanguage not in lang_list:
            res = word_check(source,target)
            return res
        # else:
        #     res = character_check(source,target)
        #     return res

    # elif len(target.split()) < src_limit:
    #     #if targetLanguage not in lang_list:
    #     return {'source':[],'target':[],"ErrorNote":["Length of translation seems shortened"]}


TAG_RE = re.compile(r'<[^>]+>')

def remove_tags(text):
    return TAG_RE.sub('', text)

######## MAIN FUNCTION  ########

@api_view(['GET','POST',])
@permission_classes([IsAuthenticated])
def QA_Check(request):
    data = []
    output = []
    out = []
    Indian_lang=['Bengali', 'Marathi', 'Telugu', 'Tamil', 'Urdu', 'Gujarati',
                 'Kannada', 'Malayalam', 'Odia', 'Punjabi', 'Assamese', 'Hindi', 'Arabic', 'Urdu', 'Korean']

    source = request.POST.get('source')
    target = request.POST.get('target')
    doc_id = request.POST.get('doc_id')
    doc = Document.objects.get(id=doc_id)
    # sourceLanguage = doc.source_language
    # targetLanguage = doc.target_language
    general_check = general_check_view(source,target,doc)
    if general_check:
        out.append({'General_check':general_check})
        return JsonResponse({'data':out},safe=False)
    # src_limit = round( ( 0.4 * len(source.split()) ), 2 )
    # if not target:
    #     return JsonResponse({"data":"Target segment is empty"},safe=False)
    # elif source.strip()==target.strip():
    #     return JsonResponse({"data":"Source and target segments are identical"},safe=False)
    # elif len(target.split()) < src_limit:
    #     return JsonResponse({"data":"Length of translation length seems shortened"},safe=False)

    ###############Untranslatables######################
    # data_alnum=Letters_Numbers(source)
    # if data_alnum:
    #     output.extend(data_alnum)
    # data_upper=UppercaseLatinWords(source)
    # if data_upper:
    #     [output.append(x) for x in data_upper if x not in output]
    # data_mixed=MixedcaseLatinWords(source)
    # if data_mixed:
    #     [output.append(x) for x in data_mixed if x not in output]
    # data_untranslatable=Default_Untranslatables_list(source)
    # if data_untranslatable:
    #     [output.append(x) for x in data_untranslatable if x not in output]
    # user_untranslatable=User_Untranslatables_list(source,doc_id)
    # if user_untranslatable:
    #     [output.append(x) for x in user_untranslatable if x not in output]
    # if output:
    #     ut = {}
    #     ut['source'] = output
    #     ut['target'] = []
    #     ut['ErrorNote'] = ["Untranslable term(s) present in Source"]
    #     out.append({'Untranslatables':ut})


    ###  FOR UNTRANSLATABLE FILE  ###
    untranslatable_words = untranslatable_words_view(source, target, doc_id)
    if untranslatable_words:
        out.append({'Untranslatables': untranslatable_words })

    ###  FOR FORBIDDEN FILE  ###
    forbidden_words = forbidden_words_view(source, target, doc_id)

    if forbidden_words:
        out.append({'Forbidden_words': forbidden_words })

    #### USER LETTER CASE  ###
    # letter_case,message = letter_case_view(source, target, doc_id)
    # print("^&*^&*^&*",letter_case)
    # out1={'source':[],'target':[],"ErrorNote":[]}
    # if letter_case:
    #     out1['target'].extend(letter_case)
    #     out1['ErrorNote']=message
    # if (sourceLanguage not in Indian_lang) and (targetLanguage not in Indian_lang):
    #     data_capital = CapitalLetter(source,target)
    #     if data_capital.get('src_word'):
    #         out1['source'].append(data_capital.get('src_word'))
    #         out1['target'].append(data_capital.get('tar_word'))
    #         out1['ErrorNote']=data_capital.get('message')
    # if out1.get('ErrorNote')!=[]:
    #     out.append({'LetterCase':out1})

    ############PUNCTUATION AND Brackets######################
    source_ = remove_tags(source)
    target_ = remove_tags(target)
    data_punc = punc_space_view(source_,target_)
    if data_punc:
        out.append({'Punctuation':data_punc})

    ###############MEASUREMENTS#######################
    # data_temp=Temperature_and_degree_signs(source,target)
    # print(data_temp.get('ErrorNote'))
    # if data_temp.get('ErrorNote')!=[]:
    #     out.append({'Measurement_check':data_temp})

    ##########TAGS CHECK##########################
    tags = tags_check(source,target)
    if tags:
        out.append({'Tags':tags})

    ##### FOR NUMBERS  #######
    numbers = numbers_view(source_,target_)
    if numbers:
        out.append({'Numbers':numbers})

    #### REPEATED WORDS ######
    repeated_words = repeated_words_view(source, target)
    if repeated_words:
        out.append({'Repeated_words':repeated_words})

    #####  EMAIL  #####
    email = inconsistent_email(source,target)
    if email:
        out.append({'Email': email})

    #####  URL  ######
    url = inconsistent_url(source,target)
    if url:
        out.append({'URL': url})

    if out:
        return JsonResponse({'data':out},safe=False)
    return JsonResponse({'data':'No errors found'},safe=False)



@api_view(['GET',])
@permission_classes([IsAuthenticated])
def download_forbidden_file(request,id):
    try:
        file = Forbidden.objects.get(id=id).forbidden_file
        return download_file(file.path)
    except:
        return Response({'msg':'Requested file not exists'},status=401)


@api_view(['GET',])
@permission_classes([IsAuthenticated])
def download_untranslatable_file(request,id):
    try:
        file = Untranslatable.objects.get(id=id).untranslatable_file
        return download_file(file.path)
    except:
        return Response({'msg':'Requested file not exists'},status=401)
