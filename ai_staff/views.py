from django.shortcuts import render
from .models import ContentTypes, Countries, Currencies, Languages, LanguagesLocale, MtpeEngines, ServiceTypes, SubjectFields, SupportFiles, Timezones,Billingunits,AiUserType
from tablib import Dataset
from .forms import UploadFileForm
from django.http import JsonResponse
# Create your views here.



def Bulk_insert(request):
    if request.method== 'POST':
        try:
            print("*******")
            print(request.FILES)
            #form = UploadFileForm(request.POST, request.FILES)
            dataset = Dataset()
            filedata = request.FILES.get('insertfile')
            
            print("&&&&&&&&")
            imported_data = dataset.load(filedata.read(), format='xlsx')
            print(imported_data)
            for data in imported_data:
                
                value = AiUserType(
			type=data[0].strip(),
			#name=data[1].strip(),
			#utc_offset=data[2].strip(),

              

    
                )
                print(value)
                value.save()
            print("$$$ END  $$$")
            return JsonResponse({'message':'success'})
        except Exception as E:
                print(E)
                return JsonResponse({'message':'Failed'})
    else:
        form =UploadFileForm()
        return render(request,'test.html',{'form':form})
