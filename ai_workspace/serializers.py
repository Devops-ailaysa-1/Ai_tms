import logging
from ai_pay.api_views import generate_client_po,po_modify
from ai_staff.serializer import AiSupportedMtpeEnginesSerializer
from ai_staff.models import AilaysaSupportedMtpeEngines, SubjectFields, ProjectType, TranscribeSupportedPunctuation, LanguagesLocale
from rest_framework import serializers
from .models import Project, Job, File, ProjectContentType, Tbxfiles,\
		ProjectSubjectField, TempFiles, TempProject, Templangpair, Task, TmxFile,\
		ReferenceFiles, TbxFile, TbxTemplateFiles, TaskCreditStatus,TaskAssignInfo,MyDocuments,\
		TaskAssignHistory,TaskDetails,TaskAssign,Instructionfiles,Workflows, Steps, WorkflowSteps,\
		ProjectFilesCreateType,ProjectSteps,VoiceProjectDetail,TaskTranscriptDetails,ExpressProjectDetail,\
		ExpressProjectAIMT,WriterProject,DocumentImages,ExpressTaskHistory#,TaskAssignRateInfo
import json,os
import pickle,itertools
from ai_workspace import forms as ws_forms
from notifications.signals import notify
from ai_workspace_okapi.utils import get_file_extension, get_processor_name
from ai_marketplace.serializers import ProjectPostJobDetailSerializer
from django.shortcuts import reverse
from rest_framework.validators import UniqueTogetherValidator
from ai_auth.models import AiUser,Team,HiredEditors
from ai_auth.validators import project_file_size, file_size
from collections import OrderedDict
from django.db.models import Q
from django.db import transaction
from ai_workspace_okapi.models import Document
from ai_auth.serializers import InternalMemberSerializer,HiredEditorSerializer
from ai_vendor.models import VendorLanguagePair
from django.db.models import OuterRef, Subquery
from ai_marketplace.serializers import ProjectPostJobDetailSerializer
from django.db import transaction
from notifications.signals import notify
from ai_auth.utils import obj_is_allowed,authorize_list,objls_is_allowed
from ai_workspace.utils import task_assing_role_ls

logger = logging.getLogger('django')

class DynamicFieldsModelSerializer(serializers.ModelSerializer):
    """
    A ModelSerializer that takes an additional `fields` argument that
    controls which fields should be displayed.
    """

    def __init__(self, *args, **kwargs):
        fields = kwargs.pop("allowed_fields", None)
        # Instantiate the superclass normally
        super(DynamicFieldsModelSerializer, self).__init__(*args, **kwargs)

        if fields:
            # fields = fields.split(',')
            # Drop any fields that are not specified in the `fields` argument.
            allowed = set(fields)
            existing = set(self.fields.keys())
            for field_name in existing - allowed:
                self.fields.pop(field_name)


class ProjectSerializer(serializers.ModelSerializer):
	class Meta:
		model = Project
		exclude = ("created_at", "ai_user","ai_project_id")
		read_only_fields = ("project_dir_path", )

	def create(self, validated_data):
		ai_user = self.context["request"].user
		project = Project.objects.create(**validated_data, ai_user=ai_user)
		return project

class JobSerializer(serializers.ModelSerializer):
	project = serializers.IntegerField(required=False, source="project_id")
	class Meta:
		model = Job
		fields = ("id","project", "source_language", "target_language", "source_target_pair",
				  "source_target_pair_names", "source_language_code", "target_language_code",\
				  "can_delete",'assignable',"type_of_job",)
		read_only_fields = ("id","source_target_pair", "source_target_pair_names")

class FileSerializer(serializers.ModelSerializer):
	project = serializers.IntegerField(required=False, source="project_id")
	file = serializers.FileField(validators=[project_file_size])
	class Meta:
		model = File
		fields = ("id","usage_type", "file", "project","filename", "get_source_file_path",
				  "get_file_name", "can_delete")
		read_only_fields=("id","filename",)

class FileSerializerv2(FileSerializer): # TmX output set
	output_file_path = serializers.CharField(source="get_source_tmx_path")
	source_file_path = serializers.CharField(source="get_source_file_path")
	class Meta(FileSerializer.Meta):
		fields = (
			"output_file_path", "source_language", "source_file_path", "target_language"
		)
	def to_representation(self, instance):
		representation = super().to_representation(instance)
		if self.instance:
			representation["extension"] = get_file_extension(instance.file.path)
			representation["processor_name"] = get_processor_name(instance.file.path)\
												.get("processor_name", None)
		return representation

class FileSerializerv3(FileSerializer):
	file_path = serializers.CharField(source="get_source_tmx_path")
	source_language_code = serializers.CharField(source="source_language")
	target_language_code = serializers.CharField(source="target_language")

	class Meta:
		model = File
		fields = (
			"file_path", "source_language_code", "target_language_code"
		)

class ProjectSetupSerializer(serializers.ModelSerializer):
	jobs = JobSerializer(many=True, source="project_jobs_set", write_only=True)
	files = FileSerializer(many=True, source="project_files_set", write_only=True)
	project_name = serializers.CharField(required=False)

	class Meta:
		model = Project
		fields = ("project_name","jobs", "files", "files_jobs_choice_url",
					"id", "progress", "files_count", "tasks_count", "project_analysis", "is_proj_analysed", ) #"project_analysis"

	def to_internal_value(self, data):
		print("Data------>",data)
		source_language = json.loads(data.pop("source_language", "0"))
		target_languages = json.loads(data.pop("target_languages", "[]"))
		if source_language and target_languages:
			data["jobs"] = [{"source_language": source_language, "target_language": \
				target_language} for target_language in target_languages]
			print(data["jobs"])
		else:
			raise ValueError("source or target values could not json loadable!!!")
			# data["jobs"] = json.loads(data.pop("jobs", "[]"))
		data['files'] = [{"file": file, "usage_type": 1} for file in data.pop('files', [])]
		print("F------>",data.get('files'))
		return super().to_internal_value(data=data)

	def create(self, validated_data):
		ai_user = self.context["request"].user
		project_jobs_set = validated_data.pop("project_jobs_set")
		project_files_set = validated_data.pop("project_files_set")
		project = Project.objects.create(**validated_data,  ai_user=ai_user)
		[project.project_jobs_set.create(**job_data) for job_data in  project_jobs_set]
		[project.project_files_set.create(**file_data) for file_data in project_files_set]
		# project.save()
		return project

class ProjectSubjectSerializer(serializers.ModelSerializer):
	class Meta:
		model = ProjectSubjectField
		fields = ("id","project", "subject")
		read_only_fields = ("id","project",)


class VoiceProjectDetailSerializer(serializers.ModelSerializer):
	class Meta:
		model = VoiceProjectDetail
		fields = ("id","project","source_language", "project_type_sub_category")
		read_only_fields = ("id","project",)

class ExpressTaskHistorySerializer(serializers.ModelSerializer):
	class Meta:
		model = ExpressTaskHistory
		fields = ("id","task","source_text", "target_text",'action','created_at',)
		



class ExpressProjectAIMTSerializer(serializers.ModelSerializer):
	customize_name = serializers.ReadOnlyField(source='customize.customize')
	class Meta:
			model = ExpressProjectAIMT
			fields = ("id",'express','source','customize','mt_engine','api_result','final_result','customize_name')
		# 	extra_kwargs = {
        #     "id":{"write_only": True},
        #     "express": {"write_only": True},
        #     "source": {"write_only": True},
        #     "customize": {"write_only": True},
		# 	"mt_engine":{"write_only": True},
        #     "api_result": {"write_only": True},
        # }

class ExpressProjectDetailSerializer(serializers.ModelSerializer):
	express_src_text = ExpressProjectAIMTSerializer(required=False,many=True,read_only=True)
	project_id = serializers.ReadOnlyField(source='task.job.project.id')
	project_name = serializers.ReadOnlyField(source='task.job.project.project_name')
	target_lang_name = serializers.ReadOnlyField(source='task.job.target_language.language')
	job_id = serializers.ReadOnlyField(source='task.job.id')
	target_lang_id = serializers.ReadOnlyField(source='task.job.target_language.id')
	source_lang_id = serializers.ReadOnlyField(source='task.job.source_language.id')
	number_of_tasks = serializers.SerializerMethodField()
	class Meta:
		model = ExpressProjectDetail
		fields = ('id','task','source_text','target_text','mt_engine','mt_raw',
					"project_id","project_name","target_lang_name","job_id",
					"target_lang_id","source_lang_id",'express_src_text','number_of_tasks',)

	def get_number_of_tasks(self,obj):
		return len(obj.task.job.project.get_tasks)
		# extra_kwargs = {
		# 	"audio_file":{
		# 		"required": False
		# 	}
		# }
# class VoiceProjectFileSerializer(serializers.ModelSerializer):
# 	class Meta:
# 		model = VoiceProjectFile
# 		fields = ('id','voice_project','audio_file')
# 		read_only_fields = ("id","voice_project",)


class ProjectContentTypeSerializer(serializers.ModelSerializer):
	# project = serializers.PrimaryKeyRelatedField()
	# content_type = serializers.PrimaryKeyRelatedField()
	class Meta:
		model = ProjectContentType
		fields = ("id","project", "content_type")
		read_only_fields = ("id","project",)

class ProjectStepsSerializer(serializers.ModelSerializer):
	class Meta:
		model = ProjectSteps
		fields = ("id","project", "steps")
		read_only_fields = ("id","project",)


