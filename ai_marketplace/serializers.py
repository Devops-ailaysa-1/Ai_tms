from rest_framework import serializers
from ai_marketplace.models import (ProjectboardDetails,ProjectPostJobDetails,
                    BidChat,BidPropasalDetails,
                    Thread,ProjectPostContentType,ProjectPostSubjectField,ChatMessage,
                    ProjectPostTemplateJobDetails,ProjectPostTemplateContentType,
                    ProjectPostTemplateSubjectField,ProjectboardTemplateDetails,
                    ProjectPostContentType,ProjectPostSteps,ProjectPostTemplateSteps)
from ai_auth.models import AiUser,AiUserProfile,HiredEditors
from ai_staff.models import Languages
from django.db.models import Q
from ai_workspace.models import Project,Job
from drf_writable_nested import WritableNestedModelSerializer
import json,requests
from ai_workspace.models import Steps
from itertools import groupby
from rest_framework.response import Response
from dj_rest_auth.serializers import UserDetailsSerializer
from ai_auth.serializers import ProfessionalidentitySerializer
from ai_vendor.serializers import VendorLanguagePairSerializer,VendorSubjectFieldSerializer,VendorContentTypeSerializer,VendorServiceInfoSerializer,VendorLanguagePairCloneSerializer
from ai_vendor.models import VendorLanguagePair,VendorServiceInfo,VendorsInfo,VendorSubjectFields
from  django.utils import timezone


class SimpleProjectSerializer(serializers.ModelSerializer):
    # project_analysis = serializers.SerializerMethodField(method_name='get_project_analysis')
    # vendor_count = serializers.SerializerMethodField(method_name='get_vendor_count')

    class Meta:
        model = Project
        fields = ("id", "project_name",)#"files_jobs_choice_url", "project_analysis",'vendor_count',)


    # def get_vendor_count(self,instance):
    #     jobs = instance.get_jobs
    #     out=[]
    #     for i in jobs:
    #          res=VendorLanguagePair.objects.filter(Q(source_lang_id=i.source_language_id) & Q(target_lang_id=i.target_language_id)).distinct('user')
    #          data = {'job':i.id,'count':res.count()}
    #          out.append(data)
    #     return out
    #
    # def get_project_analysis(self,instance):
    #     user = self.context.get("request").user if self.context.get("request")!=None else self\
    #            .context.get("ai_user", None)
    #     if instance.ai_user == user:
    #         tasks = instance.get_tasks
    #     elif instance.team:
    #         if ((instance.team.owner == user)|(user in instance.team.get_project_manager)):
    #             tasks = instance.get_tasks
    #         else:
    #             tasks = [task for job in instance.project_jobs_set.all() for task \
    #                     in job.job_tasks_set.all() for task_assign in task.task_info.filter(assign_to_id = user)]
    #     else:
    #         tasks = [task for job in instance.project_jobs_set.all() for task \
    #                 in job.job_tasks_set.all() for task_assign in task.task_info.filter(assign_to_id = user)]
    #     res = instance.project_analysis(tasks)
    #     return res


class BidChatSerializer(serializers.ModelSerializer):
    class Meta:
        model = BidChat
        fields = "__all__"

    def save(self):
        message = BidChat.objects.create(**self.validated_data)
        return message

    def save_update(self):
        return super().save()


class BidPropasalServicesRatesSerializer(serializers.ModelSerializer):

    class Meta:
        model = BidPropasalDetails
        fields = ('bidpostjob','mtpe_rate','mtpe_hourly_rate','mtpe_count_unit','currency',)




