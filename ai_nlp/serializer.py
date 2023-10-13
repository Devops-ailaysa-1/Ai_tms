from rest_framework import serializers
from ai_nlp.models import PdffileUpload,PdffileChatHistory
from ai_nlp.utils import loader #,thumbnail_create


class PdffileChatHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = PdffileChatHistory
        fields ='__all__'

class PdffileShowDetailsSerializer(serializers.ModelSerializer):
    pdf_file_chat=PdffileChatHistorySerializer(many=True)
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
from ai_nlp.utils import epub_processing
def chat_page_chk(instance):
    from ai_workspace_okapi.utils import page_count_in_docx
    page_count=0
    file_format=''
    if instance.file.name.endswith(".docx"): 
        page_count,file_path = page_count_in_docx(instance.file.path)
        file_format='docx'
    elif instance.file.name.endswith(".pdf"):
        pdf = PdfFileReader(open(instance.file.path,'rb') ,strict=False)
        page_count = pdf.getNumPages()
        file_format='pdf'
    elif instance.file.name.endswith(".epub"):
        text = epub_processing(instance.file.path)
        page_count = num_tokens(text)
        file_format='epub'
    elif instance.file.name.endswith(".txt"):
        page_count = check_txt(instance.file.path)
        file_format='txt'
    return page_count,file_format



class PdffileUploadSerializer(serializers.ModelSerializer):
    # website = serializers.CharField(required=False)
    class Meta:
        model = PdffileUpload
        fields =('id','file_name','created_at','updated_at','celery_id','status','user','file')


    def create(self, validated_data):
        request = self.context['request']
        from ai_auth.api_views import AilaysaPurchasedUnits
        chat_unit_obj = AilaysaPurchasedUnits(user=request.user)

        unit_chk = chat_unit_obj.get_units(service_name="pdf-chat-files")
        if unit_chk['total_units_left']>0: 
            instance = PdffileUpload.objects.create(**validated_data)
            page_count,file_format = chat_page_chk(instance)
            if file_format in ["pdf","docx"] and page_count > 300:
                instance.delete()
                raise serializers.ValidationError({'msg':'file size limit exceed' }, code=400)
            
            elif file_format in ["epub","txt"] and page_count > 200_000:
                instance.delete()
                raise serializers.ValidationError({'msg':'file size limit exceed' }, code=400)
            
            instance.file_name = instance.file.name.split("/")[-1]#.split(".")[0] ###not a file
            instance.status="PENDING"
            # if instance.file.name.endswith(".epub"):
            #     text_scrap = epub_processing(instance.file.path)
            #     instance.text_file =text_scrap
            #     instance.save()
            celery_id = loader.apply_async(args=(instance.id,),) #loader(instance.id)#
            print(celery_id)
            print("vector chromadb created")
            instance.celery_id=celery_id
            instance.is_train=False

            # if instance.file.name.endswith(".pdf"):
            #     instance.pdf_thumbnail = thumbnail_create(instance.file.path)
            chat_unit_obj = AilaysaPurchasedUnits(user=instance.user)
            chat_unit_obj.deduct_units(service_name="pdf-chat-files",to_deduct_units=1)
            instance.save()

            return instance
        else:
            raise serializers.ValidationError({'msg':'Need to buy add-on pack reached your file upload limit'}, code=400)
        