class ProjectCreationSerializer(serializers.ModelSerializer):
	jobs = JobSerializer(many=True, source="project_jobs_set", write_only=True)
	source_language = serializers.DictField(read_only=True, source="_source_language")
	target_languages = serializers.ListField(read_only=True, source="_target_languages")
	files = FileSerializer(many=True, source="project_files_set")
	subjects =ProjectSubjectSerializer(many=True, source="proj_subject",required=False)
	contents =ProjectContentTypeSerializer(many=True, source="proj_content_type",\
		required=False)
	project_name = serializers.CharField(required=False)

	class Meta:
		model = Project
		fields = ("id","ai_project_id","project_name", "jobs", "files","contents","subjects",\
				  "mt_engine", "source_language", "target_languages")
		read_only_fields = ("id","ai_project_id")
		extra_kwargs = {
			"mt_engine":{
				"required": False
			}
		}
	def run_validation(self, data):
		# print("run_validation")
		return super().run_validation(data=data)

	def to_representation(self, instance):
		ret = super().to_representation(instance)
		ret["jobs"] = {
			"source_language": ret.pop("source_language"),
			"target_languages": ret.pop("target_languages")
		}
		return  ret

	def is_valid(self, *args, **kwargs):

		if not isinstance( self.initial_data['jobs'],dict ):
			self.initial_data['jobs'] = json.loads(self.initial_data['jobs'])

		if isinstance( self.initial_data.get('subjects', None), str ):
			self.initial_data['subjects'] = json.loads(self.initial_data['subjects'])

		if isinstance( self.initial_data.get('contents', None), str ):
			self.initial_data['contents'] = json.loads(self.initial_data['contents'])

		self.initial_data['files'] = [{"file":file, "usage_type":1} for file in self.\
			initial_data['files']]
		# self.initial_data['files'] = [{"file"}]
		return super().is_valid(*args, **kwargs)

	def create(self, validated_data):
		ai_user = self.context["request"].user
		project_jobs_set = validated_data.pop("project_jobs_set")
		project_files_set = validated_data.pop("project_files_set")
		proj_subject, proj_content_type = None, None
		if "proj_subject" in validated_data:
			proj_subject = validated_data.pop("proj_subject")
		if "proj_content_type" in validated_data:
			proj_content_type = validated_data.pop("proj_content_type")


		project = Project.objects.create(**validated_data,  ai_user=ai_user)
		[project.project_jobs_set.create(**job_data) for job_data in  project_jobs_set]
		[project.project_files_set.create(**file_data) for file_data in project_files_set]
		if proj_subject:
			[project.proj_subject.create(**sub_data) for sub_data in  proj_subject]
		if proj_content_type:
			[project.proj_content_type.create(**content_data) for content_data in \
			 proj_content_type]
		return project

class TemplangpairSerializer(serializers.ModelSerializer):
	project = serializers.CharField(required=False,source="temp_proj_langpair")
	class Meta:
		model = Templangpair
		fields = ( "project","source_language", "target_language")

class TempFileSerializer(serializers.ModelSerializer):
	project = serializers.CharField(required=False,source="temp_proj_file")
	class Meta:
		model = TempFiles
		fields = ("project", "files")


class TempProjectSetupSerializer(serializers.ModelSerializer):
	mt_engine_id = serializers.PrimaryKeyRelatedField(queryset=AilaysaSupportedMtpeEngines.objects.all().values_list('pk', flat=True),required=False)
	langpair = TemplangpairSerializer(many=True, source="temp_proj_langpair")
	tempfiles = TempFileSerializer(many=True, source="temp_proj_file",required=False)

	class Meta:
		model = TempProject
		fields = ( "temp_proj_id","langpair", "tempfiles",'mt_engine_id',)
		read_only_fields = ("temp_proj_id", )


	def is_valid(self, *args, **kwargs):
		print("intial-->",self.initial_data )
		source_language = json.loads(self.initial_data["source_language"])
		target_languages = json.loads(self.initial_data["target_languages"])
		self.initial_data['mt_engine_id'] = json.loads(self.initial_data.get("mt_engine","1"))
		if source_language and target_languages:
			self.initial_data['langpair'] = [{"source_language": source_language, "target_language": \
				target_language} for target_language in target_languages]
		self.initial_data['tempfiles'] = [{"files":file} for file in self.initial_data\
			['tempfiles']]
		print("Aftre intial-->",self.initial_data )
		return super().is_valid(*args, **kwargs)


	def create(self, validated_data):
		#ai_user = self.context["request"].user
		print('validated data==>',validated_data)
		langpair = validated_data.pop("temp_proj_langpair")
		tempfiles = validated_data.pop("temp_proj_file")
		temp_project = TempProject.objects.create(**validated_data)
		[temp_project.temp_proj_langpair.create(**lang_data) for lang_data in  langpair]
		[temp_project.temp_proj_file.create(**file_data) for file_data in tempfiles]
		# project.save()
		return temp_project


######################################## nandha ##########################################


class TaskSerializer(serializers.ModelSerializer):
	source_file_path = serializers.CharField(source="file.get_source_file_path", \
		read_only=True)
	output_file_path = serializers.CharField(source="file.output_file_path", read_only=True)
	source_language = serializers.CharField(source="job.source__language", read_only=True)
	target_language = serializers.CharField(source="job.target__language", read_only=True)
	document_url = serializers.URLField(source="get_document_url", read_only=True)
	filename = serializers.CharField(source="file.get_file_name", read_only=True)
	source_language_id = serializers.IntegerField(source="job.source_language.id",\
		read_only=True)
	target_language_id = serializers.IntegerField(source="job.target_language.id",\
		read_only=True)

	class Meta:
		model = Task
		fields = ("source_file_path", "source_language",
				  "target_language", "document_url","filename",
				  "file", "job",'output_file_path',
				  "source_language_id", "target_language_id", "extension", "processor_name"
				  )

		extra_kwargs = {
			"file":{"write_only": True},
			"job": {"write_only": True},
			# "version": {"write_only": True},
			# "assign_to": {"write_only": True},
		}

		validators = [
			UniqueTogetherValidator(
				queryset=Task.objects.all(),
				fields=['file', 'job']#, 'version']
			)
		]
	# def run_validation(self,data):
	# 	if self.context['request']._request.method == 'POST':
	# 		assign_to = int(self.context.get("assign_to"))
	# 		print(assign_to)
	# 		customer_id = self.context.get("customer")
	# 		print(customer_id)
	# 		if assign_to != customer_id:
	# 			vendors = AvailableVendors.objects.filter(customer_id = customer_id).values_list('vendor_id',flat = True)
	# 			if assign_to not in (list(vendors)):
	# 				raise serializers.ValidationError({"message":"This vendor is not hired vendor for customer"})
	# 	return super().run_validation(data)


	# def to_internal_value(self, data):
	# 	data["version"] = 1
	# 	data["assign_to"] = self.context.get("assign_to", None)
	# 	return super().to_internal_value(data=data)

	def to_representation(self, instance):
		representation = super().to_representation(instance)
		return representation

class TaskSerializerv2(TaskSerializer):
	class Meta(TaskSerializer.Meta):
		pass
	def to_internal_value(self, data):
		return super(TaskSerializer, self).to_internal_value(data=data)

class TmxFileSerializer(serializers.ModelSerializer):
	# serializers.FileField(man)
	is_processed = serializers.BooleanField(required=False, write_only=True)
	is_failed = serializers.BooleanField(required=False, write_only=True)

	class Meta:
		model = TmxFile
		fields = ("id", "project", "tmx_file", "is_processed", "is_failed", "filename")

	@staticmethod
	def prepare_data(data):
		if not (("project" in data) and ("tmx_files" in data)) :
			raise serializers.ValidationError("required fields missing!!!")
		project = data["project"]
		return [
			{"project": project, "tmx_file": tmx_file} for tmx_file in data["tmx_files"]
		]

class PentmWriteSerializer(serializers.ModelSerializer):
	penseive_tm_write_path = serializers.CharField(source="pentm_path", read_only=True)
	tmx_data = serializers.JSONField(source="tmx_files_path_not_processed", read_only=True)

	class Meta:
		model = Project
		fields = (
			"source_language_code", "target_language_codes",
			"penseive_tm_write_path", "tmx_data",
		)
class TbxUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tbxfiles
        fields = "__all__"


# class TbxTemplateUploadSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = TbxTemplateUploadFiles
#         fields = "__all__"

# class TaskSerializer(serializers.ModelSerializer):
# 	source_file_path = serializers.SerializerMethodField("get_source_file_path")
# 	source_language = serializers.SerializerMethodField("get_source_language")
# 	target_language = serializers.SerializerMethodField("get_target_language")
# 	class Meta:
# 		model = Task
# 		fields = ("source_file_path", "source_language",
# 				  "target_language")
#
# 	def get_source_file_path(self, obj):
# 		# print(obj.file.path)
# 		return obj.file.file.path
#
# 	def get_source_language(self, obj):
# 		return (obj.job.source_language.locale.first().locale_code)
#
# 	def get_target_language(self, obj):
# 		return (obj.job.target_language.locale.first().locale_code)
#
# 	def to_representation(self, instance):
# 		representation = super().to_representation(instance)
# 		representation["extension"] = get_file_extension(instance.file.file.path)
# 		representation["processor_name"] = get_processor_name(instance.file.file.path)\
# 											.get("processor_name", None)
# 		return representation
#  {'source_file_path': '/home/langscape/Documents/ailaysa_github/Ai_TMS/media/u98163/u98163p2/source/test1.txt', 'source_language': 'af', 'target_language': 'hy', 'extension': '.txt', 'processor_name': 'plain-text-processor'}
######################################## nandha ##########################################
class ProjectFilesCreateTypeSerializer(serializers.ModelSerializer):
	class Meta:
		model = ProjectFilesCreateType
		fields = ("id","file_create_type", "project")
		read_only_fields = ("id","project",)