class BidPropasalDetailSerializer(serializers.ModelSerializer):
    service_and_rates = BidPropasalServicesRatesSerializer(many=True,required=False)
    projectpost_id  = serializers.PrimaryKeyRelatedField(queryset=ProjectboardDetails.objects.all().values_list('pk', flat=True))
    vendor_id = serializers.PrimaryKeyRelatedField(queryset=AiUser.objects.all().values_list('pk', flat=True))
    job_id = serializers.SerializerMethodField()
    bid_vendor_uid = serializers.ReadOnlyField(source =  'vendor.uid')
    bid_vendor_name = serializers.ReadOnlyField(source = 'vendor.fullname')
    projectpost_title = serializers.ReadOnlyField(source = 'projectpost.proj_name')
    original_project_id = serializers.ReadOnlyField(source = 'projectpost.project.id')
    bidpostjob_name = serializers.ReadOnlyField(source = 'bidpostjob.source_target_pair_names')
    professional_identity= serializers.ReadOnlyField(source='vendor.professional_identity_info.avatar_url')
    # projectpost_status = serializers.SerializerMethodField()
    current_status = serializers.SerializerMethodField()#ReadOnlyField(source='status.status')

    class Meta:
        model = BidPropasalDetails
        fields = ('id','projectpost_id','projectpost_title','vendor_id','bidpostjob','proposed_completion_date','description','sample_file','filename',\
                    'mtpe_rate','mtpe_hourly_rate','mtpe_count_unit','currency','status','current_status','edited_count','service_and_rates','bid_step',\
                    'original_project_id','job_id','bidpostjob_name','bid_vendor_name','bid_vendor_uid','professional_identity','created_at',)
        extra_kwargs = {
        	"bidpostjob":{
        		"required": False
        	}
            # "status":{
            # "write_only":True
            # }
        }

    def get_job_id(self,obj):
        tar_lang = None if obj.bidpostjob.src_lang_id == obj.bidpostjob.tar_lang_id else obj.bidpostjob.tar_lang_id
        pr = obj.bidpostjob.projectpost.project
        job = pr.project_jobs_set.filter(Q(source_language_id = obj.bidpostjob.src_lang_id) & Q(target_language_id = tar_lang))
        return job[0].id if job else None

    def get_current_status(self,obj):
        if obj.projectpost.closed_at != None:
            return "Projectpost Closed"
        elif obj.projectpost.deleted_at !=None:
            return "Projectpost Deleted"
        else:
            return obj.status.status

    # def get_projectpost_status(self,obj):
    #     if obj.projectpost.closed_at != None:
    #         return "closed"
    #     elif obj.projectpost.deleted_at !=None:
    #         return "deleted"
    #     else:
    #         return "Active"


    def run_validation(self, data):
        if self.context['request']._request.method == 'POST':
            pp = ProjectboardDetails.objects.get(id = data.get('projectpost_id'))
            vendor = AiUser.objects.get(id=data.get('vendor_id'))
            if vendor == pp.customer:
                raise serializers.ValidationError({"msg":"you can't bid your post"})
        if data.get("service_and_rates") and isinstance( data.get("service_and_rates"), str):
            data["service_and_rates"]=json.loads(data["service_and_rates"])
        return super().run_validation(data)


    def create(self,data):
        service = data.pop("service_and_rates",[])
        res = [BidPropasalDetails.objects.get_or_create(bidpostjob=i.get('bidpostjob'),vendor_id=data.get('vendor_id'),\
                defaults={**data,'bidpostjob':i.get('bidpostjob'),'mtpe_rate':i.get('mtpe_rate'),'mtpe_hourly_rate':i.get('mtpe_hourly_rate'),\
                            'mtpe_count_unit':i.get('mtpe_count_unit'),'currency':i.get('currency')}) for i in service]
        return res

    def update(self, instance, data):
        service = data.pop("service_and_rates",[])
        dt = super().update(instance, data)
        if service:
            queryset = BidPropasalDetails.objects.filter(bidpostjob_id=service[0].get('bidpostjob'))
            edited_count = 1 if queryset.first().edited_count==None else queryset.first().edited_count+1
            queryset.update(mtpe_rate=service[0].get('mtpe_rate'),\
                                            mtpe_hourly_rate =service[0].get('mtpe_hourly_rate'),mtpe_count_unit = service[0].get('mtpe_count_unit'),\
                                            status_id=5,edited_count=edited_count)
            return queryset[0]
        return instance



