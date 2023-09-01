from types import GetSetDescriptorType

from ai_vendor.models import (VendorBankDetails, VendorCATsoftware,
                              VendorContentTypes, VendorLanguagePair,
                              VendorMembership, VendorMtpeEngines,
                              VendorServiceInfo, VendorServiceTypes,
                              VendorsInfo, VendorSubjectFields, TranslationSamples, MtpeSamples,
                              )
from django.http import JsonResponse
from django.shortcuts import render
from tablib import Dataset

from .forms import UploadFileForm
from .models import (AiUserType, Billingunits, ContentTypes, Countries,ProzExpertize,
                     Currencies, Languages, LanguagesLocale, MtpeEngines,ProzLanguagesCode,
                     ServiceTypes, SubjectFields, SupportFiles, Timezones,IndianStates,StripeTaxId,
                     LanguageMetaDetails, OldVendorPasswords, CurrencyBasedOnCountry,MTLanguageSupport,TranscribeSupportedPunctuation)
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
                value = ProzExpertize(
                            subject_field_id = data[1],
                            expertize_ids =data[2],
                            #speech_to_text = data[2],
                            #text_to_speech = data[3],
                            #translate = data[4],
                            # script_id = data[2],
                            # ime = data[3],
                            # uid =data[4],
                            # email = data[5],
                            # fullname =data[6],
                            # is_staff = data[7],
                            # is_active = data[8],
                            # date_joined = data[9],
                            # from_mysql = data[10],

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