class ProjectQuickSetupSerializer(serializers.ModelSerializer):
	jobs = JobSerializer(many=True, source="project_jobs_set", write_only=True)
	files = FileSerializer(many=True, source="project_files_set", write_only=True)
	voice_proj_detail = VoiceProjectDetailSerializer(required=False,allow_null=True)
	project_name = serializers.CharField(required=False,allow_null=True)
	team_exist = serializers.BooleanField(required=False,allow_null=True, write_only=True)
	workflow_id = serializers.PrimaryKeyRelatedField(queryset=Workflows.objects.all().values_list('pk', flat=True),required=False,allow_null=True, write_only=True)
	mt_engine_id = serializers.PrimaryKeyRelatedField(queryset=AilaysaSupportedMtpeEngines.objects.all().values_list('pk', flat=True),required=False,allow_null=True,write_only=True)
	assign_enable = serializers.SerializerMethodField(method_name='check_role')
	project_type_id = serializers.PrimaryKeyRelatedField(queryset=ProjectType.objects.all().values_list('pk',flat=True),required=False)
	project_analysis = serializers.SerializerMethodField(method_name='get_project_analysis')
	subjects =ProjectSubjectSerializer(many=True, source="proj_subject",required=False,write_only=True)
	contents =ProjectContentTypeSerializer(many=True, source="proj_content_type",required=False,write_only=True)
	steps = ProjectStepsSerializer(many=True,source="proj_steps",required=False)#,write_only=True)
	project_deadline = serializers.DateTimeField(required=False,allow_null=True,write_only=True)
	mt_enable = serializers.BooleanField(required=False,allow_null=True)
	project_type_id = serializers.PrimaryKeyRelatedField(queryset=ProjectType.objects.all().values_list('pk',flat=True),required=False,write_only=True)
	pre_translate = serializers.BooleanField(required=False,allow_null=True)
	copy_paste_enable = serializers.BooleanField(required=False,allow_null=True)
	from_text = serializers.BooleanField(required=False,allow_null=True,write_only=True)
	file_create_type = serializers.CharField(read_only=True,
			source="project_file_create_type.file_create_type")
	#subjects =ProjectSubjectSerializer(many=True, source="proj_subject",required=False,write_only=True)

	class Meta:
		model = Project
		fields = ("id", "project_name","assigned", "jobs","clone_available","assign_enable","files",
		 			"progress", "tasks_count", "show_analysis","project_analysis", "is_proj_analysed","get_project_type",\
					"project_deadline","pre_translate","copy_paste_enable","workflow_id","team_exist","mt_engine_id",\
					"project_type_id","voice_proj_detail","steps","contents",'file_create_type',"subjects","created_at",\
					"mt_enable","from_text",'get_assignable_tasks_exists',)#"files_count", "files_jobs_choice_url","text_to_speech_source_download",
	
		# extra_kwargs = {
		# 	"subjects": {"write_only": True},
		# 	"contents": {"write_only": True},
		# 	"project_deadline": {'write_only': True},
		# 	"mt_engine_id": {'write_only': True},
		# 	"from_text" : {'write_only' : True},
		# 	"steps" : {'write_only' : True},
		# 	"mt_enable" : {'write_only' : True},
		# }



	def run_validation(self,data):
		if self.context.get("request")!=None and self.context['request']._request.method == 'POST':
				pt = json.loads(data.get('project_type')[0]) if data.get('project_type') else 1
				if pt not in [4 ,3] and data.get('target_languages')==None:
						raise serializers.ValidationError({"msg":"target languages needed for translation project"})
		if data.get('target_languages')!=None:
			comparisons = [source == target for (source, target) in itertools.
				product(data['source_language'],data['target_languages'])]
			if True in comparisons:
				raise serializers.ValidationError({"msg":"source and target "
					"languages should not be same"})
		return super().run_validation(data)

	def to_internal_value(self, data):

		#print("Internal value ===> ", data)
		data["project_type_id"] = data.get("project_type",[1])[0]
		data["project_name"] = data.get("project_name", [None])[0]
		data["project_deadline"] = data.get("project_deadline",[None])[0]
		data['mt_engine_id'] = data.get('mt_engine',[1])[0]
		data['mt_enable'] = data.get('mt_enable',['true'])[0]
		data['copy_paste_enable'] = data.get('copy_paste_enable',['true'])[0]

		data["jobs"] = [{"source_language": data.get("source_language", [None])[0], "target_language":\
			target_language} for target_language in data.get("target_languages", [])]
		data['team_exist'] = data.get('team',[None])[0]

		if data.get('subjects'):
			data["subjects"] = [{"subject":sub} for sub in data.get('subjects',[])]

		if data.get("contents"):
			data["contents"]=[{"content_type":cont} for cont in data.get('contents',[])]

		data["steps"] = [{"steps":step} for step in data.get('steps',[])] if data.get('steps') else [{"steps":1}]

		if data.get('sub_category'):
			data["voice_proj_detail"] = {"source_language": data.get("source_language", [None])[0],\
										"project_type_sub_category":data.get("sub_category",[None])[0]}

		if data.get('audio_file'):
		 	data['files'] = [{"file": file, "usage_type": 1} for file in data.get('audio_file', [])]
		else:
			data['files'] = [{"file": file, "usage_type": 1} for file in data.pop('files', [])]

		if self.context.get("request")!=None and self.context['request']._request.method == 'POST':
			data["jobs"] = [{"source_language": data.get("source_language", [None])[0], "target_language":\
				target_language} for target_language in data.get("target_languages", [None])]
			data['pre_translate'] = data.get('pre_translate',['false'])[0]
			data['from_text'] =  data.get('from_text',[0])[0]

		else:
			data["jobs"] = [{"source_language": data.get("source_language", [None])[0], "target_language":\
				target_language} for target_language in data.get("target_languages", [])]
			if data.get('pre_translate'):
				data['pre_translate'] = data.get('pre_translate')[0]

		data['mt_engine_id'] = data.get('mt_engine',[1])[0]
		return super().to_internal_value(data=data)

	def get_project_analysis(self,instance):
		user = self.context.get("request").user if self.context.get("request")!=None else self\
			.context.get("ai_user", None)

		user_1 = user.team.owner if user.team else user

		if instance.ai_user == user:
			tasks = instance.get_tasks
		elif instance.team:
			if ((instance.team.owner == user)|(user in instance.team.get_project_manager)):
				tasks = instance.get_tasks
			else:
				tasks = [task for job in instance.project_jobs_set.all() for task \
						in job.job_tasks_set.all() for task_assign in task.task_info.filter(assign_to_id = user_1)]

		else:
			tasks = [task for job in instance.project_jobs_set.all() for task \
					in job.job_tasks_set.all() for task_assign in task.task_info.filter(assign_to_id = user_1)]

		res = instance.project_analysis(tasks)
		return res

	def check_role(self, instance):
		if self.context.get("request")!=None:
			user = self.context.get("request").user
		else:user = self.context.get("ai_user", None)
		if instance.team :
			return True if ((instance.team.owner == user)\
				or(instance.team.internal_member_team_info.all().\
				filter(Q(internal_member_id = user.id) & Q(role_id=1)))\
				or(instance.team.owner.user_info.all()\
				.filter(Q(hired_editor_id = user.id) & Q(role_id=1))))\
				else False
		else:
			return True if ((instance.ai_user == user) or\
			(instance.ai_user.user_info.all().filter(Q(hired_editor_id = user.id) & Q(role_id=1))))\
			else False


	def create(self, validated_data):
		print("Validated data ===> ", validated_data)

		if self.context.get("request")!=None:
			created_by = self.context.get("request", None).user
			create_type = validated_data.pop('from_text',None)
			user = created_by
		else:
			created_by = self.context.get("ai_user", None)
			create_type = True
			user = created_by
		if created_by.team:ai_user = created_by.team.owner
		else:ai_user = created_by
		team = created_by.team if created_by.team else None
		project_manager = created_by
		voice_proj_detail = validated_data.pop("voice_proj_detail",[])
		validated_data.pop('team_exist')
		# print("validated_data---->",validated_data)
		project_type = validated_data.get("project_type_id")
		proj_subject = validated_data.pop("proj_subject",[])
		proj_steps = validated_data.pop("proj_steps",[])
		proj_content_type = validated_data.pop("proj_content_type",[])
		try:
			with transaction.atomic():
				project, files, jobs = Project.objects.create_and_jobs_files_bulk_create(
					validated_data, files_key="project_files_set", jobs_key="project_jobs_set", \
					f_klass=File,j_klass=Job, ai_user=ai_user,\
					team=team,project_manager=project_manager,created_by=created_by)#,team=team,project_manager=project_manager)
				obj_is_allowed(project,"create",user)
				# print("files---",files[0].id)
				objls_is_allowed(files,"create",user)
				objls_is_allowed(jobs,"create",user)
				if ((create_type == True) and ((project_type == 1) or (project_type == 2))):
					pro_fil = ProjectFilesCreateType.objects.create(project=project,file_create_type=ProjectFilesCreateType.FileType.from_text)
					obj_is_allowed(pro_fil,"create",user)
				else:
					pro_fil = ProjectFilesCreateType.objects.create(project=project)
					obj_is_allowed(pro_fil,"create",user)
				if proj_subject:
					proj_subj_ls = [project.proj_subject.create(**sub_data) for sub_data in  proj_subject]
					objls_is_allowed(proj_subj_ls,"create",user)
				if proj_content_type:
					proj_content_ls = [project.proj_content_type.create(**content_data) for content_data in proj_content_type]
					objls_is_allowed(proj_content_ls,"create",user)
				if proj_steps:
					proj_steps_ls = [project.proj_steps.create(**steps_data) for steps_data in proj_steps]
					objls_is_allowed(proj_steps_ls,"create",user)

				if project_type == 1 or project_type == 2 or project_type == 5:
					tasks = Task.objects.create_tasks_of_files_and_jobs(
						files=files, jobs=jobs, project=project,klass=Task)  # For self assign quick setup run)
					objls_is_allowed(tasks,"create",user)
				if voice_proj_detail:
					voice_project = VoiceProjectDetail.objects.create(**voice_proj_detail,project=project)
					if voice_project.project_type_sub_category.id == 1 or 2 : #1--->speech-to-text #2--->text-to-speech
						rr = voice_project.project.project_jobs_set.filter(~Q(target_language = None))
						if voice_project.project_type_sub_category.id == 2 and rr:
							tasks = Task.objects.create_tasks_of_files_and_jobs(
								files=files, jobs=jobs, project=project, klass=Task)
							objls_is_allowed(tasks,"create",user)
						else:
							tasks = Task.objects.create_tasks_of_audio_files(files=files,jobs=jobs,project=project, klass=Task)
							objls_is_allowed(tasks,"create",user)
				if project_type == 5:
					ex = [ExpressProjectDetail.objects.create(task = i[0]) for i in tasks]
				# tasks = Task.objects.create_tasks_of_files_and_jobs(
				# 	files=files, jobs=jobs, project=project, klass=Task)
				task_assign = TaskAssign.objects.assign_task(project=project)
				objls_is_allowed(task_assign,"create",user)
				#tt = mt_only(project,self.context.get('request'))
				#print(tt)
		except BaseException as e:
			print("Exception---------->",e)
			logger.warning(f"project creation failed {user.uid} : {str(e)}")
			raise serializers.ValidationError({"error": f"project creation failed {user.uid}"})
		return  project

	def update(self, instance, validated_data):#No update for project_type
		print("DATA---->",validated_data)
		if validated_data.get('project_name'):
			instance.project_name = validated_data.get("project_name",\
									instance.project_name)
			instance.save()

		if validated_data.get('mt_engine_id'):
			instance.mt_engine_id = validated_data.get("mt_engine_id",\
									instance.mt_engine_id)
			instance.save()

		if 'mt_enable' in validated_data:
			instance.mt_enable = validated_data.get("mt_enable",\
									instance.mt_enable)
			instance.save()

		if 'copy_paste_enable' in validated_data:
			instance.copy_paste_enable = validated_data.get("copy_paste_enable",\
									instance.copy_paste_enable)
			instance.save()

		if validated_data.get('project_deadline'):
			instance.project_deadline = validated_data.get("project_deadline",\
									instance.project_deadline)
			instance.save()

		if 'team_exist' in validated_data:
			if validated_data.get('team_exist') == False:
				instance.team_id = None  
			else:
				try:instance.ai_user.team.id
				except: instance.team_id = None
			instance.save()

		if validated_data.get('project_manager_id'):
			instance.project_manager_id = validated_data.get('project_manager_id')
			instance.save()

		if 'pre_translate' in validated_data:##################Need to check this mt-only edit option#######
			instance.pre_translate = validated_data.get("pre_translate",\
									instance.pre_translate)
			instance.save()

		files_data = validated_data.pop("project_files_set")
		jobs_data = validated_data.pop("project_jobs_set")
		project_type = instance.project_type_id

		with transaction.atomic():
			project, files, jobs = Project.objects.create_and_jobs_files_bulk_create_for_project(instance,\
									files_data, jobs_data, f_klass=File, j_klass=Job)
			try:
				if instance.voice_proj_detail.project_type_sub_category_id == 1 or 2: #1--->speech-to-text #2--->text-to-speech
						tasks = Task.objects.create_tasks_of_audio_files_by_project(project=project)
			except:
				tasks = Task.objects.create_tasks_of_files_and_jobs_by_project(\
					project=project)

		contents_data = validated_data.pop("proj_content_type",[])
		subjects_data = validated_data.pop("proj_subject",[])
		steps_data = validated_data.pop("proj_steps",[])

		project,contents,subjects,steps = Project.objects.create_content_and_subject_and_steps_for_project(instance,\
							contents_data, subjects_data, steps_data,\
							c_klass=ProjectContentType, s_klass = ProjectSubjectField, step_klass = ProjectSteps)

		if project_type == 1 or project_type == 2 or project_type == 5:
			tasks = Task.objects.create_tasks_of_files_and_jobs_by_project(\
					project=project)
		if project_type == 3:
			tasks = Task.objects.create_glossary_tasks_of_jobs_by_project(\
			        project = instance)

		if project_type == 5:
			ex = [ExpressProjectDetail.objects.get_or_create(task = i[0]) for i in tasks]

		task_assign = TaskAssign.objects.assign_task(project=project)

		return  project

	# def to_representation(self, value):
	# 	from ai_glex.serializers import GlossarySerializer
	# 	from ai_glex.models import Glossary
	# 	data = super().to_representation(value)
	# 	try:
	# 		ins = Glossary.objects.get(project_id = value.id)
	# 		print(ins)
	# 		glossary_serializer = GlossarySerializer(ins)
	# 		data['glossary'] = glossary_serializer.data
	# 	except:
	# 		data['glossary'] = None
	# 	return data