#
# class BidPropasalUpdateSerializer(serializers.ModelSerializer):
#     service_and_rates = BidPropasalServicesRatesSerializer(many=True,required=False)
#     projectpost_id  = serializers.PrimaryKeyRelatedField(queryset=ProjectboardDetails.objects.all().values_list('pk', flat=True))
#     vendor_id = serializers.PrimaryKeyRelatedField(queryset=AiUser.objects.all().values_list('pk', flat=True))
#
#     class Meta:
#         model = BidPropasalDetails
#         fields = ('id','projectpost_id','vendor_id','service_and_rates','proposed_completion_date','description','sample_file','filename',)
#
#     def run_validation(self, data):
#         if data.get("service_and_rates") and isinstance( data.get("service_and_rates"), str):
#             data["service_and_rates"]=json.loads(data["service_and_rates"])
#         return data

    # def create(self,data):
    #     bidpost_obj = BidPropasalDetails.objects.filter(projectpost_id = data.get('post_id'))
    #     service = data.pop("service_and_rates",[])
    #     if not bidpost_obj:
    #         bd = BidPropasalDetails.objects.create(**data)
    #         if service:
    #             [BidProposalServicesRates.objects.create(**i,status=1) for i in service]
    #     if bidpost_obj:
    #         if service:
    #             bidservice_obj =BidProposalServicesRates.objects.filter(bidpostjob_id=service.get('bidpostjob'))



    # def update(self, instance, data):
    #     service = data.pop("service_and_rates",[])[0]
    #     queryset = BidProposalServicesRates.objects.filter(bidpostjob_id=service.get('bidpostjob'))
    #     edited_count = 1 if queryset.first().edited_count==None else queryset.first().edited_count+1
    #     if service:
    #         queryset.update(mtpe_rate=service.get('mtpe_rate'),\
    #                                         mtpe_hourly_rate =service.get('mtpe_hourly_rate'),mtpe_count_unit = service.get('mtpe_count_unit'),\
    #                                         status_id=5,edited_count=edited_count)
    #     return super().update(instance, data)





class ThreadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Thread
        fields = "__all__"

    def run_validation(self, data):
        first_person = data.get('first_person')
        second_person = data.get('second_person')
        bid = data.get('bid')
        if first_person == second_person:
            raise serializers.ValidationError({"msg":"Thread between same person cannot be created"})
        else:
            lookup1 = Q(first_person=first_person) & Q(second_person=second_person)
            lookup2 = Q(first_person=second_person) & Q(second_person=first_person)
            lookup = Q(lookup1 | lookup2)
            qs = Thread.objects.filter(lookup)
            if qs.exists():
                raise serializers.ValidationError({"msg":f'Thread between {first_person} and {second_person} already exists.','thread_id':qs[0].id})# for this {bid}.'})
        return super().run_validation(data)



class GetVendorDetailSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    uid = serializers.CharField(read_only=True)
    fullname = serializers.CharField(read_only=True)
    organisation_name = serializers.ReadOnlyField(source='ai_profile_info.organisation_name')
    legal_category = serializers.ReadOnlyField(source='vendor_info.type.name')
    currency = serializers.ReadOnlyField(source='vendor_info.currency.currency_code')
    country = serializers.ReadOnlyField(source = 'country.name')
    location = serializers.ReadOnlyField(source = 'vendor_info.location')
    native_lang = serializers.ReadOnlyField(source = 'vendor_info.native_lang.language')
    year_of_experience = serializers.ReadOnlyField(source = 'vendor_info.year_of_experience')
    professional_identity= serializers.ReadOnlyField(source='professional_identity_info.avatar_url')
    vendor_subject = VendorSubjectFieldSerializer(read_only=True,many=True)
    vendor_contentype = VendorContentTypeSerializer(read_only=True,many=True)
    vendor_lang_pair = serializers.SerializerMethodField(source='get_vendor_lang_pair')
    status = serializers.SerializerMethodField()

    def get_vendor_lang_pair(self, obj):
        request = self.context['request']
        job_id= request.query_params.get('job')
        source_lang = request.query_params.get('source_lang')
        target_lang = request.query_params.get('target_lang')
        if job_id:
            source_lang=Job.objects.get(id=job_id).source_language_id
            target_lang=Job.objects.get(id=job_id).target_language_id
        queryset = obj.vendor_lang_pair.filter(Q(source_lang_id=source_lang)&Q(target_lang_id=target_lang)&Q(deleted_at=None))
        query = queryset.filter(currency = obj.currency_based_on_country)
        if query.exists():
            if query[0].service.exists() or query[0].servicetype.exists():
                return VendorLanguagePairCloneSerializer(query, many=True, read_only=True).data
            else:return {'service':[],'servicetype':[]}
        else:
            query = queryset.filter(currency_id=144)
            if query.exists():
                if query[0].service.exists() or query[0].servicetype.exists():
                    return VendorLanguagePairCloneSerializer(query, many=True, read_only=True).data
                else:return {'service':[],'servicetype':[]}
            else:
                objs = [data for data in queryset if data.service.exists() or data.servicetype.exists()]
                if objs:
                    return VendorLanguagePairCloneSerializer(objs[0], many=False, read_only=True).data
                else:return {'service':[],'servicetype':[]}
        # query = obj.vendor_lang_pair.filter(Q(source_lang_id=source_lang)&Q(target_lang_id=target_lang)&Q(deleted_at=None))
        # if query.count() > 1:
        #     query1 = query.filter(currency_id=obj.currency_based_on_country_id)
        #     if query1.exists():
        #         queryset = query1
        #     else: queryset = [query.first(),]
        # return VendorLanguagePairCloneSerializer(queryset, many=True, read_only=True).data

    def get_status(self,obj):
        request_user = self.context['request'].user
        user = request_user.team.owner if ((request_user.team) and (request_user.is_internal_member == True)) else request_user
        editor = AiUser.objects.get(uid = obj.uid)
        if editor in user.get_hired_editors:
            hired = HiredEditors.objects.get(Q(hired_editor = editor)&Q(user = user))
            return hired.get_status_display()
        else:
            return None

