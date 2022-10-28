from django.http import JsonResponse
from rest_framework.response import Response
import requests
import regex as re
from rest_framework.decorators import api_view, parser_classes
# from checkApp.models import (LetterCase,Untranslatable, Untranslatables,
#                                 forbidden_file_model, LetterCase
#                             )
#from .serializers import Forbidden_File_Serializer, UntranslatableSerializer, LetterCaseSerializer
from rest_framework.viewsets import ModelViewSet
from ai_workspace_okapi.models import Document
import nltk
nltk.download('stopwords')
nltk.download('punkt')
from nltk import word_tokenize
from nltk.util import ngrams
from nltk.corpus import stopwords
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
    message.append("Degree sign placed improperly")
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
#         unigram=ngrams(tokens_new,1)
#         single_words=list(" ".join(i) for i in unigram)
#         bigrams = ngrams(tokens_new,2)
#         double_words=list(" ".join(i) for i in bigrams)
#         trigrams = ngrams(tokens_new,3)
#         triple_words=list(" ".join(i) for i in trigrams)
#         fourgrams = ngrams(tokens_new,4)
#         four_words=list(" ".join(i) for i in fourgrams)
#         data=find_userlist(single_words,userlist)
#         data.extend(find_userlist(double_words,userlist))
#         data.extend(find_userlist(triple_words,userlist))
#         data.extend(find_userlist(four_words,userlist))
#         return data
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
        ErrorNote.append('URL count mismatch')
    for i in tar_url_list:
        if i not in src_url_list:
            tar_missing.append(i)
    for j in src_url_list:
        if j not in tar_url_list:
            src_missing.append(j)
    if src_missing==[] and tar_missing ==[]:
        ErrorNote=ErrorNote
    else:
        ErrorNote.append('Inconsistent URL formats')
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
        ErrorNote.append('Mismatch in URL count')
    for i in tar_email_list:
        if i not in src_email_list:
            tar_missing.append(i)
    for j in src_email_list:
        if j not in tar_email_list:
            src_missing.append(j)
    if src_missing==[] and tar_missing ==[]:
        ErrorNote=ErrorNote
    else:
        ErrorNote.append('Inconsistency in URL format')
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
    sent = re.sub("(?<=[a-z])'(?=[a-z])", "", expr)###############to remove apostrophe
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
    multispace       = re.compile(r'(\s{3}+|^(\s{3})|\s{3}$|\s\.)')
    #punc            = re.compile(r'(\.\.+$)|(\.\.+)')
    punc             = re.compile(r'(\.\.+)[^\.+$]')
    endpunc          = re.compile(r'((\.+|\!+|\?+)(</\d>)?)$')
    quotes           = re.compile(r'(\w+\s(\'|\")\w+(\s|\,))|(\w+(\'|\")\s\w(\s|\,))')
    #quotesmismatch   = re.compile(r'(\'\s?\w+\")|(\"\s?\w+\')')
    #brac1            = re.compile(r'\(\w+[.-/]?\w+?(\}|\])')
    #brac2            = re.compile(r'\{\w+[.-/]?\w+?(\)|\])')
    #brac3            = re.compile(r'\[\w+[.-/]?\w+?(\)|\})')
    list = []
    src_values = []
    tgt_values = []
    for i in range(2):
        seg = "Source" if i == 0 else "Target"
        content = src if seg=="Source" else tgt
        values = src_values if seg=="Source" else tgt_values

        # if bool(openbracket.findall(content)):
        #     for i in openbracket.finditer(content):
        #         values.append(i.group(0))
        # if bool(closebracket.findall(content)):
        #     for i in closebracket.finditer(content):
        #         if i.group(1):
        #             values.append(i.group(1))
        # if bool(openbracket.findall(content)) or bool(closebracket.findall(content)):
        #     list.append("{seg} contains one or more unclosed brackets".format(seg=seg))
        if bool(multispace.findall(content)):
            list.append("{seg} segment contains multiple spaces or spaces at start / end".format(seg=seg))
        if punc.findall(content):
            list.append("More than one fullstops found in {seg}".format(seg=seg))

        ### BRACKET MISMATCH ##
        if not bool(is_matched(content)):
            list.append("{seg} contains mismatched bracket(s)".format(seg=seg))
        # if bool(brac1.findall(content)):
        #     for i in brac1.finditer(content):
        #         values.append(i.group(0))
        # if bool(brac2.findall(content)):
        #     for i in brac2.finditer(content):
        #         values.append(i.group(0))
        # if bool(brac3.findall(content)):
        #     for i in brac3.finditer(content):
        #         values.append(i.group(0))
        # if bool(brac1.findall(content)) or bool(brac2.findall(content)) or bool(brac3.findall(content)):
        #     list.append("{seg} contains mismatched bracket(s)".format(seg=seg))
        # if bool(quotes.findall(content)):
        #     list.append("{seg} contains space before or after apostrophe".format(seg=seg))
        # if bool(quotesmismatch.findall(content)):
        #     for i in quotesmismatch.finditer(content):
        #         values.append(i.group(0))
        if not bool(is_quote_matched(content)):
            list.append("Quotes mismatch in {seg}".format(seg=seg))

    if endpunc.findall(src.strip()) !=  endpunc.findall(tgt.strip()):
        list.append("Mismatch in end punctuation")

    # close = closebracket.finditer(src)
    # for i in close:
    #     print("CLOSE BRAC---->", i.group(0))

    if list != []:
        punc_out = {}
        punc_out['source'] = src_values
        punc_out['target'] = tgt_values
        punc_out['ErrorNote'] = list
        return punc_out
    else:
        return None