class InstructionfilesSerializer(serializers.ModelSerializer):
	instruction_file = serializers.FileField(allow_null=True,validators=[file_size])
	class Meta:
		model = Instructionfiles
		fields = "__all__"
        
class MyDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = MyDocuments
        fields = "__all__"

class WriterProjectSerializer(serializers.ModelSerializer):
	related_docs = MyDocumentSerializer(required=False,many=True)
	class Meta:
		model = WriterProject
		fields = ('id','proj_name','ai_user','created_at','updated_at','related_docs',)

class TaskAssignSerializer(serializers.ModelSerializer):
	task_info = TaskSerializer(required=False,many=True)
	# step = serializers.PrimaryKeyRelatedField(queryset=Steps.objects.all().values_list('pk', flat=True),required=False)
	class Meta:
		model = TaskAssign
		fields =('task_info','step','assign_to','mt_enable','complaint_reason',
				'mt_engine','pre_translate','copy_paste_enable','status',
				'client_response','client_reason','user_who_approved_or_rejected')

class TaskAssignInfoNewSerializer(serializers.ModelSerializer):
	task_assign_info = TaskAssignSerializer(required=False)
	class Meta:
		model = TaskAssignInfo
		fields = ('instruction','assignment_id','deadline','mtpe_rate','estimated_hours','mtpe_count_unit','total_word_count','currency',\
				  'assigned_by','task_assign_info','task_ven_status','account_raw_count','billable_char_count','billable_word_count',)

####################Need to change################################