class ProjectPostJobSerializer(serializers.ModelSerializer):
    class Meta:
        model=ProjectPostJobDetails
        fields=('id','src_lang','tar_lang',)

class ProjectPostJobDetailSerializer(serializers.ModelSerializer):
    bid_count = serializers.SerializerMethodField()
    bid_details = BidPropasalDetailSerializer(many=True,read_only=True)
    # bidproject_details = BidPropasalDetailSerializer(many=True,read_only=True)
    class Meta:
        model=ProjectPostJobDetails
        fields=('id','src_lang','tar_lang','bid_count','bid_details',)

    def get_bid_count(self, obj):
        return obj.bid_details.count()

class ProjectPostContentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectPostContentType
        fields = ('id','content_type',)

class ProjectPostStepsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectPostSteps
        fields = ('steps',)

class ProjectPostSubjectFieldSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectPostSubjectField
        fields = ('id','subject',)


class ProjectPostTemplateStepsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectPostTemplateSteps
        fields = ('steps',)

class ProjectPostTemplateJobDetailSerializer(serializers.ModelSerializer):

    class Meta:
        model=ProjectPostTemplateJobDetails
        fields=('id','src_lang','tar_lang',)



class ProjectPostTemplateContentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectPostTemplateContentType
        fields = ('content_type',)

class ProjectPostTemplateSubjectFieldSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectPostTemplateSubjectField
        fields = ('subject',)


class ProjectPostSerializer(WritableNestedModelSerializer,serializers.ModelSerializer):
    bid_count = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    # bidproject_details = BidPropasalDetailSerializer(many=True,read_only=True)
    projectpost_jobs=ProjectPostJobDetailSerializer(many=True,required=False)
    projectpost_content_type=ProjectPostContentTypeSerializer(many=True,required=False)
    projectpost_subject=ProjectPostSubjectFieldSerializer(many=True,required=False)
    projectpost_steps=ProjectPostStepsSerializer(many=True,required=False)
    project_id=serializers.PrimaryKeyRelatedField(queryset=Project.objects.all().values_list('pk', flat=True),write_only=True)
    customer_id = serializers.PrimaryKeyRelatedField(queryset=AiUser.objects.all().values_list('pk', flat=True),write_only=True)
    # steps_id = serializers.PrimaryKeyRelatedField(queryset=Steps.objects.all().values_list('pk', flat=True),write_only=True)
    class Meta:
        model=ProjectboardDetails
        fields=('id','project_id','customer_id','proj_name','proj_desc','post_word_count','status',
                 'bid_deadline','proj_deadline','ven_native_lang','ven_res_country','ven_special_req',
                 'bid_count','projectpost_jobs','projectpost_content_type','projectpost_subject',
                 'rate_range_min','rate_range_max','currency','unit','milestone','projectpost_steps',
                 'closed_at','deleted_at','created_at',)#'bidproject_details',

    def get_bid_count(self, obj):
        bidproject_details = BidPropasalDetailSerializer(many=True,read_only=True)
        print(obj.bidproject_details.count())
        return obj.bidproject_details.count()

    def get_status(self,obj):
        present = timezone.now()
        if obj.closed_at:
            return "Closed"
        elif obj.bid_deadline < present:
            return "Expired"
        else:
            return "Active"

    def run_validation(self, data):
        # if data.get('steps'):
        #     data['steps'] = json.loads(data['steps'])
        if data.get('contents') and isinstance( data.get("contents"), str):
            data["projectpost_content_type"] = json.loads(data['contents'])

        if data.get('subjects') and isinstance( data.get("subjects"), str):
            data["projectpost_subject"] = json.loads(data['subjects'])

        if data.get('steps') and isinstance( data.get("steps"), str):
            data['projectpost_steps'] = json.loads(data['steps'])

        if data.get("jobs") and isinstance( data.get("jobs"), str):
            jobs=json.loads(data["jobs"])
            source_language = jobs[0].get("src_lang")
            target_languages = jobs[0].get("tar_lang")
            if source_language and target_languages:
                data["projectpost_jobs"] = [{"src_lang": source_language, "tar_lang": target_language}
                                            for target_language in jobs[0].get("tar_lang",None)]
            else:
                data["projectpost_jobs"] = [{"src_lang": source_language, "tar_lang":None}]
        # print("data---->",data["projectpost_jobs"])
        return super().run_validation(data)


