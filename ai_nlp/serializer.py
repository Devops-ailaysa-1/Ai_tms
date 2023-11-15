from rest_framework import serializers
from ai_nlp.models import PdffileUpload,PdffileChatHistory ,ChatEmbeddingLLMModel,PdfQustion
from ai_nlp.utils import loader #,thumbnail_create


class PdfQustionSerializer(serializers.ModelSerializer):
    class Meta:
        model =PdfQustion
        fields ='__all__'


class PdffileChatHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = PdffileChatHistory
        fields ='__all__'

class PdffileShowDetailsSerializer(serializers.ModelSerializer):
    pdf_file_chat=PdffileChatHistorySerializer(many=True)
    pdf_file_question = PdfQustionSerializer(many=True)
    class Meta:
        model = PdffileUpload
        fields = '__all__'

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        pdf_file_chat = instance.pdf_file_chat.order_by('id')
        representation['pdf_file_chat'] = PdffileChatHistorySerializer(pdf_file_chat, many=True).data
        return representation

from ai_openai.api_views import encoding
def num_tokens(string) -> int:
    num_tokens = len(encoding.encode(string)) 
    return num_tokens

def check_txt(path):
    with open(path,'rb') as fp:
        tot_tokens = num_tokens(str(fp.read()))
    return tot_tokens

from PyPDF2 import PdfFileReader 
from PyPDF2.errors import FileNotDecryptedError
from ai_nlp.utils import epub_processing

def chat_page_chk(instance):
    from ai_workspace_okapi.utils import page_count_in_docx ,count_pdf_pages
    page_count=0
    file_format=''
    if instance.file.name.endswith(".docx"): 
        page_count,file_path = page_count_in_docx(instance.file.path)
        file_format='docx'
    elif instance.file.name.endswith(".pdf"):
        pdf = PdfFileReader(open(instance.file.path,'rb') ,strict=False)
        try:
            # page_count = pdf.getNumPages()
            page_count = count_pdf_pages(instance.file.path)
            file_format='pdf'
        except FileNotDecryptedError:
            raise serializers.ValidationError({'msg':'File has been encrypted unable to process' }, code=400)
    elif instance.file.name.endswith(".epub"):
        text = epub_processing(instance.file.path,text_word_count_check=True)
        page_count = num_tokens(text)
        file_format='epub'
    elif instance.file.name.endswith(".txt"):
        page_count = check_txt(instance.file.path)
        file_format='txt'
    return page_count,file_format



class PdffileUploadSerializer(serializers.ModelSerializer):
    # website = serializers.CharField(required=False)
    pdf_file_question = PdfQustionSerializer(many=True,required=False)
    class Meta:
        model = PdffileUpload
        fields =('id','file_name','created_at','updated_at','celery_id','status','user','file','pdf_file_question')


    def create(self, validated_data):
        request = self.context['request']
        from ai_auth.api_views import AilaysaPurchasedUnits
        chat_unit_obj = AilaysaPurchasedUnits(user=request.user)

        unit_chk = chat_unit_obj.get_units(service_name="pdf-chat-files")
        # unit_chk['total_units_left'] = 90
        if unit_chk['total_units_left']>0: 
            instance = PdffileUpload.objects.create(**validated_data)
            page_count,file_format = chat_page_chk(instance)
            if file_format in ["pdf","docx"] and page_count > 300:
                instance.delete()
                raise serializers.ValidationError({'msg':'File page limit should be less than 300' }, code=400)
            
            elif file_format in ["epub","txt"] and page_count > 200_000:
                instance.delete()
                raise serializers.ValidationError({'msg':'File word limit should be less than 200,000' }, code=400)
            
            instance.file_name = instance.file.name.split("/")[-1]#.split(".")[0] ###not a file
            instance.status="PENDING"
            emb_instance = ChatEmbeddingLLMModel.objects.get(model_name="cohere")
            print("emb_instance",emb_instance)
            instance.embedding_name = emb_instance
            instance.save()
            celery_id = loader.apply_async(args=(instance.id,),) #loader(instance.id)#
            print(celery_id)
            print("vector chromadb created")
            instance.celery_id=celery_id
            instance.is_train=False
            chat_unit_obj = AilaysaPurchasedUnits(user=instance.user)
            chat_unit_obj.deduct_units(service_name="pdf-chat-files",to_deduct_units=1)
            instance.save()

            return instance
        else:
            raise serializers.ValidationError({'msg':'Need to buy add-on pack reached your file upload limit'}, code=400)
        

from ai_nlp.models import StoryIllustate,IllustateGeneration





class StoryIllustateSerializer(serializers.ModelSerializer):
    class Meta:
        model = StoryIllustate
        fields ='__all__'


class IllustateGenerationSerializer(serializers.ModelSerializer):
    illustrate_story = StoryIllustateSerializer(required=False,many=True)
    class Meta:
        model = IllustateGeneration
        fields =('id','illustrate_story','text')