class TaskAssignInfoSerializer(serializers.ModelSerializer):
    assign_to=serializers.PrimaryKeyRelatedField(queryset=AiUser.objects.all().values_list('pk', flat=True),required=False,write_only=True)
    tasks = serializers.ListField(required=False)
    step = serializers.PrimaryKeyRelatedField(queryset=Steps.objects.all().values_list('pk', flat=True),required=False,write_only=True)
    assign_to_details = serializers.SerializerMethodField()
    assigned_by_details = serializers.SerializerMethodField()
    job = serializers.ReadOnlyField(source='task_assign.task.job.id')
    project = serializers.ReadOnlyField(source='task_assign.task.job.project.id')
    task_assign_detail = serializers.SerializerMethodField()
    files = InstructionfilesSerializer(many=True,required=False)
    instruction_files = serializers.SerializerMethodField()
    mt_engine_id = serializers.PrimaryKeyRelatedField(queryset=AilaysaSupportedMtpeEngines.objects.all().values_list('pk', flat=True),required=False)
    mt_enable = serializers.BooleanField(required=False,allow_null=True,write_only=True)
    pre_translate = serializers.BooleanField(required=False,allow_null=True,write_only=True)
    reassigned = serializers.BooleanField(required=False,allow_null=True,write_only=True)


    class Meta:
        model = TaskAssignInfo
        fields = ('id','instruction','instruction_files','step','task_ven_status','change_request_reason','reassigned',\
                   'job','project','assigned_by','assignment_id','mt_engine_id','deadline','created_at',\
                   'assign_to','tasks','mtpe_rate','estimated_hours','mtpe_count_unit','currency','files',\
                    'total_word_count','assign_to_details','assigned_by_details','payment_type', 'mt_enable',\
                    'pre_translate','task_assign_detail','account_raw_count','billable_char_count','billable_word_count',)

        extra_kwargs = {
            'assigned_by':{'write_only':True},
            # 'assign_to':{'write_only':True}
             }

    def get_assign_to_details(self,instance):
        if instance.task_assign.assign_to:
            deleted = True if 'deleted' in instance.task_assign.assign_to.email else False
            external_editor = True if instance.task_assign.assign_to.is_internal_member==False else False
            email = instance.task_assign.assign_to.email if instance.task_assign.assign_to.is_internal_member==True else None
            managers = [i.id for i in instance.task_assign.assign_to.team.get_project_manager] if external_editor and instance.task_assign.assign_to.team and instance.task_assign.assign_to.team.owner.is_agency else []
            try:avatar = instance.task_assign.assign_to.professional_identity_info.avatar_url
            except:avatar = None
            return {"id":instance.task_assign.assign_to_id,"managers":managers,"name":instance.task_assign.assign_to.fullname,"email":email,"avatar":avatar,"external_editor":external_editor,"account_deleted":deleted}
	    #if instance.task.assign_to:
	    #    external_editor = True if instance.task.assign_to.is_internal_member==False else False
	    #    email = instance.task.assign_to.email if instance.task.assign_to.is_internal_member==True else None
	    #    try:avatar = instance.task.assign_to.professional_identity_info.avatar_url
	    #    except:avatar = None
	    #    return {"id":instance.task.assign_to_id,"name":instance.task.assign_to.fullname,"email":email,"avatar":avatar,"external_editor":external_editor}

    def get_assigned_by_details(self,instance):
        if instance.assigned_by:
            return {"id":instance.assigned_by_id,"name":instance.assigned_by.fullname,"email":instance.assigned_by.email}

    def get_instruction_files(self,instance):
        files = []
        queryset = instance.task_assign_instruction_file.all()
        for obj in queryset:
            files.append({'id':obj.id,'filename':obj.filename})
        return files

    def get_task_assign_detail(self,instance):
        step = instance.task_assign.step.id
        mt_enable = instance.task_assign.mt_enable
        pre_translate = instance.task_assign.pre_translate
        copy_paste_enable = instance.task_assign.copy_paste_enable
        task_status = instance.task_assign.get_status_display()
        client_response = instance.task_assign.get_client_response_display() if instance.task_assign.client_response else None
        count = TaskAssignInfo.objects.filter(task_assign__task= instance.task_assign.task).count()
        print("Count-------------->",count)
        if count == 1:
            can_open = True
        else:
	        if instance.task_assign.step_id == 1:
	            try:
	                #print("$$$$$$$$$",TaskAssign.objects.filter(task = instance.task_assign.task).filter(step_id=2).first().status)
	                if TaskAssign.objects.filter(task = instance.task_assign.task).filter(step_id=2).first().status == 2:
	                    can_open = False
	                else:can_open = True
	            except:can_open = True
	        elif instance.task_assign.step_id == 2:
	            if TaskAssign.objects.filter(task = instance.task_assign.task).filter(step_id=1).first().status == 3:
	                can_open = True
	            else:can_open = False
        return {'step':step,'mt_enable':mt_enable,'pre_translate':pre_translate,'task_status':task_status,"client_response":client_response,"can_open":can_open}

    def run_validation(self, data):
        if data.get('assign_to'):
           data["assign_to"] = json.loads(data["assign_to"])
        if data.get('step'):
           data["step"] = json.loads(data["step"])
        if data.get('mt_engine'):
           data['mt_engine_id'] = json.loads(data['mt_engine'])
        if data.get('mt_enable'):
           data['mt_enable'] = json.loads(data['mt_enable'])
        if data.get('reassigned'):
           data['reassigned'] = json.loads(data['reassigned'])
        if data.get('pre_translate'):
           data['pre_translate'] = json.loads(data['pre_translate'])
        # if data.get('tasks'): #and self.context['request']._request.method=='POST':
        #    print("tasks------>",data['tasks']) 
        #    print("type-------->",[type(i) for i in data['tasks']])
        #    data['tasks'] = [task for task in data.pop('tasks',[])]
        if data.get('files'):
           data['files'] = [{'instruction_file':file} for file in data['files']]
        data['assigned_by'] = self.context['request'].user.id
        print("validated data run validation----->",data)
        return super().run_validation(data)


    def create(self, data):
        from ai_tm.api_views import get_weighted_char_count,get_weighted_word_count
        print('validated data==>',data)
        task_list = data.pop('tasks')
        step = data.pop('step')
        assign_to = data.pop('assign_to')
        files = data.pop('files')
        project = Task.objects.get(id=task_list[0]).job.project
        mt_engine_id = data.pop('mt_engine_id',None)
        mt_enable = data.pop('mt_enable',None)
        reassigned = data.pop('reassigned',False)
        print("reassigned----->",reassigned)
        user1 = AiUser.objects.get(id=assign_to)
        pre_translate = data.pop('pre_translate',None)
        with transaction.atomic():
            if reassigned:
                print("Inside if")
                task_assigns = [TaskAssign.objects.get_or_create(task_id = task,step_id = step,reassigned=True,\
								defaults = {"status":1,"mt_engine_id":project.mt_engine_id,\
                         "mt_enable":project.mt_enable,"pre_translate":project.pre_translate,'copy_paste_enable':project.copy_paste_enable}) for task in task_list]
                task_assign_list = [t[0] for t in task_assigns]
            else:
                print("inside else")
                task_assign_list = [TaskAssign.objects.get(Q(task_id = task) & Q(step_id = step) & Q(reassigned = reassigned)) for task in task_list]
            print('task_assign_list--------->',task_assign_list)
            task_assign_info = [TaskAssignInfo.objects.create(**data,task_assign = task_assign ) for task_assign in task_assign_list]
            #objls_is_allowed(task_assign_info,"create",self.context.get('request').user)
            for i in task_assign_info:
                try:total_word_count = i.task_assign.task.document.total_word_count
                except:
                    try:total_word_count = i.task_assign.task.task_details.first().task_word_count
                    except:total_word_count=None
                # billable_word_count = get_weighted_word_count(i.task_assign.task)
                # billable_char_count = get_weighted_char_count(i.task_assign.task)
                TaskAssignInfo.objects.filter(id=i.id).update(total_word_count = total_word_count)#,billable_char_count=billable_char_count,billable_word_count=billable_word_count)
            tt = [Instructionfiles.objects.create(**instruction_file,task_assign_info = assign) for instruction_file in files for assign in task_assign_info]
            task_assign_data = [TaskAssign.objects.filter(Q(task_id = task) & Q(step_id = step) & Q(reassigned = reassigned)).update(assign_to_id = assign_to) for task in task_list]
            print("Task Assign-------->",[TaskAssign.objects.filter(Q(task_id = task) & Q(step_id = step) & Q(reassigned = reassigned)).first().assign_to for task in task_list])
            if mt_engine_id or mt_enable or pre_translate:
                [TaskAssign.objects.filter(Q(task_id = task) & Q(step_id = step) & Q(reassigned = reassigned)).update(mt_engine_id=mt_engine_id,mt_enable=mt_enable,pre_translate=pre_translate) for task in task_list]
        if user1.is_internal_member == False:
          print("task_assing id",[i.task_assign.assign_to for i in task_assign_info])
          generate_client_po([i.id for i in task_assign_info])
        else:
          task_assing_role_ls([i.id for i in task_assign_info])
        return task_assign_info


    # def update(self,instance,data):
    #     print("DATA-------->",data)
    #     if 'assign_to' in data:
    #         task = Task.objects.get(id = instance.task_id)
    #         segment_count=0 if task.document == None else task.get_progress.get('confirmed_segments')
    #         task_info = Task.objects.filter(id = instance.task_id).update(assign_to = data.get('assign_to'))
    #         task_history = TaskAssignHistory.objects.create(task_id =instance.task_id,previous_assign_id=task.assign_to_id,task_segment_confirmed=segment_count,unassigned_by=self.context.get('request').user)
    #         instance.task_ven_status = None
    #         instance.save()
    #     if 'task_ven_status' in data:
    #         ws_forms.task_assign_ven_status_mail(instance.task,instance.task_ven_status)
    #     if 'mtpe_rate' in data or 'mtpe_count_unit' in data or 'currency' in data:
    #         if instance.task_ven_status == 'change_request':
    #             instance.task_ven_status = None
    #             instance.save()
    #         elif instance.task_ven_status == 'task_accepted':
    #             raise serializers.ValidationError("Rates Can't be changed..Vendor already accepted rates and started working!!!")
    #     return super().update(instance, data)


    # def to_representation(self, instance):
    #     data = super().to_representation(instance)
    #     print(instance)
    #     data["assign_to"] = instance.task.assign_to.id
    #     # data['assigned_by'] = instance.task.job.project.ai_user.fullname
    #     return data


