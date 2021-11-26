from types import GetSetDescriptorType

from ai_vendor.models import (VendorBankDetails, VendorCATsoftware,
                              VendorContentTypes, VendorLanguagePair,
                              VendorMembership, VendorMtpeEngines,
                              VendorServiceInfo, VendorServiceTypes,
                              VendorsInfo, VendorSubjectFields, TranslationSamples, MtpeSamples)
from django.http import JsonResponse
from django.shortcuts import render
from tablib import Dataset

from .forms import UploadFileForm
from .models import (AiUserType, Billingunits, ContentTypes, Countries,
                     Currencies, Languages, LanguagesLocale, MtpeEngines,
                     ServiceTypes, SubjectFields, SupportFiles, Timezones,IndianStates,StripeTaxId,
                     LanguageMetaDetails)
from ai_auth.models import AiUser


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
            # print(imported_data)
            for data in imported_data:
                value = AiUser(
            id = data[0],
			password =data[1],
            last_login = data[2],
            is_superuser = data[3],
			uid =data[4],
            email = data[5],
			fullname =data[6],
            is_staff = data[7],
            is_active = data[8],
            date_joined = data[9],
            from_mysql = data[10],
            #state_code=data[3],
            #unit_rate=data[3],
            #hourly_rate=data[4],
            #minute_rate = data[5],		
            #currency = data[3],
            #vm_status = data[4],
            #status = data[5],
            #token = data[6],
            #skype = data[7],
            #proz_link = data[8],
            #cv_file = data[9],
            #native_lang_id = data[10],
            #year_of_experience = data[11],
            #rating = data[12],
            # created_at = data[3],              
            # updated_at = data[4],
            # deleted_at = data[5],
            # updated_at = data[13],            
            # updated_at = data[14].strip(),            
            # locale_code = data[2].strip(),

            # id =data[0],
            # user_id = data[1],
            # source_lang_id = data[2],		
            # target_lang_id = data[3],
            # created_at = data[3],
            # updated_at = data[4],
            # deleted_at = data[5],
                )
                # print(value)
            value.save()
            # print("$$$ END  $$$")
            return JsonResponse({'message':'success'})
        except Exception as E:
                print(E)
                return JsonResponse({'message':'Failed'})
    else:
        form =UploadFileForm()
        return render(request,'test.html',{'form':form})