# class ForbiddenFileUploadViewSet(ModelViewSet):
#     queryset = forbidden_file_model.objects.all()
#     serializer_class = Forbidden_File_Serializer
#     parser_classes = (MultiPartParser, FormParser,)
#
# class UntranslatableFileUploadViewSet(ModelViewSet):
#     queryset = Untranslatable.objects.all()
#     serializer_class = UntranslatableSerializer
#     parser_classes = (MultiPartParser, FormParser,)
#
# class LetterCaseFileUploadViewSet(ModelViewSet):
#     queryset = LetterCase.objects.all()
#     serializer_class = LetterCaseSerializer
#     parser_classes = (MultiPartParser, FormParser,)


# def forbidden_words_view(source, target, doc_id):
#     try:
#         uploadfile = forbidden_file_model.objects.filter(doc_id=doc_id).last().file
#         list = uploadfile.readlines()
#         j = 0
#         for j in range(len(list)):
#             list[j] = str(list[j].strip(), 'utf-8')
#         forbidden_out = {}
#         punctuation='''!"#$%&'``()*+,-./:;<=>?@[\]^`{|}~_'''
#         stop_words=stopwords.words('english')
#         src_list = word_tokenize(source)
#         source_new = [word for word in src_list if word not in punctuation and word not in stop_words]
#         src_forbidden = []
#         for i in source_new:
#             if i in list:
#                 src_forbidden.append(i)
#         tgt_forbidden = []
#         tgt_list = word_tokenize(target)
#         tgt_new = [word for word in tgt_list if word not in punctuation and word not in stop_words]
#         for i in tgt_new:
#             if i in list and (i not in src_forbidden):
#                 tgt_forbidden.append(i)
#         if tgt_forbidden:
#             forbidden_out['source'] = []
#             forbidden_out['target'] = tgt_forbidden
#             forbidden_out['ErrorNote'] = ["Forbidden word(s) are used"]
#             return forbidden_out
#         else:
#             return None
#     except:
#         return None

###### NUMBERS VIEW  ##########
def stripNum(num):
    num_str = str(num)
    punc = '''!()-[]{};:'"\, <>./?@#$%^&*_~'''
    for ele in num_str:
        if ele in punc:
            num_str = num_str.replace(ele, "")
    return num_str

def numbers_view(source, target):
    number  = re.compile(r'[^</>][0-9]+[-,./]*[0-9]*[-,./]*[0-9]*[^<>]') # Better regex needs to be added
    src_list = number.findall(source)
    tar_list = number.findall(target)
    src_numbers = []
    tar_numbers = []
    src_missing = []
    tar_missing = []
    num_out = {}
    if src_list==[] and tar_list==[]:
        return None
    elif src_list==[] and tar_list!=[]:
        num_out['source'] = ["No numbers in source"]
        num_out['target'] = tar_list
        num_out['ErrorNote'] = ["Numbers mismatch or missing"]
        return num_out
    else:
        if tar_list:
            for i in src_list:
                src_numbers.append(stripNum(i))
            for i in tar_list:
                tar_numbers.append(stripNum(i))

            for tar in tar_list:
                tar_str = stripNum(tar)
                if tar_str not in src_numbers:
                    tar_missing.append(tar)
            for src in src_list:
                src_str = stripNum(src)
                if src_str not in tar_numbers:
                    src_missing.append(src)
            msg = ["Numbers mismatch or missing"] if len(src_list)==len(tar_list) else ["Numbers mismatch or missing", "Numbers count mismatch"]
            num_out['source'] = src_missing
            num_out['target'] = tar_missing
            num_out['ErrorNote'] = msg
            if num_out['source']==[] and num_out['target']==[]:
                return None
            else:
                return num_out
        else:
            num_out['source'] = src_list
            num_out['target'] = ['No numbers in target']
            num_out['ErrorNote'] = ["Numbers mismatch or missing"]
            return num_out


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
        repeat_out['ErrorNote'] = ["Repeated words"]
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
    tags_out={'source':src_missing,'target':tar_missing,'ErrorNote':['Inconsistency in tag(s)']}
    if tags_out.get('source')==[] and tags_out.get('target')==[]:
        return None
    else:
        return tags_out

def general_check_view(source,target):
    src_limit = round( ( 0.4 * len(source.split()) ), 2 )
    if not target:
        return {'source':[],'target':[],"ErrorNote":["Target segment is empty"]}
    elif source.strip()==target.strip():
        return {'source':[],'target':[],"ErrorNote":["Source and target segments are identical"]}
    elif len(target.split()) < src_limit:
        return {'source':[],'target':[],"ErrorNote":["Length of translation length seems shortened"]}


TAG_RE = re.compile(r'<[^>]+>')

def remove_tags(text):
    return TAG_RE.sub('', text)

######## MAIN FUNCTION  ########

@api_view(['GET','POST',])
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
    sourceLanguage = doc.source_language
    targetLanguage = doc.target_language
    general_check = general_check_view(source,target)
    if general_check:
        out.append({'General_Check':general_check})
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

    ####  FOR FORBIDDEN FILE  ###
    # forbidden_words = forbidden_words_view(source, target, doc_id)
    # if forbidden_words:
    #     out.append({'forbidden_words': forbidden_words })

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
    data_temp=Temperature_and_degree_signs(source,target)
    print(data_temp.get('ErrorNote'))
    if data_temp.get('ErrorNote')!=[]:
        out.append({'Measurement Check':data_temp})

    ##########TAGS CHECK##########################
    tags = tags_check(source,target)
    if tags:
        out.append({'Tags':tags})

    ##### FOR NUMBERS  #######
    numbers = numbers_view(source,target)
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