class VendorDashBoardSerializer(serializers.ModelSerializer):
	filename = serializers.CharField(read_only=True, source="file.filename")
	source_language = serializers.CharField(read_only=True, source=\
		"job.source_language.id")
	target_language = serializers.CharField(read_only=True, source=\
		"job.target_language.id")
	project_name = serializers.CharField(read_only=True, source=\
		"file.project.project_name")
	document_url = serializers.CharField(read_only=True, source="get_document_url")
	progress = serializers.DictField(source="get_progress", read_only=True)
	#task_assign_info = TaskAssignInfoSerializer(required=False)
	task_assign_info = serializers.SerializerMethodField(source = "get_task_assign_info")
	task_reassign_info = serializers.SerializerMethodField(source = "get_task_reassign_info")
	#task_self_assign_info = serializers.SerializerMethodField()
	bid_job_detail_info = serializers.SerializerMethodField()
	open_in =  serializers.SerializerMethodField()
	transcribed = serializers.SerializerMethodField()
	text_to_speech_convert_enable = serializers.SerializerMethodField()
	converted = serializers.SerializerMethodField()
	is_task_translated = serializers.SerializerMethodField()
	mt_only_credit_check = serializers.SerializerMethodField()
	# can_open = serializers.SerializerMethodField()
	# task_word_count = serializers.SerializerMethodField(source = "get_task_word_count")
	# task_word_count = serializers.IntegerField(read_only=True, source ="task_details.first().task_word_count")
	# assigned_to = serializers.SerializerMethodField(source='get_assigned_to')

	class Meta:
		model = Task
		fields = \
			("id", "filename",'job','document',"download_audio_source_file","mt_only_credit_check", "transcribed", "text_to_speech_convert_enable","ai_taskid", "source_language", "target_language", "task_word_count","task_char_count","project_name",\
			"document_url", "progress","task_assign_info","task_reassign_info","bid_job_detail_info","open_in","assignable","first_time_open",'converted','is_task_translated',)

	def get_converted(self,obj):
		if obj.job.project.project_type_id == 4 :
				if  obj.job.project.voice_proj_detail.project_type_sub_category_id == 1:
					if obj.task_transcript_details.filter(~Q(transcripted_text__isnull = True)).exists():
						return True
					else:return False
				elif  obj.job.project.voice_proj_detail.project_type_sub_category_id == 2:
					if obj.job.target_language==None:
						if obj.task_transcript_details.exists():
							return True
						else:return False
					else:return None
				else:return None
		elif obj.job.project.project_type_id == 1 or obj.job.project.project_type_id == 2:
			if obj.job.target_language==None and os.path.splitext(obj.file.file.path)[1] == '.pdf':
				if obj.pdf_task.all().exists() == True:
					return True
				else:return False
			else:return None
		else:return None

	def get_is_task_translated(self,obj):
		if obj.job.project.project_type_id == 1 or obj.job.project.project_type_id == 2:
			if obj.job.target_language==None and os.path.splitext(obj.file.file.path)[1] == '.pdf':
				if obj.pdf_task.all().exists() == True and obj.pdf_task.first().translation_task_created == True:
					return True
				else:return False
			else:return None
		else:return None

	def get_mt_only_credit_check(self,obj):
		try:return obj.document.doc_credit_check_open_alert
		except:return None


	def get_transcribed(self,obj):
		if obj.job.project.project_type_id == 4 :
			if  obj.job.project.voice_proj_detail.project_type_sub_category_id == 1:
				if obj.task_transcript_details.filter(~Q(transcripted_text__isnull = True)).exists():
					return True
				else:return False
			else:return None
		else:return None

	def get_text_to_speech_convert_enable(self,obj):
		if obj.job.project.project_type_id == 4 :
			if  obj.job.project.voice_proj_detail.project_type_sub_category_id == 2:
				if obj.job.target_language==None:
					if obj.task_transcript_details.exists():
						return False
					else:return True
				else:return None
			else:return None
		else:return None


	def get_open_in(self,obj):
		try:
			if obj.job.project.project_type_id == 5:
				return "ExpressEditor"
			elif obj.job.project.project_type_id == 4:
				if  obj.job.project.voice_proj_detail.project_type_sub_category_id == 1:
					if obj.job.target_language==None:
						return "Ailaysa Writer or Text Editor"
					else:
						return "Transeditor"
				elif  obj.job.project.voice_proj_detail.project_type_sub_category_id == 2:
					if obj.job.target_language==None:
						return "Download"
					else:return "Transeditor"
			elif obj.job.project.project_type_id == 1 or obj.job.project.project_type_id == 2:
				if obj.job.target_language==None and os.path.splitext(obj.file.file.path)[1] == '.pdf':
					try:return obj.pdf_task.last().pdf_api_use
					except:return None
				else:return "Transeditor"	
			else:return "Transeditor"
		except:
			try:
				if obj.job.project.glossary_project:
					return "GlossaryEditor"
			except:
				return "Transeditor"

	def get_bid_job_detail_info(self,obj):
		if obj.job.project.proj_detail.all():
			qs = obj.job.project.proj_detail.last().projectpost_jobs.filter(Q(src_lang_id = obj.job.source_language.id) & Q(tar_lang_id = obj.job.target_language.id if obj.job.target_language else obj.job.source_language_id))
			return ProjectPostJobDetailSerializer(qs,many=True,context={'request':self.context.get("request")}).data
		else:
			return None


	def get_task_assign_info(self, obj):
		user = self.context.get('request').user
		task_assign = obj.task_info.filter(Q(task_assign_info__isnull=False) & Q(assign_to=user))
		if task_assign:task_assign_final= task_assign
		else:
			task_assign_final = obj.task_info.filter(Q(task_assign_info__isnull=False) & Q(reassigned=False))
		# task_assign = obj.task_info.filter(Q(task_assign_info__isnull=False) & Q(reassigned=False))
		if task_assign_final:
			task_assign_info=[]
			for i in task_assign_final:
				try:task_assign_info.append(i.task_assign_info)
				except:pass
			return TaskAssignInfoSerializer(task_assign_info,many=True).data
		else: return None

	def get_task_reassign_info(self, obj):
		user = self.context.get('request').user.team.owner if self.context.get('request').user.team else self.context.get('request').user
		project_managers = self.context.get('request').user.team.get_project_manager if self.context.get('request').user.team else []
		if user.is_agency == True:
			task_assign = obj.task_info.filter(Q(task_assign_info__isnull=False) & Q(reassigned=True))
			if task_assign:
				task_assign_info=[]
				for i in task_assign:
					try:task_assign_info.append(i.task_assign_info)
					except:pass
				return TaskAssignInfoSerializer(task_assign_info,many=True).data
			else: return None
		else:
			task_assign = obj.task_info.filter(Q(task_assign_info__isnull=False) & Q(reassigned=True))
			print("Task Assign-------->",task_assign)
			if task_assign and task_assign.filter(assign_to=user):
				return True
				# else:return None
			else: return None

	# def get_task_self_assign_info(self,obj):
	# 	user = self.context.get("request").user
	# 	task_assign = obj.task_info.filter(task_assign_info__isnull=False)
	# 	if task_assign:
	# 		for i in task_assign:
	# 			if i.step_id == 1:return None
	# 			else:
	# 				self_assign = obj.task_info.filter(task_assign_info__isnull=True).first()
	# 				print("SA------------>",self_assign)
	# 				if self_assign:
	# 					step = self_assign.step.id
	# 					mt_enable = self_assign.mt_enable
	# 					pre_translate = self_assign.pre_translate
	# 					copy_paste_enable = self_assign.copy_paste_enable
	# 					task_status = self_assign.get_status_display()
	# 					try:
	# 						if TaskAssign.objects.filter(task = self_assign.task).filter(step_id=2).first().status == 2:
	# 							can_open = False
	# 						else:can_open = True
	# 					except:can_open = True
	# 					return {'step':step,'mt_enable':mt_enable,'pre_translate':pre_translate,'task_status':task_status,"can_open":can_open}
	# 				else:return None
	# 	else:
	# 		return None

	# def get_task_word_count(self,instance):
	# 	if instance.document_id:
	# 		document = Document.objects.get(id = instance.document_id)
	# 		return document.total_word_count
	# 	else:
	# 		t = TaskDetails.objects.get(task_id = instance.id)
	# 		return t.task_word_count


class ProjectSerializerV2(serializers.ModelSerializer):
	class Meta:
		model = Project
		fields = ("threshold", "max_hits", "id")

class ReferenceFileSerializer(serializers.ModelSerializer):
	class Meta:
		model = ReferenceFiles
		fields = ("project", "ref_files", "filename", "id")
		extra_kwargs = {
			"ref_files": {"write_only": True}
		}

class TbxFileSerializer(serializers.ModelSerializer):

	class Meta:
	    model = TbxFile
	    fields = ("id", "project", "tbx_file", "job", "filename")

	def save_update(self):
	    return super().save()

	@staticmethod
	def prepare_data(data):
		if not (("project_id" in data) and ("tbx_file" in data)) :
			raise serializers.ValidationError("Required fields missing!!!")
		project = data["project_id"]
		job = data.get("job_id", None)
		#tbx_file = data.get("tbx_file")
		return [{"project": project, "job": job, "tbx_file": tbx_file} for tbx_file in data['tbx_file']]

	# @staticmethod
	# def prepare_data(data):
	# 	if not (("project" in data) and ("tmx_files" in data)) :
	# 		raise serializers.ValidationError("required fields missing!!!")
	# 	project = data["project"]
	# 	return [
	# 		{"project": project, "tmx_file": tmx_file} for tmx_file in data["tmx_files"]
	# 	]

class TbxTemplateSerializer(serializers.ModelSerializer):

    class Meta:
        model = TbxTemplateFiles
        fields = ("id", "project", "job", "tbx_template_file")

    @staticmethod
    def prepare_data(data):
        if not (("project_id" in data) and ("job_id" in data) and ("tbx_template_file" in data)):
            raise serializers.ValidationError("Required fields missing!!!")
        project = data["project_id"]
        job = data.get("job_id")
        tbx_template_file = data.get("tbx_template_file")
        return {"project": project, "job": job, "tbx_template_file": tbx_template_file}

class TaskCreditStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskCreditStatus
        fields = "__all__"


class TaskDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskDetails
        fields = "__all__"