class PrimaryBidDetailSerializer(serializers.Serializer):
    bid_applied = serializers.SerializerMethodField()
    projectpost_steps = ProjectPostStepsSerializer(many=True,required=False)
    service_info = serializers.SerializerMethodField()
    post_jobs = serializers.SerializerMethodField()

    class Meta:
        fields = ('post_jobs','projectpost_steps','bid_applied','service_info',)

    def get_bid_applied(self,obj):
        applied =[]
        vendor = self.context.get("request").user
        jobs = obj.get_postedjobs
        for i in jobs:
            if i.bid_details.filter(vendor_id = vendor.id):
                applied.append(i)
        return ProjectPostJobDetailSerializer(applied,many=True).data

    def get_post_jobs(self,obj):
        vendor = self.context.get("request").user
        jobs = obj.get_postedjobs
        matched_jobs=[]
        for i in jobs:
            if i.src_lang_id == i.tar_lang_id:
                res = VendorLanguagePair.objects.filter((Q(source_lang_id=i.src_lang_id) | Q(target_lang_id=i.tar_lang_id) & Q(user=vendor) & Q(deleted_at=None)))
            else:
                res = VendorLanguagePair.objects.filter((Q(source_lang_id=i.src_lang_id) & Q(target_lang_id=i.tar_lang_id) & Q(user=vendor) & Q(deleted_at=None)))
            # res = VendorLanguagePair.objects.filter((Q(source_lang_id=i.src_lang_id) & Q(target_lang_id=i.tar_lang_id) & Q(user=vendor) & Q(deleted_at=None)))
            if res:
                matched_jobs.append(i)
        print(matched_jobs)
        return ProjectPostJobSerializer(matched_jobs,many=True).data



    def get_service_info(self,obj):
        vendor = self.context.get("request").user
        jobs = obj.get_postedjobs
        service_details=[]
        for i in jobs:
            if i.src_lang_id == i.tar_lang_id:
                query = VendorLanguagePair.objects.filter((Q(source_lang_id=i.src_lang_id) | Q(target_lang_id=i.tar_lang_id) & Q(user=vendor) & Q(deleted_at=None)))\
                        .select_related('service').values('currency','service__mtpe_rate','service__mtpe_hourly_rate','service__mtpe_count_unit')
            else:
                query = VendorLanguagePair.objects.filter((Q(source_lang_id=i.src_lang_id) & Q(target_lang_id=i.tar_lang_id) & Q(user=vendor) & Q(deleted_at=None)))\
                        .select_related('service').values('currency','service__mtpe_rate','service__mtpe_hourly_rate','service__mtpe_count_unit')
            query1 = query.filter(currency=obj.currency)
            if query1: res= query1
            else: res= query
            #########################if user preffered currency exists,then use that or pick first instance matching that job pair and convert to user_preffered_currency###############
            if res:
                # vpc = currency
                # upc = obj.currency.currency_code
                # payload = {'q': vpc+'_'+upc}
                # res1 = requests.get('https://free.currconv.com/api/v7/convert?compact=ultra&apiKey=78341dcc54736bbff6e1',params=payload)
                # rate = res1.json().get(payload.get('q'))
                # out=[{"vendor_id":vendor.id,"postedjob_id":i.id,"user_preffered_currency_id":obj.currency.id,"user_preffered_currency":obj.currency.currency_code,"vendor_given_currency":currency,"mtpe_rate":float(res[0].get('service__mtpe_rate'))*rate,"mtpe_hourly_rate":float(res[0].get('service__mtpe_hourly_rate'))*rate,"mtpe_count_unit":float(res[0].get('service__mtpe_count_unit'))*rate}]
                out=[{"vendor_id":vendor.id,"postedjob_id":i.id,"user_preffered_currency_id":obj.currency.id,"user_preffered_currency":obj.currency.currency_code,"vendor_given_currency":res[0].get('currency'),"mtpe_rate":res[0].get('service__mtpe_rate'),"mtpe_hourly_rate":res[0].get('service__mtpe_hourly_rate'),"mtpe_count_unit":res[0].get('service__mtpe_count_unit')}]
            else:
                out=[]
            service_details.extend(out)
        return service_details



