

from rest_framework import  viewsets
from rest_framework.response import Response
from ai_writer.models import FileDetails
from ai_writer.serializer import SpellCheckSerializer, ProductDescriptionSerializer ,FaceBookAdSerializer, FileSerializer ,VerbSerializer
from htmldocx import HtmlToDocx
from docx import Document
import  re ,mimetypes ,os  ,string ,requests ,json
from delta import html
from ai_tms import settings
from django.http import JsonResponse , HttpResponse
from rest_framework.decorators import api_view
import openai
from langdetect import detect_langs
from ai_staff.models import LanguagesLocale 


openai.api_key = settings.OPENAI_APIKEY
NLP_CLOUD_API = settings.NLP_CLOUD_API
END_POINT= settings.END_POINT


num_beams = 10
num_return_sequences = 10
 

temp = [0 , 0.3 , 0.7]
frequency_penalty = [0 , 0.7, 1.7]
presence_penalty = [0 , 0.7 , 1.7] 
max_tokens = int(settings.MAX_TOKEN)
engine= "text-curie-001"

 
class CreateFileView(viewsets.ViewSet):
    def list(self,request):
        file_pk = FileDetails.objects.all()
        query_s = request.query_params.get("user_name")
        print(file_pk)
        query_id = request.query_params.get("id")
        if query_s:
            queryset = file_pk.filter(user_name = query_s).order_by("-updated_at")
        if query_s is None:
            queryset = file_pk.filter(id = query_id)
           
        serializer = FileSerializer(queryset , many = True)
        if  serializer is not None:
            return Response(serializer.data)    
        else:
            return Response(serializer.error)

    def create(self,request):
        print("testing create")
        serializer = FileSerializer(data = {**request.POST.dict()})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors)


    def update(self,request,pk):
 
        file_pk = FileDetails.objects.get(id=pk)
        serializer = FileSerializer(file_pk,data={**request.POST.dict()},partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors)


    def delete(self,request,pk):
        file_pk = FileDetails.objects.get(id=pk)
        file_pk.delete()
        return  Response("item successfully deleted")



########spellcheck and grammar check##############





@api_view(['POST',])
def hunspellcheck(request):
    word = request.POST.get('word')
    lang = request.POST.get('lang')
    data = {}
    data['word'] = word
    data['lang'] = lang
    end_pts = END_POINT +"hunspellcheck/"
    result = requests.post(end_pts , data )
    serialize = SpellCheckSerializer(result.json())
    return JsonResponse(serialize.data)



@api_view(['POST',])
def hunspell_sentence_check_and_grammar_check(request):
    sentence = request.POST.get('sentence')
    lang = request.POST.get('lang')
    data = {}
    data['sentence'] = sentence
    data['lang'] = lang
    end_pts = END_POINT +"hunspell_sentence_check/"
    result = requests.post(end_pts , data )
    return JsonResponse(result.json())



@api_view(['POST',])
def grammar_check_model(request):
    text = request.POST.get('text')
    data = {}
    data['text'] = text
    end_pts = END_POINT +"grammar-checker/"
    result = requests.post(end_pts , data )
    return JsonResponse(result.json())

################################download_docx #######################################





@api_view(['GET',])
def download_docx(request):
    id  = request.query_params.get('id')
    file = FileDetails.objects.get(id = id)
    docx = file.store_quill_data
    docx = eval(docx.replace("true" , "True"))
    document = Document()
    new_parser = HtmlToDocx()
    docx = docx['ops']
    docx = html.render(docx)
    new_parser.add_html_to_document(docx, document)
    document.save(file.file_name+'.docx')
    file_path = file.file_name+'.docx'
    fl = open(file_path, 'rb')
    mime_type, _ = mimetypes.guess_type(file_path)
    response = HttpResponse(fl, content_type=mime_type)
    response['Content-Disposition'] = "attachment; filename=%s" % file.file_name+'.docx'
    os.remove(file.file_name+'.docx')
    return response



@api_view(['GET',])
def docx_save(request):
    id  = request.query_params.get('id')
    file = FileDetails.objects.get(id = id)
    docx = file.store_quill_data
    docx = eval(docx.replace("true" , "True"))
    document = Document()
    new_parser = HtmlToDocx()
    docx = docx['ops']
    docx = html.render(docx)
    new_parser.add_html_to_document(docx, document)
    document.save(file.file_name+'.docx')
    return JsonResponse({"save":"True"})


###########syn-verb################


@api_view(['POST',])
def synonmys_lookup(request):
    if request.method == "POST":
        data = {}
        txt = request.POST["text"]
        end_pts = END_POINT +"synonyms/"
        data['text'] = txt
        result = requests.post(end_pts , data )
        serialize = VerbSerializer(result.json())
        return JsonResponse(serialize.data)


#######paraphrasing######


@api_view(['POST',])
def paraphrasing(request):
    text = {}
    sentence = request.POST.get('sentence')
    text['sentence'] = sentence
    end_pts = END_POINT +"paraphrase/"
    data = requests.post(end_pts , text)
    return JsonResponse(data.json())



###########nlpcloud and openai ##########
def generate_prediction_openai(prompt , keywords , describe_type):
    choices = {}
    for i , j in enumerate(zip(temp , frequency_penalty ,presence_penalty)):
        choices[i] = text_generator(prompt ,"\n"+describe_type+": " + keywords , j[0] ,j[1] ,j[2],max_tokens )
        choices[i] = choices[i].replace("\n" , "")

    return choices


def text_generator(prompt , keywords , temperature ,frequency_penalty ,presence_penalty , max_tokens ):
    response = openai.Completion.create(
      engine=engine ,
      prompt=prompt+keywords,
      temperature=temperature,
      max_tokens=max_tokens,
      top_p=1.0,
      frequency_penalty=frequency_penalty,
      presence_penalty=presence_penalty
    )
    return  response['choices'][0]['text']




@api_view(['POST',])
def text_creater(request):

    CATEGORIES = request.POST.get('category')
    choices = {}
     
    if CATEGORIES == "Product-Description":
        prompt = request.POST.get('product_name')
        product_info = request.POST.get('product_info')
        keywords = request.POST.get('keywords')
        if keywords:
            if product_info.endswith("."):
                product_info = product_info+"."
            prompt = "Write a product description for "+ prompt + ", " + product_info
            if not keywords.endswith("."):
                keywords = keywords+"."
            

        choices = generate_prediction_openai(prompt,keywords , "Keywords") 
        serializer = ProductDescriptionSerializer({"prompt":prompt , "keywords": keywords , "choices" : choices })
        if choices:
            return Response(serializer.data)
        else:
            return Response(serializer.errors)

    if CATEGORIES == "FacebookAd":
        prompt = request.POST.get('product_name')
        description = request.POST.get('description')
        prompt = "Generate five Facebook Ad headline for " + prompt+"."
        if not description.endswith("."):
            description = description+"."
        choices = generate_prediction_openai(prompt,description , "description")     
        serializer = FaceBookAdSerializer({"prompt":prompt , "description": description , "choices" : choices })
        if choices:
            return Response(serializer.data)
        else:
            return Response(serializer.errors)
        






@api_view(['POST'])
def langudetect(request):
  # language = {}
  sentence = request.POST.get('sentence')
  detected = detect_langs(sentence)  
  lang = str(detected[0]).rstrip(':.0123456789')
  code = LanguagesLocale.objects.filter(locale_code = lang)
  for  i in code:
    print(i.locale_code)
                
  return JsonResponse({"language":lang})