class TaskTranscriptDetailSerializer(serializers.ModelSerializer):
    project_name = serializers.ReadOnlyField(source ='task.job.project.project_name')
    source_lang = serializers.SerializerMethodField()
    punctuation_support = serializers.SerializerMethodField()
    transcription_source_file = serializers.SerializerMethodField()
    class Meta:
        model = TaskTranscriptDetails
        fields = "__all__"
        #fields = ('id','quill_data','transcripted_text','writer_filename','writer_edited_count')
        write_only_fields = ("project_name",'source_lang',"source_audio_file", "translated_audio_file","transcripted_file_writer",\
							"audio_file_length","user","created_at","updated_at","punctuation_support","transcription_source_file",)
        #read_only_fields = ("id","task",)
    def get_source_lang(self,obj):
        return obj.task.job.project.project_jobs_set.first().source_language.language

    def get_transcription_source_file(self,obj):
	    return obj.task.file.file.url

    def get_punctuation_support(self,obj):
       lang = obj.task.job.project.project_jobs_set.first().source_language
       locale = [i.id for i in lang.locale.all()]
       #print("Locale--------------->",locale)
       sp = TranscribeSupportedPunctuation.objects.filter(language_locale__in = locale)
       return True if sp else False

class ProjectListSerializer(serializers.ModelSerializer):
	jobs = serializers.SerializerMethodField()
	assignable = serializers.SerializerMethodField()

	class Meta:
		model = Project
		fields = ("id", "project_name","jobs","assignable",)

	def get_jobs(self,obj):
		source_lang = obj.project_jobs_set.first().source_language_id
		target_lang = [i.target_language_id for i in obj.project_jobs_set.exclude(target_language=None)]
		return {'source':source_lang,'target':target_lang}

	def get_assignable(self, data):
		data_1 = data.get_assignable_tasks_exists
		if data_1: return True
		else: return False

	


class VendorLanguagePairOnlySerializer(serializers.ModelSerializer):
	source_lang = serializers.ReadOnlyField(source = 'source_lang.language')
	target_lang = serializers.ReadOnlyField(source = 'target_lang.language')
	# currency = serializers.ReadOnlyField(source = 'currency.currency_code')
	class Meta:
		model = VendorLanguagePair
		fields = ('source_lang','target_lang',)#'currency',)

class HiredEditorDetailSerializer(serializers.Serializer):
	name = serializers.ReadOnlyField(source='hired_editor.fullname')
	id = serializers.ReadOnlyField(source='hired_editor_id')
	obj_id = serializers.ReadOnlyField(source='id')
	#is_agency = serializers.ReadOnlyField(source='hired_editor.is_agency')
	status = serializers.ReadOnlyField(source='get_status_display')
	avatar= serializers.ReadOnlyField(source='hired_editor.professional_identity_info.avatar_url')
	vendor_lang_pair = serializers.SerializerMethodField()
	#suggestions = serializers.SerializerMethodField()

	# def get_suggestions(self,obj):
	# 	request = self.context['request']
	# 	#job_ids= request.query_params.getlist('job')
	# 	project_id= request.query_params.get('project')
	# 	proj = Project.objects.get(id = project_id)
	# 	jobs = proj.get_jobs
	# 	lang_pair = VendorLanguagePair.objects.none()
	# 	for i in jobs:
			# if i.target_language_id == None:
			# 	tr = VendorLanguagePair.objects.filter(Q(target_lang_id=i.source_language_id) & Q(user_id = obj.hired_editor_id) &Q(deleted_at=None)).distinct('user')
			# else:
			# 	tr = VendorLanguagePair.objects.filter(Q(source_lang_id=i.source_language_id) & Q(target_lang_id=i.target_language_id) & Q(user_id = obj.hired_editor_id) &Q(deleted_at=None)).distinct('user')
			# print("Tr------------>",tr)
	# 		lang_pair = lang_pair.union(tr)
	# 	print("langpair----------------->",lang_pair)
	# 	return VendorLanguagePairOnlySerializer(lang_pair, many=True, read_only=True).data


	def get_vendor_lang_pair(self,obj):
		request = self.context['request']
		job_ids= request.query_params.getlist('job')
		project_id= request.query_params.get('project')
		proj = Project.objects.get(id = project_id)
		jobs = Job.objects.filter(id__in = job_ids) if job_ids else proj.get_jobs
		lang_pair = VendorLanguagePair.objects.none()
		condition_satisfied = True
		for i in jobs:
			print(i.source_language_id,i.target_language_id)
			if i.target_language_id == None:
				tr = VendorLanguagePair.objects.filter(Q(target_lang_id=i.source_language_id) & Q(user_id = obj.hired_editor_id) &Q(deleted_at=None)).distinct('user')
			else:
				tr = VendorLanguagePair.objects.filter(Q(source_lang_id=i.source_language_id) & Q(target_lang_id=i.target_language_id) & Q(user_id = obj.hired_editor_id) &Q(deleted_at=None)).distinct('user')
			print("Tr------------>",tr)
			if tr:
				condition_satisfied = True
				lang_pair = lang_pair.union(tr)
			else:
				condition_satisfied = False
				lang_pair = VendorLanguagePair.objects.none()
				break
		print("Langpair---------->",lang_pair)
		return VendorLanguagePairOnlySerializer(lang_pair, many=True, read_only=True).data

class InternalEditorDetailSerializer(serializers.Serializer):
	name = serializers.ReadOnlyField(source='internal_member.fullname')
	id = serializers.ReadOnlyField(source='internal_member_id')
	status = serializers.ReadOnlyField(source='get_status_display')
	avatar= serializers.ReadOnlyField(source='internal_member.professional_identity_info.avatar_url')
	vendor_lang_pair = serializers.SerializerMethodField()

	def get_vendor_lang_pair(self,obj):
		request = self.context['request']
		job_id= request.query_params.get('job')
		project_id= request.query_params.get('project')
		proj = Project.objects.get(id = project_id)
		jobs = Job.objects.filter(id = job_id) if job_id else proj.get_jobs
		lang_pair = VendorLanguagePair.objects.none()
		for i in jobs:
			tr = VendorLanguagePair.objects.filter(Q(source_lang_id=i.source_language_id) & Q(target_lang_id=i.target_language_id) & Q(user_id = obj.internal_member_id) &Q(deleted_at=None)).distinct('user')
			lang_pair = lang_pair.union(tr)
		return VendorLanguagePairOnlySerializer(lang_pair, many=True, read_only=True).data



class GetAssignToSerializer(serializers.Serializer):
	internal_editors = serializers.SerializerMethodField()
	external_editors = serializers.SerializerMethodField()
	suggestions = serializers.SerializerMethodField()
	agencies = serializers.SerializerMethodField()

	def get_internal_editors(self,obj):
		request = self.context['request']
		if obj.team:
			team = obj.team.internal_member_team_info.filter(role=2)
			return InternalEditorDetailSerializer(team,many=True,context={'request': request}).data
		else:
			return []


	def get_agencies(self,obj):
		try:
			default = AiUser.objects.get(email="ailaysateam@gmail.com")########need to change later##############
			if self.context.get('request').user == default:
				tt =[]
			else:
				try:profile = default.professional_identity_info.avatar_url
				except:profile = None
				tt = [{'name':default.fullname,'email':"ailaysateam@gmail.com",'id':default.id,'is_agency':default.is_agency,'status':'Invite Accepted','avatar':profile}]
		except:
			tt=[]
		request = self.context['request']
		qs = obj.team.owner.user_info.filter(role=2) if obj.team else obj.user_info.filter(role=2)
		qs_ = qs.filter(hired_editor__is_active = True).filter(hired_editor__is_agency = True).filter(~Q(hired_editor__email = "ailaysateam@gmail.com"))
		ser = HiredEditorDetailSerializer(qs_,many=True,context={'request': request}).data
		for i in ser:
			if i.get("vendor_lang_pair")!=[]:
				tt.append(i)
		return tt

	def get_external_editors(self,obj):
		request = self.context['request']
		tt=[]
		qs = obj.team.owner.user_info.filter(role=2) if obj.team else obj.user_info.filter(role=2)
		qs_ = qs.filter(hired_editor__is_active = True).filter(hired_editor__is_agency = False).filter(~Q(hired_editor__email = "ailaysateam@gmail.com"))
		ser = HiredEditorDetailSerializer(qs_,many=True,context={'request': request}).data
		for i in ser:
			if i.get("vendor_lang_pair")!=[]:
				tt.append(i)
		return tt

	def get_suggestions(self,obj):
		try:
			default = AiUser.objects.get(email="ailaysateam@gmail.com")########need to change later##############
			if self.context.get('request').user == default:
				tt =[]
			else:
				try:profile = default.professional_identity_info.avatar_url
				except:profile = None
				tt = [{'name':default.fullname,'email':"ailaysateam@gmail.com",'id':default.id,'is_agency':default.is_agency,'status':'Invite Accepted','avatar':profile}]
		except:
			tt=[]
		request = self.context['request']
		qs = obj.team.owner.user_info.filter(role=2) if obj.team else obj.user_info.filter(role=2)
		qs_ = qs.filter(hired_editor__is_active = True).filter(~Q(hired_editor__email = "ailaysateam@gmail.com"))
		ser = HiredEditorDetailSerializer(qs_,many=True,context={'request': request}).data
		for i in ser:
			if i.get("vendor_lang_pair")!=[]:
				tt.append(i)
		return tt
		# return HiredEditorDetailSerializer(qs,many=True,context={'request': request}).data


class StepsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Steps
        fields = "__all__"

class WorkflowsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Workflows
        fields = "__all__"