class AvailablePostJobSerializer(serializers.Serializer):
    post_id = serializers.ReadOnlyField(source = 'id')
    post_name = serializers.ReadOnlyField(source='proj_name')
    post_desc = serializers.ReadOnlyField(source='proj_desc')
    posted_by = serializers.ReadOnlyField(source='customer.fullname')
    apply = serializers.SerializerMethodField()
    post_bid_deadline =serializers.ReadOnlyField(source='bid_deadline')
    post_deadline = serializers.ReadOnlyField(source='proj_deadline')
    projectpost_subject=ProjectPostSubjectFieldSerializer(many=True,required=False)
    projectpost_steps =ProjectPostStepsSerializer(many=True,required=False)
    projectpost_jobs=ProjectPostJobSerializer(many=True,required=False)


    class Meta:
        fields = ('post_id', 'post_name','posted_by','post_desc','post_bid_deadline','post_deadline','projectpost_steps','projectpost_jobs','projectpost_subject','apply', )

    def get_apply(self, obj):
        vendor = self.context.get("request").user
        jobs = obj.get_postedjobs
        for i in jobs:
            if i.src_lang_id == i.tar_lang_id:
                res = VendorLanguagePair.objects.filter((Q(source_lang_id=i.src_lang_id) | Q(target_lang_id=i.tar_lang_id) & Q(user=vendor) & Q(deleted_at=None)))
            else:
                res = VendorLanguagePair.objects.filter((Q(source_lang_id=i.src_lang_id) & Q(target_lang_id=i.tar_lang_id) & Q(user=vendor) & Q(deleted_at=None)))
            if res:
                return True
        return False

class ProjectPostTemplateSerializer(WritableNestedModelSerializer,serializers.ModelSerializer):
    template_name = serializers.CharField()
    projectposttemp_jobs=ProjectPostTemplateJobDetailSerializer(many=True,required=False)
    projectposttemp_content_type=ProjectPostTemplateContentTypeSerializer(many=True,required=False)
    projectposttemp_subject=ProjectPostTemplateSubjectFieldSerializer(many=True,required=False)
    projectposttemp_steps = ProjectPostTemplateStepsSerializer(many=True,required=False)
    project_id=serializers.PrimaryKeyRelatedField(queryset=Project.objects.all().values_list('pk', flat=True),write_only=True)
    customer_id = serializers.PrimaryKeyRelatedField(queryset=AiUser.objects.all().values_list('pk', flat=True),write_only=True)
    # steps_id = serializers.PrimaryKeyRelatedField(queryset=Steps.objects.all().values_list('pk', flat=True),write_only=True)
    class Meta:
        model=ProjectboardTemplateDetails
        fields=('id','template_name','project_id','customer_id','proj_name','proj_desc',
                 'bid_deadline','proj_deadline','ven_native_lang','ven_res_country','ven_special_req',
                 'rate_range_min','rate_range_max','currency','unit','milestone','projectposttemp_steps',
                 'projectposttemp_jobs','projectposttemp_content_type','projectposttemp_subject',)

    def run_validation(self, data):
        print("validated_data---->",data)
        if data.get('contents') and isinstance( data.get("contents"), str):
            data["projectposttemp_content_type"] = json.loads(data['contents'])

        if data.get('subjects') and isinstance( data.get("subjects"), str):
            data["projectposttemp_subject"] = json.loads(data['subjects'])

        if data.get('steps') and isinstance( data.get("steps"), str):
            data['projectposttemp_steps'] = json.loads(data['steps'])

        if data.get("jobs") and isinstance( data.get("jobs"), str):
            jobs=json.loads(data["jobs"])
            source_language = jobs[0].get("src_lang")
            target_languages = jobs[0].get("tar_lang")
            if source_language and target_languages:
                data["projectposttemp_jobs"] = [{"src_lang": source_language, "tar_lang": target_language}
                                            for target_language in target_languages]
        print("data---->",data["projectposttemp_jobs"])
        return super().run_validation(data)

