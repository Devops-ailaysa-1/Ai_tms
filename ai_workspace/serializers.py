from ai_pay.api_views import generate_client_po
from ai_staff.serializer import AiSupportedMtpeEnginesSerializer
from ai_staff.models import AilaysaSupportedMtpeEngines, SubjectFields, ProjectType,ProjectTypeDetail
from rest_framework import serializers
from .models import Project, Job, File, ProjectContentType, Tbxfiles,\
		ProjectSubjectField, TempFiles, TempProject, Templangpair, Task, TmxFile,\
		ReferenceFiles, TbxFile, TbxTemplateFiles, TaskCreditStatus,\
		TaskAssignInfo,TaskAssignHistory,TaskDetails,VoiceProjectDetail,TaskTranscriptDetails
import json
import pickle,itertools
from ai_workspace import forms as ws_forms
from ai_workspace_okapi.utils import get_file_extension, get_processor_name
# from ai_marketplace.models import AvailableVendors
from django.shortcuts import reverse
from rest_framework.validators import UniqueTogetherValidator
from ai_auth.models import AiUser,Team,HiredEditors
from ai_auth.validators import project_file_size
from collections import OrderedDict
from django.db.models import Q
from django.db import transaction
from ai_workspace_okapi.models import Document
from ai_auth.serializers import InternalMemberSerializer,HiredEditorSerializer
from ai_vendor.models import VendorLanguagePair
from django.db.models import OuterRef, Subquery
from ai_marketplace.serializers import ProjectPostJobDetailSerializer
from django.db import transaction

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
				  "can_delete")
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
				  "file", "job", "version", "assign_to", 'output_file_path',
				  "source_language_id", "target_language_id", "extension", "processor_name"
				  )

		extra_kwargs = {
			"file":{"write_only": True},
			"job": {"write_only": True},
			"version": {"write_only": True},
			"assign_to": {"write_only": True},}

		validators = [
			UniqueTogetherValidator(
				queryset=Task.objects.all(),
				fields=['file', 'job', 'version']
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


	def to_internal_value(self, data):
		data["version"] = 1
		data["assign_to"] = self.context.get("assign_to", None)
		return super().to_internal_value(data=data)

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

class ProjectQuickSetupSerializer(serializers.ModelSerializer):
	jobs = JobSerializer(many=True, source="project_jobs_set", write_only=True)
	files = FileSerializer(many=True, source="project_files_set", write_only=True)
	voice_proj_detail = VoiceProjectDetailSerializer(required=False,allow_null=True)
	project_name = serializers.CharField(required=False,allow_null=True)
	team_exist = serializers.BooleanField(required=False,allow_null=True, write_only=True)
	mt_engine_id = serializers.PrimaryKeyRelatedField(queryset=AilaysaSupportedMtpeEngines.objects.all().values_list('pk', flat=True),required=False,allow_null=True)
	assign_enable = serializers.SerializerMethodField(method_name='check_role')
	project_type_id = serializers.PrimaryKeyRelatedField(queryset=ProjectType.objects.all().values_list('pk',flat=True),required=False)
	project_analysis = serializers.SerializerMethodField(method_name='get_project_analysis')

	class Meta:
		model = Project
		fields = ("id", "project_name","assigned", "jobs","assign_enable","files","files_jobs_choice_url",
		 			"progress", "files_count", "tasks_count", "project_analysis", "is_proj_analysed",
					"team_exist","mt_engine_id","project_type_id","voice_proj_detail",)


	def run_validation(self,data):
		if self.context.get("request")!=None and self.context['request']._request.method == 'POST':
				pt = json.loads(data.get('project_type')[0]) if data.get('project_type') else 1
				if pt!=4 and data.get('target_languages')==None:
						raise serializers.ValidationError({"msg":"target languages needed for translation project"})
		if data.get('target_languages')!=None:
			comparisons = [source == target for (source, target) in itertools.product(data['source_language'],data['target_languages'])]
			if True in comparisons:
				raise serializers.ValidationError({"msg":"source and target languages should not be same"})
		return super().run_validation(data)

	def to_internal_value(self, data):
		print("DTATA------>",data)
		data["project_name"] = data.get("project_name", [None])[0]
		data["project_type_id"] = data.get("project_type",[1])[0]
		if data.get('sub_category'):
			data["voice_proj_detail"] = {"source_language": data.get("source_language", [None])[0],\
										"project_type_sub_category":data.get("sub_category",[None])[0]}
		if data.get('audio_file'):
		 	data['files'] = [{"file": file, "usage_type": 1} for file in data.get('audio_file', [])]
		else:
			data['files'] = [{"file": file, "usage_type": 1} for file in data.pop('files', [])]
		print('data[files]-------------->',data['files'])
		if self.context.get("request")!=None and self.context['request']._request.method == 'POST':
			data["jobs"] = [{"source_language": data.get("source_language", [None])[0], "target_language":\
				target_language} for target_language in data.get("target_languages", [None])]
		else:
			data["jobs"] = [{"source_language": data.get("source_language", [None])[0], "target_language":\
				target_language} for target_language in data.get("target_languages", [])]
		data['team_exist'] = data.get('team',[None])[0]
		data['mt_engine_id'] = data.get('mt_engine',[1])[0]
		return super().to_internal_value(data=data)

	def get_project_analysis(self,instance):
		user = self.context.get("request").user if self.context.get("request")!=None else self.context.get("ai_user", None)
		if instance.ai_user == user:
			tasks = instance.get_tasks
		elif instance.team:
			if ((instance.team.owner == user)|(user in instance.team.get_project_manager)):
				tasks = instance.get_tasks
			else:
				tasks = [task for job in instance.project_jobs_set.all() for task \
						in job.job_tasks_set.all().filter(assign_to_id = user)]
		else:
			tasks = [task for job in instance.project_jobs_set.all() for task \
						in job.job_tasks_set.all().filter(assign_to_id = user)]
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
		if self.context.get("request")!=None:
			created_by = self.context.get("request", None).user
		else:
		 	created_by = self.context.get("ai_user", None)
		if created_by.team:ai_user = created_by.team.owner
		else:ai_user = created_by
		team = created_by.team if created_by.team else None
		project_manager = created_by
		voice_proj_detail = validated_data.pop("voice_proj_detail",[])
		validated_data.pop('team_exist')
		print("validated_data---->",validated_data)
		project, files, jobs = Project.objects.create_and_jobs_files_bulk_create(
			validated_data, files_key="project_files_set", jobs_key="project_jobs_set", \
			f_klass=File,j_klass=Job, ai_user=ai_user,\
			team=team,project_manager=project_manager,created_by=created_by)#,team=team,project_manager=project_manager)

		if voice_proj_detail:
			voice_project = VoiceProjectDetail.objects.create(**voice_proj_detail,project=project)
			if voice_project.project_type_sub_category.id == 1 or 2: #1--->speech-to-text #2--->text-to-speech
				rr = voice_project.project.project_jobs_set.filter(~Q(target_language = None))
				if voice_project.project_type_sub_category.id == 2 and rr:
					tasks = Task.objects.create_tasks_of_files_and_jobs(
						files=files, jobs=jobs, project=project, klass=Task)
				else:
					tasks = Task.objects.create_tasks_of_audio_files(files=files,jobs=jobs,project=project, klass=Task)
		tasks = Task.objects.create_tasks_of_files_and_jobs(
			files=files, jobs=jobs, project=project, klass=Task)  # For self assign quick setup run)
		return  project

	def update(self, instance, validated_data):
		if validated_data.get('project_name'):
			instance.project_name = validated_data.get("project_name",\
									instance.project_name)
			instance.save()

		if 'team_exist' in validated_data:
			instance.team_id = None if validated_data.get('team_exist') == False else instance.ai_user.team.id
			instance.save()

		if validated_data.get('project_manager_id'):
			instance.project_manager_id = validated_data.get('project_manager_id')
			instance.save()

		if validated_data.get('mt_engine_id'):
			instance.mt_engine_id = validated_data.get('mt_engine_id')
			instance.save()

		files_data = validated_data.pop("project_files_set")
		jobs_data = validated_data.pop("project_jobs_set")
		with transaction.atomic():
			project, files, jobs = Project.objects.create_and_jobs_files_bulk_create_for_project(instance,\
									files_data, jobs_data, f_klass=File, j_klass=Job)
			try:
				if instance.voice_proj_detail.project_type_sub_category_id == 1 or 2: #1--->speech-to-text #2--->text-to-speech
						tasks = Task.objects.create_tasks_of_audio_files_by_project(project=project)
			except:
				tasks = Task.objects.create_tasks_of_files_and_jobs_by_project(\
					project=project)
		return  project

class TaskAssignInfoSerializer(serializers.ModelSerializer):
    assign_to=serializers.PrimaryKeyRelatedField(queryset=AiUser.objects.all().values_list('pk', flat=True),required=False,write_only=True)
    tasks = serializers.ListField(required=False)
    # assigned_by_name = serializers.ReadOnlyField(source='assigned_by.fullname')
    assign_to_details = serializers.SerializerMethodField()
    assigned_by_details = serializers.SerializerMethodField()
    job = serializers.ReadOnlyField(source='task.job.id')
    project = serializers.ReadOnlyField(source='task.job.project.id')
    instruction_file = serializers.FileField(required=False, allow_empty_file=True, allow_null=True)
    # assigned_to_name = serializers.ReadOnlyField(source='task.assign_to.fullname')
    # assigned_by = serializers.CharField(required=False,read_only=True)
    class Meta:
        model = TaskAssignInfo
        fields = ('id','instruction','instruction_file','filename','task_ven_status',\
                   'job','project','assigned_by','assignment_id','deadline','created_at',\
                   'assign_to','tasks','mtpe_rate','mtpe_count_unit','currency',\
                    'total_word_count','assign_to_details','assigned_by_details','payment_type')
        extra_kwargs = {
            'assigned_by':{'write_only':True},
            # 'assign_to':{'write_only':True}
             }

    def get_assign_to_details(self,instance):
	    if instance.task.assign_to:
	        external_editor = True if instance.task.assign_to.is_internal_member==False else False
	        email = instance.task.assign_to.email if instance.task.assign_to.is_internal_member==True else None
	        try:avatar = instance.task.assign_to.professional_identity_info.avatar_url
	        except:avatar = None
	        return {"id":instance.task.assign_to_id,"name":instance.task.assign_to.fullname,"email":email,"avatar":avatar,"external_editor":external_editor}

    def get_assigned_by_details(self,instance):
        if instance.assigned_by:
            return {"id":instance.assigned_by_id,"name":instance.assigned_by.fullname,"email":instance.assigned_by.email}




    def run_validation(self, data):
        if data.get('assign_to'):
           data["assign_to"] = json.loads(data["assign_to"])
        if data.get('task') and self.context['request']._request.method=='POST':
           data['tasks'] = [json.loads(task) for task in data.pop('task',[])]
        else:
           data['tasks'] = [json.loads(data.pop('task'))]
        # print(data['tasks'])
        data['assigned_by'] = self.context['request'].user.id
        # print("validated data run validation----->",data)
        return super().run_validation(data)


    def create(self, data):
        print('validated data kk==>',data)
        task_list = data.pop('tasks')
        assign_to = data.pop('assign_to')
        user1 = AiUser.objects.get(id=assign_to)
        total_word_count = data.pop('total_word_count',None)
        task_obj_list = Task.objects.filter(id__in=task_list)
        with transaction.atomic():
          task_assign_info = [TaskAssignInfo.objects.create(**data,task_id = task.id,total_word_count = task.task_word_count) for task in task_obj_list]
          task_info = [Task.objects.filter(id = task).update(assign_to_id = assign_to) for task in task_list]
          if user1.is_internal_member == False:
             generate_client_po(task_assign_info)
        return task_assign_info

    def update(self,instance,data):
        print("DATA-------->",data)
        if 'assign_to' in data:
            task = Task.objects.get(id = instance.task_id)
            segment_count=0 if task.document == None else task.get_progress.get('confirmed_segments')
            task_info = Task.objects.filter(id = instance.task_id).update(assign_to = data.get('assign_to'))
            task_history = TaskAssignHistory.objects.create(task_id =instance.task_id,previous_assign_id=task.assign_to_id,task_segment_confirmed=segment_count,unassigned_by=self.context.get('request').user)
            instance.task_ven_status = None
            instance.save()
        if 'task_ven_status' in data:
            ws_forms.task_assign_ven_status_mail(instance.task,instance.task_ven_status)
        if 'mtpe_rate' in data or 'mtpe_count_unit' in data or 'currency' in data:
            if instance.task_ven_status == 'change_request':
                instance.task_ven_status = None
                instance.save()
            elif instance.task_ven_status == 'task_accepted':
                raise serializers.ValidationError("Rates Can't be changed..Vendor already accepted rates and started working!!!")
        return super().update(instance, data)

    # def to_representation(self, instance):
    #     data = super().to_representation(instance)
    #     print(instance)
    #     data["assign_to"] = instance.task.assign_to.id
    #     # data['assigned_by'] = instance.task.job.project.ai_user.fullname
    #     return data


class VendorDashBoardSerializer(serializers.ModelSerializer):
	filename = serializers.CharField(read_only=True, source="file.filename")
	source_language = serializers.CharField(read_only=True, source=\
		"job.source_language.language")
	target_language = serializers.CharField(read_only=True, source=\
		"job.target_language.language")
	project_name = serializers.CharField(read_only=True, source=\
		"file.project.project_name")
	document_url = serializers.CharField(read_only=True, source="get_document_url")
	progress = serializers.DictField(source="get_progress", read_only=True)
	task_assign_info = TaskAssignInfoSerializer(required=False)
	bid_job_detail_info = serializers.SerializerMethodField()
	open_in =  serializers.SerializerMethodField()
	# task_word_count = serializers.SerializerMethodField(source = "get_task_word_count")
	# task_word_count = serializers.IntegerField(read_only=True, source ="task_details.first().task_word_count")
	# assigned_to = serializers.SerializerMethodField(source='get_assigned_to')

	class Meta:
		model = Task
		fields = \
			("id","filename", "ai_taskid","source_language", "target_language", "task_word_count","task_char_count","project_name",\
			"document_url", "progress","task_assign_info","bid_job_detail_info","open_in","assignable","first_time_open",)

	def get_bid_job_detail_info(self,obj):
		if obj.job.project.proj_detail.all():
			qs = obj.job.project.proj_detail.first().projectpost_jobs.filter(Q(src_lang_id = obj.job.source_language.id) & Q(tar_lang_id = obj.job.target_language.id if obj.job.target_language else obj.job.source_language.id ))
			return ProjectPostJobDetailSerializer(qs,many=True,context={'request':self.context.get("request")}).data
		else:
			return None

	def get_open_in(self,obj):
		try:
			if  obj.job.project.voice_proj_detail.project_type_sub_category_id == 1:return "Ailaysa Writer"
			elif  obj.job.project.voice_proj_detail.project_type_sub_category_id == 2:
				if obj.job.target_language==None:
					return "Download"
				else:return "Transeditor"
			else:return "Transeditor"
		except:
			return "Transeditor"
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
		tbx_file = data.get("tbx_file")
		return {"project": project, "job": job, "tbx_file": tbx_file}

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


# class TaskAssignInfoSerializer(serializers.ModelSerializer):
#     assign_to=serializers.PrimaryKeyRelatedField(queryset=AiUser.objects.all().values_list('pk', flat=True),required=False,write_only=True)
#     tasks = serializers.ListField(required=False)
#     class Meta:
#         model = TaskAssignInfo
#         fields = ('id','instruction','reference_file','assignment_id','deadline','assign_to','tasks','mtpe_rate','mtpe_count_unit','currency','total_word_count')
#
#     def run_validation(self, data):
#         if data.get('assign_to'):
#            data["assign_to"] = json.loads(data["assign_to"])
#         if data.get('task') and self.context['request']._request.method=='POST':
#            data['tasks'] = [json.loads(task) for task in data.pop('task',[])]
#         else:
#            data['tasks'] = [json.loads(data.pop('task'))]
#         print(data['tasks'])
#         print("validated data run validation----->",data)
#         return super().run_validation(data)
#
#     def create(self, data):
#         print('validated data==>',data)
#         task_list = data.pop('tasks')
#         assign_to = data.pop('assign_to')
#         task_info = [Task.objects.filter(id = task).update(assign_to_id = assign_to) for task in task_list]
#         task_assign_info = [TaskAssignInfo.objects.create(**data,task_id = task ) for task in task_list]
#         return task_assign_info
#
#     def update(self,instance,data):
#         if 'assign_to' in data:
#             task = Task.objects.get(id = instance.task_id)
#             segment_count=0 if task.document == None else task.get_progress.get('confirmed_segments')
#             task_info = Task.objects.filter(id = instance.task_id).update(assign_to = data.get('assign_to'))
#             task_history = TaskAssignHistory.objects.create(task_id =instance.task_id,previous_assign_id=task.assign_to_id,task_segment_confirmed=segment_count)
#         return super().update(instance, data)

class TaskDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskDetails
        fields = "__all__"

class TaskTranscriptDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskTranscriptDetails
        fields = "__all__"
        #read_only_fields = ("id","task",)

# class TasklistSerializer(TaskSerializer):
# 	task_assign_info = TaskAssignInfoSerializer(required=False)
# 	class Meta(TaskSerializer.Meta):
# 		fields = ("task_assign_info",)






class ProjectListSerializer(serializers.ModelSerializer):
	assign_enable = serializers.SerializerMethodField(method_name='check_role')

	class Meta:
		model = Project
		fields = ("id", "project_name","assign_enable","files_jobs_choice_url", )


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
	status = serializers.ReadOnlyField(source='get_status_display')
	avatar= serializers.ReadOnlyField(source='hired_editor.professional_identity_info.avatar_url')
	vendor_lang_pair = serializers.SerializerMethodField()

	def get_vendor_lang_pair(self,obj):
		request = self.context['request']
		job_id= request.query_params.get('job')
		project_id= request.query_params.get('project')
		proj = Project.objects.get(id = project_id)
		jobs = Job.objects.filter(id = job_id) if job_id else proj.get_jobs
		lang_pair = VendorLanguagePair.objects.none()
		for i in jobs:
			if i.target_language_id == None:
				tr = VendorLanguagePair.objects.filter(Q(source_lang_id=i.source_language_id) | Q(target_lang_id=i.source_language_id) & Q(user_id = obj.hired_editor_id) &Q(deleted_at=None)).distinct('user')
			else:
				tr = VendorLanguagePair.objects.filter(Q(source_lang_id=i.source_language_id) & Q(target_lang_id=i.target_language_id) & Q(user_id = obj.hired_editor_id) &Q(deleted_at=None)).distinct('user')
			lang_pair = lang_pair.union(tr)
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

	def get_internal_editors(self,obj):
		request = self.context['request']
		if obj.team:
			team = obj.team.internal_member_team_info.filter(role=2)
			return InternalEditorDetailSerializer(team,many=True,context={'request': request}).data
		else:
			return []

	def get_external_editors(self,obj):
		try:
			default = AiUser.objects.get(email="ailaysateam@gmail.com")########need to change later##############
			if self.context.get('request').user == default:
				tt =[]
			else:
				try:profile = default.professional_identity_info.avatar_url
				except:profile = None
				tt = [{'name':default.fullname,'email':"ailaysateam@gmail.com",'id':default.id,'status':'Invite Accepted','avatar':profile}]
		except:
			tt=[]
		request = self.context['request']
		qs = obj.team.owner.user_info.filter(role=2) if obj.team else obj.user_info.filter(role=2)
		qs_ = qs.filter(~Q(hired_editor__email = "ailaysateam@gmail.com"))
		ser = HiredEditorDetailSerializer(qs_,many=True,context={'request': request}).data
		for i in ser:
			if i.get("vendor_lang_pair")!=[]:
				tt.append(i)
		return tt
		# return HiredEditorDetailSerializer(qs,many=True,context={'request': request}).data