class WorkflowsStepsSerializer(serializers.ModelSerializer):
    workflows = serializers.PrimaryKeyRelatedField(queryset=Workflows.objects.all().values_list('pk', flat=True),required=False,write_only=True)
    steps =  serializers.ListField(required=False)
    user = serializers.PrimaryKeyRelatedField(queryset=AiUser.objects.all().values_list('pk', flat=True),required=False,write_only=True)
    workflow_name = serializers.CharField(required=False)

    class Meta:
        model = WorkflowSteps
        fields = ('workflows','steps','workflow_name','user',)

    def run_validation(self, data):
        print("Run Data---->",data)
        # if data.get('workflow_name'):
        if data.get('steps'):
           data['steps'] = [step for step in data.pop('steps',[])]
        return super().run_validation(data)


    def create(self,data):
        workflow_name = data.pop('workflow_name')
        user = data.pop('user')
        wf = Workflows.objects.create(name = workflow_name,user_id=user)
        steps = data.pop('steps')
        tt = [WorkflowSteps.objects.create(workflow = wf,steps_id = i )for i in steps]
        return wf

    def update(self,instance,data):
        if data.get('workflow_name'):
           instance.name = data.get('workflow_name')
           instance.save()
        if data.get('steps'):
           [WorkflowSteps.objects.create(workflow = instance,steps_id = i )for i in data.get('steps')]
        return super().update(instance, data)

def msg_send_vendor_accept(task_assign,input):
    from ai_marketplace.serializers import ThreadSerializer
    from ai_marketplace.models import ChatMessage
    sender = task_assign.assign_to
    receivers = []
    receiver =  task_assign.task_assign_info.assigned_by
    receivers =  receiver.team.get_project_manager if receiver.team.owner.is_agency or receiver.is_agency else []
    receivers.append( task_assign.task_assign_info.assigned_by)
    print("Receivers----------->",receivers)
    for i in receivers:
        thread_ser = ThreadSerializer(data={'first_person':sender.id,'second_person':i.id})
        if thread_ser.is_valid():
            thread_ser.save()
            thread_id = thread_ser.data.get('id')
        else:
            thread_id = thread_ser.errors.get('thread_id')
		#print("Thread--->",thread_id)
        print("Details----------->",task_assign.task.ai_taskid,task_assign.assign_to.fullname,task_assign.task.job.project.project_name)
        if input == 'task_accepted':
            message = "Task with task_id "+task_assign.task.ai_taskid+" assigned to "+ task_assign.assign_to.fullname +" in "+task_assign.task.job.project.project_name+" has accepted your rates and started working."
        elif input == 'change_request':
            message = "Task with task_id "+task_assign.task.ai_taskid+" assigned to "+ task_assign.assign_to.fullname +" in "+task_assign.task.job.project.project_name+" has submitted change request and waiting for your response."
        msg = ChatMessage.objects.create(message=message,user=sender,thread_id=thread_id)
        notify.send(sender, recipient=i, verb='Message', description=message,thread_id=int(thread_id))


def msg_send_customer_rate_change(task_assign):
    from ai_marketplace.serializers import ThreadSerializer
    from ai_marketplace.models import ChatMessage
    sender = task_assign.task_assign_info.assigned_by
    receiver =  task_assign.assign_to 
    receivers = []
    receivers =  receiver.team.get_project_manager if receiver.team.owner.is_agency or receiver.is_agency else []
    receivers.append(task_assign.assign_to)
    print("Receivers--------->",receivers)
    for i in receivers: 
        thread_ser = ThreadSerializer(data={'first_person':sender.id,'second_person':i.id})
        if thread_ser.is_valid():
            thread_ser.save()
            thread_id = thread_ser.data.get('id')
        else:
            thread_id = thread_ser.errors.get('thread_id')
        message = "Task with task_id "+task_assign.task.ai_taskid+" assigned to "+ task_assign.assign_to.fullname +" in "+task_assign.task.job.project.project_name+" has changed rates. please view and accept"
        print("Message---------------->",message)
        msg = ChatMessage.objects.create(message=message,user=sender,thread_id=thread_id)
        notify.send(sender, recipient=i, verb='Message', description=message,thread_id=int(thread_id))


def notify_task_completion_status(task_assign):
    from ai_marketplace.serializers import ThreadSerializer
    from ai_marketplace.models import ChatMessage
    sender = task_assign.assign_to
    receivers=[]
    try:
        team = task_assign.task.job.project.ai_user.team
        receivers =  team.get_project_manager if team else [task_assign.task_assign_info.assigned_by]
    except:pass
    task_ass_list = TaskAssign.objects.filter(task=task_assign.task).filter(~Q(assign_to=task_assign.assign_to))
    if task_ass_list: receivers.append(task_ass_list.first().assign_to)
    print('Receivers-------------->',receivers)
    for i in receivers:
       thread_ser = ThreadSerializer(data={'first_person':sender.id,'second_person':i.id})
       if thread_ser.is_valid():
            thread_ser.save()
            thread_id = thread_ser.data.get('id')
       else:
            thread_id = thread_ser.errors.get('thread_id')
       message = "Task with task_id "+task_assign.task.ai_taskid+" assigned to "+ task_assign.assign_to.fullname +' for '+task_assign.step.name +" in "+task_assign.task.job.project.project_name+" has submitted task."
       print("Message---------------->",message)
       msg = ChatMessage.objects.create(message=message,user=sender,thread_id=thread_id)
       notify.send(sender, recipient=i, verb='Message', description=message,thread_id=int(thread_id))



class TaskAssignUpdateSerializer(serializers.Serializer):
	task_assign = TaskAssignSerializer(required=False)
	task_assign_info = TaskAssignInfoNewSerializer(required=False)
	files = InstructionfilesSerializer(many=True,required=False)


	def to_internal_value(self, data):
		task_assign = {}
		for key in TaskAssignSerializer.Meta.fields:
			if key in data:
				task_assign[key] = data.pop(key)
		data['task_assign'] = task_assign
		task_assign_info = {}
		for key in TaskAssignInfoNewSerializer.Meta.fields:
			if key in data:
				task_assign_info[key] = data.pop(key)
		data['task_assign_info'] = task_assign_info
		if data.get('files'):
			data['files'] = [{'instruction_file':file} for file in data['files']]
		return super().to_internal_value(data)

	def update(self,instance,data):
		task_assign_serializer = TaskAssignSerializer()
		task_assign_info_serializer = TaskAssignInfoNewSerializer()
		po_update =[]
		if 'task_assign' in data:
			task_assign_data = data.get('task_assign')
			if task_assign_data.get('status') == 3:
				notify_task_completion_status(instance)
			# if task_assign_data.get('status') == 4:
			# 	notify_task_rework(instance)
			if task_assign_data.get('assign_to'):
				segment_count=0 if instance.task.document == None else instance.task.get_progress.get('confirmed_segments')
				task_history = TaskAssignHistory.objects.create(task_assign =instance,previous_assign_id=instance.assign_to_id,task_segment_confirmed=segment_count)
				task_assign_info_serializer.update(instance.task_assign_info,{'task_ven_status':None})
				task_assign_data.update({'status':1})
				po_update.append('assign_to')
			if task_assign_data.get('client_response'):
				task_assign_data.update({'user_who_approved_or_rejected':self.context.get('request').user})
			task_assign_serializer.update(instance, task_assign_data)
		if 'task_assign_info' in data:
			task_detail = data.get('task_assign_info')
			if (('currency' in task_detail) or ('mtpe_rate' in task_detail) or ('mtpe_hourly_rate' in task_detail) or ('estimated_hours' in task_detail) or ('mtpe_count_unit' in task_detail)):
				if instance.task_assign_info.task_ven_status == "change_request":
					try:msg_send_customer_rate_change(instance)
					except:pass
					# editing po
					print("inside accepted rate")
					po_update.append('accepted_rate')
					# po_update.append('change_request')
				else:
					po_update.append('accepted_rate_by_owner')
				task_assign_info_serializer.update(instance.task_assign_info,{'task_ven_status':None})

			if 'task_ven_status' in data.get('task_assign_info'):
				if data.get('task_assign_info').get('task_ven_status') == 'task_accepted':
					po_update.append("accepted")
				if data.get('task_assign_info').get('task_ven_status') == "change_request":
					po_update.append('change_request')
				ws_forms.task_assign_ven_status_mail(instance,data.get('task_assign_info').get('task_ven_status'))
				try:msg_send_vendor_accept(instance,data.get('task_assign_info').get('task_ven_status'))
				except:pass
			task_assign_info_data = data.get('task_assign_info')
			try:
				task_assign_info_serializer.update(instance.task_assign_info,task_assign_info_data)
			except:
				pass
			print("po update",po_update)
			if len(po_update)>0:
				try:
					po = po_modify(instance.task_assign_info.id,po_update)
					if not po:
						raise ValueError("new po not generated")
				except BaseException as e:
					logger.error(f"po creation failed with for task_assign->{instance.id} ,error :{str(e)}")

		if 'files' in data:
			[Instructionfiles.objects.create(**instruction_file,task_assign_info = instance.task_assign_info) for instruction_file in data['files']]
		return data


class DocumentImagesSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentImages
        fields = "__all__"



class MyDocumentSerializerNew(serializers.Serializer):
	id = serializers.IntegerField(read_only=True)
	word_count = serializers.IntegerField(read_only=True)
	doc_name = serializers.CharField(read_only=True)
	open_as = serializers.CharField(read_only=True)
	document_type__type = serializers.CharField(read_only=True)
	created_at = serializers.DateTimeField(read_only=True)