class VendorInfoListSerializer(serializers.ModelSerializer):
    legal_category = serializers.ReadOnlyField(source='type.name')
    currency = serializers.ReadOnlyField(source='currency.currency_code')
    class Meta:
        model = VendorsInfo
        fields = ('legal_category','currency')


class VendorServiceSerializer(serializers.ModelSerializer):
    service = VendorServiceInfoSerializer(many=True,read_only=True)
    Currency = serializers.ReadOnlyField(source='currency.currency_code')
    class Meta:
        model = VendorLanguagePair
        fields = ('Currency','service',)


class GetVendorListSerializer(serializers.ModelSerializer):
    vendor_lang_pair = serializers.SerializerMethodField(source='get_vendor_lang_pair')
    legal_category = serializers.ReadOnlyField(source='vendor_info.type.name')
    currency = serializers.ReadOnlyField(source='vendor_info.currency.currency_code')
    country = serializers.ReadOnlyField(source = 'country.sortname')
    professional_identity= serializers.ReadOnlyField(source='professional_identity_info.avatar_url')
    status = serializers.SerializerMethodField()
    class Meta:
        model = AiUser
        fields = ('id','uid','fullname','legal_category','country','currency','professional_identity','vendor_lang_pair','status',)


    def get_status(self,obj):
        request_user = self.context['request'].user
        user = request_user.team.owner if ((request_user.team) and (request_user.is_internal_member == True)) else request_user
        editor = AiUser.objects.get(uid = obj.uid)
        if editor in user.get_hired_editors:
            hired = HiredEditors.objects.get(Q(hired_editor = editor)&Q(user = user))
            return hired.get_status_display()
        else:
            return None

    def get_vendor_lang_pair(self, obj):
        request = self.context['request']
        job_id= request.query_params.get('job')
        source_lang = request.query_params.get('source_lang')
        target_lang = request.query_params.get('target_lang')
        if job_id:
            source_lang=Job.objects.get(id=job_id).source_language_id
            target_lang=Job.objects.get(id=job_id).target_language_id
        queryset = obj.vendor_lang_pair.filter(Q(source_lang_id=source_lang)&Q(target_lang_id=target_lang)&Q(deleted_at=None))
        query = queryset.filter(currency=obj.currency_based_on_country)
        if query.exists():
            if query[0].service.exists():
                return VendorServiceSerializer(query, many=True, read_only=True).data
            else:return {'service':[]}
        else:
            query1 = queryset.filter(currency_id = 144)
            if query1.exists():
                if query1[0].service.exists():
                    return VendorServiceSerializer(query1, many=True, read_only=True).data
                else:return {'service':[]}
            else:
                objs = [data for data in queryset if data.service.exists()]
                if objs:
                    return VendorServiceSerializer(objs[0], many=False, read_only=True).data
                else:return {'service':[]}


        # if query.count() > 1:
        #     query1 = query.filter(currency_id=obj.currency_based_on_country_id)
        #     if query1.exists():
        #         queryset = query1
        # else: queryset = [query.first(),]
        #return VendorServiceSerializer(queryset, many=True, read_only=True).data

class ChatMessageSerializer(serializers.ModelSerializer):
    user_name = serializers.ReadOnlyField(source='user.fullname')

    class Meta:
        model = ChatMessage
        fields = ('id','thread','user','user_name','message','timestamp',)


    def run_validation(self,data):
        if self.context['request']._request.method == 'POST':
            user = int(data.get('user'))
            thread = data.get('thread')
            user1 = Thread.objects.get(id = thread).first_person_id
            user2 = Thread.objects.get(id = thread).second_person_id
            if (user!=user1) and (user!=user2):
                raise serializers.ValidationError({"msg":'This person is not in this thread,he cannot send messages here'})
        return super().run_validation(data)


class ChatMessageByDateSerializer(serializers.ModelSerializer):
    logged_in_user = serializers.SerializerMethodField()
    user_name = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()
    message = serializers.SerializerMethodField()
    organisation_name = serializers.SerializerMethodField()
    class Meta:
        model = Thread
        fields = ('logged_in_user','user_name','avatar','organisation_name','message',)

    def get_logged_in_user(self,obj):
        user = self.context['request'].user
        return user.id

    def get_user_name(self,obj):
        user = obj.first_person if obj.second_person == self.context['request'].user else obj.second_person
        # user = self.context['request'].user
        return user.fullname

    def get_avatar(self,obj):
        user = obj.first_person if obj.second_person == self.context['request'].user else obj.second_person
        try: return user.professional_identity_info.avatar_url
        except: return None

    def get_organisation_name(self,obj):
        user = obj.first_person if obj.second_person == self.context['request'].user else obj.second_person
        try: return user.ai_profile_info.organisation_name
        except: return None

    def get_message(self, obj):
        message = self.context['request'].query_params.get('message')
        if message:
            messages = ChatMessage.objects.filter(Q(thread_id = obj.id) & Q(message__icontains=message))
        else:
            messages = ChatMessage.objects.filter(thread_id = obj.id)
        messages_grouped_by_date = groupby(messages.iterator(), lambda m: m.timestamp.date())
        messages_dict = {}
        for date, group_of_messages in messages_grouped_by_date:
            dict_key = date.strftime('%Y-%m-%d')
            messages_dict[dict_key] = ChatMessageSerializer(group_of_messages,many=True).data
        return messages_dict


class GetVendorListBasedonProjectSerializer(serializers.ModelSerializer):
    vendor_lang_pair = serializers.SerializerMethodField(source='get_vendor_lang_pair')
    legal_category = serializers.ReadOnlyField(source='vendor_info.type.name')
    currency = serializers.ReadOnlyField(source='vendor_info.currency.currency_code')
    country = serializers.ReadOnlyField(source = 'country.sortname')
    professional_identity= serializers.ReadOnlyField(source='professional_identity_info.avatar_url')
    status = serializers.SerializerMethodField()
    class Meta:
        model = AiUser
        fields = ('id','uid','fullname','legal_category','country','currency','professional_identity','vendor_lang_pair','status',)


    def get_status(self,obj):
        request_user = self.context['request'].user
        user = request_user.team.owner if ((request_user.team) and (request_user.is_internal_member == True)) else request_user
        editor = AiUser.objects.get(uid = obj.uid)
        if editor in user.get_hired_editors:
            hired = HiredEditors.objects.get(Q(hired_editor = editor)&Q(user = user))
            return hired.get_status_display()
        else:
            return None

    def get_vendor_lang_pair(self, obj):
        request = self.context['request']
        source_lang = self.context['sl']
        target_lang = self.context['tl']
        queryset = obj.vendor_lang_pair.filter(Q(source_lang_id=source_lang)&Q(target_lang_id=target_lang)&Q(deleted_at=None))
        query = queryset.filter(currency=obj.currency_based_on_country)
        if query.exists():
            if query[0].service.exists():
                return VendorServiceSerializer(query, many=True, read_only=True).data
            else:return {'service':[]}
        else:
            query1 = queryset.filter(currency_id = 144)
            if query1.exists():
                if query1[0].service.exists():
                    return VendorServiceSerializer(query1, many=True, read_only=True).data
                else:return {'service':[]}
            else:
                objs = [data for data in queryset if data.service.exists()]
                if objs:
                    return VendorServiceSerializer(objs[0], many=False, read_only=True).data
                else:return {'service':[]}
