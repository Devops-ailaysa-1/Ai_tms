from ai_staff.serializer import AiSupportedMtpeEnginesSerializer
from ai_staff.models import AilaysaSupportedMtpeEngines, SubjectFields, ProjectType
from rest_framework import serializers
from .models import Project, Job, File, ProjectContentType, Tbxfiles,\
		ProjectSubjectField, TempFiles, TempProject, Templangpair, Task, TmxFile,\
		ReferenceFiles, TbxFile, TbxTemplateFiles, TaskCreditStatus,TaskAssignInfo,\
		TaskAssignHistory,TaskDetails,TaskAssign,Instructionfiles,Workflows, Steps, WorkflowSteps,\
		ProjectFilesCreateType,ProjectSteps
import json
import pickle,itertools
from ai_workspace_okapi.utils import get_file_extension, get_processor_name
from ai_marketplace.models import AvailableVendors
from django.shortcuts import reverse
from rest_framework.validators import UniqueTogetherValidator
from ai_auth.models import AiUser,Team,HiredEditors
from ai_auth.validators import project_file_size
from django.db.models import Q
from ai_workspace_okapi.models import Document
from ai_auth.serializers import InternalMemberSerializer,HiredEditorSerializer
from ai_vendor.models import VendorLanguagePair
from django.db.models import OuterRef, Subquery



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
	langpair = TemplangpairSerializer(many=True, source="temp_proj_langpair")
	tempfiles = TempFileSerializer(many=True, source="temp_proj_file",required=False)

	class Meta:
		model = TempProject
		fields = ( "temp_proj_id","langpair", "tempfiles")
		read_only_fields = ("temp_proj_id", )


	def is_valid(self, *args, **kwargs):
		print("intial-->",self.initial_data )
		source_language = json.loads(self.initial_data["source_language"])
		target_languages = json.loads(self.initial_data["target_languages"])
		# if len(self.initial_data['tempfiles'])>20:
		# 	raise serializers.ValidationError({"msg":"Number of files per project exceeded."})
		# if len(target_languages)>20:
		# 	raise serializers.ValidationError({"msg":"Number of jobs per project exceeded."})
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




class ProjectQuickSetupSerializer(serializers.ModelSerializer):
	jobs = JobSerializer(many=True, source="project_jobs_set", write_only=True)
	files = FileSerializer(many=True, source="project_files_set", write_only=True)
	project_name = serializers.CharField(required=False,allow_null=True)
	team_exist = serializers.BooleanField(required=False,allow_null=True, write_only=True)
	workflow_id = serializers.PrimaryKeyRelatedField(queryset=Workflows.objects.all().values_list('pk', flat=True),required=False,allow_null=True, write_only=True)
	mt_engine_id = serializers.PrimaryKeyRelatedField(queryset=AilaysaSupportedMtpeEngines.objects.all().values_list('pk', flat=True),required=False,allow_null=True, write_only=True)
	assign_enable = serializers.SerializerMethodField(method_name='check_role')
	project_analysis = serializers.SerializerMethodField(method_name='get_project_analysis')
	file_create_type = serializers.CharField(read_only=True,
			source="project_file_create_type.file_create_type")
	subjects =ProjectSubjectSerializer(many=True, source="proj_subject",required=False)
	contents =ProjectContentTypeSerializer(many=True, source="proj_content_type",required=False)
	steps = ProjectStepsSerializer(many=True,source="proj_steps",required=False)
	project_deadline = serializers.DateTimeField(required=False,allow_null=True)
	mt_enable = serializers.BooleanField(required=False,allow_null=True)
	project_type_id = serializers.PrimaryKeyRelatedField(queryset=ProjectType.objects.all().values_list('pk',flat=True),required=False,write_only=True)
	pre_translate = serializers.BooleanField(required=False,allow_null=True)
	file_create_type = serializers.CharField(read_only=True,
			source="project_file_create_type.file_create_type")

	class Meta:
		model = Project
		fields = ("id", "project_name","project_deadline","mt_enable","pre_translate","assigned", "jobs","assign_enable","files","files_jobs_choice_url","workflow_id",
		 			"progress", "files_count","steps", "tasks_count", "project_analysis", "is_proj_analysed","team_exist","subjects","contents","project_type_id", "file_create_type",'mt_engine_id',)
	# class Meta:
	# 	model = Project
	# 	fields = ("id", "project_name", "jobs", "files","team_id",'get_team',"assign_enable",'project_manager_id',"files_jobs_choice_url",
	# 	 			"progress", "files_count", "tasks_count", "project_analysis", "is_proj_analysed", )# "project_analysis",)#,'ai_user')

	def run_validation(self,data):
		if data.get('steps'):
			if '1' not in data['steps']:
				raise serializers.ValidationError({"msg":"step 1 is mandatory"})
		if data.get('target_languages')!=None:
			comparisons = [source == target for (source, target) in itertools.
				product(data['source_language'],data['target_languages'])]
			if True in comparisons:
				raise serializers.ValidationError({"msg":"source and target "
					"languages should not be same"})
		return super().run_validation(data)

	def to_internal_value(self, data):
		data["project_type_id"] = data.get("project_type",[1])[0]
		data["project_name"] = data.get("project_name", [None])[0]
		data["project_deadline"] = data.get("project_deadline",[None])[0]
		# data['workflow_id'] = data.get('workflow',[1])[0]
		data['mt_engine_id'] = data.get('mt_engine',[1])[0]
		data['mt_enable'] = data.get('mt_enable',['true'])[0]
		data['pre_translate'] = data.get('pre_translate',['false'])[0]
		data["jobs"] = [{"source_language": data.get("source_language", [None])[0], "target_language":\
			target_language} for target_language in data.get("target_languages", [])]
		data['files'] = [{"file": file, "usage_type": 1} for file in data.pop('files', [])]
		data['team_exist'] = data.get('team',[None])[0]
		if data.get('subjects'):
			data["subjects"] = [{"subject":sub} for sub in data.get('subjects',[])]
		if data.get("contents"):
			data["contents"]=[{"content_type":cont} for cont in data.get('contents',[])]
		data["steps"] = [{"steps":step} for step in data.get('steps',[])] if data.get('steps') else [{"steps":1}]
		print('dtatatat---->',data)
		return super().to_internal_value(data=data)

	def get_project_analysis(self,instance):
		user = self.context.get("request").user if self.context.get("request")!=None else self\
			.context.get("ai_user", None)
		if instance.ai_user == user:
			tasks = instance.get_tasks
		elif instance.team:
			if ((instance.team.owner == user)|(user in instance.team.get_project_manager)):
				tasks = instance.get_tasks
			else:
				tasks = [task for job in instance.project_jobs_set.all() for task \
						in job.job_tasks_set.all() for task_assign in task.task_info.filter(assign_to_id = user)]
				# tasks = [task for job in instance.project_jobs_set.all() for task \
				# 		in job.job_tasks_set.all().filter(assign_to_id = user)]
		else:
			tasks = [task for job in instance.project_jobs_set.all() for task \
					in job.job_tasks_set.all() for task_assign in task.task_info.filter(assign_to_id = user)]
			# tasks = [task for job in instance.project_jobs_set.all() for task \
			# 			in job.job_tasks_set.all().filter(assign_to_id = user)]
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
		# workflow = validated_data.get('workflow_id')
		validated_data.pop('team_exist')
		print("validated_data---->",validated_data)
		project_type = validated_data.get("project_type_id")
		proj_subject = validated_data.pop("proj_subject",[])
		proj_steps = validated_data.pop("proj_steps",[])
		proj_content_type = validated_data.pop("proj_content_type",[])

		project, files, jobs = Project.objects.create_and_jobs_files_bulk_create(
			validated_data, files_key="project_files_set", jobs_key="project_jobs_set", \
			f_klass=File,j_klass=Job, ai_user=ai_user,\
			team=team,project_manager=project_manager,created_by=created_by)#,team=team,project_manager=project_manager)
		ProjectFilesCreateType.objects.create(project=project)

		if proj_subject:
			[project.proj_subject.create(**sub_data) for sub_data in  proj_subject]
		if proj_content_type:
			[project.proj_content_type.create(**content_data) for content_data in proj_content_type]
		if proj_steps:
			[project.proj_steps.create(**steps_data) for steps_data in proj_steps]

		# steps = [i.steps for i in WorkflowSteps.objects.filter(workflow=workflow)]#need to include custom workflows
		print("STEP---->",proj_steps)

		if project_type == 1 or project_type == 2:
			tasks = Task.objects.create_tasks_of_files_and_jobs(
				files=files, jobs=jobs, project=project,klass=Task)  # For self assign quick setup run)
			task_assign = TaskAssign.objects.assign_task(project=project)
		return  project

	def update(self, instance, validated_data):#No update for steps and project_type
		if validated_data.get('project_name'):
			instance.project_name = validated_data.get("project_name",\
									instance.project_name)
			instance.save()

		if validated_data.get('mt_engine_id'):
			instance.mt_engine_id = validated_data.get("mt_engine_id",\
									instance.mt_engine_id)
			instance.save()

		if 'team_exist' in validated_data:
			instance.team_id = None if validated_data.get('team_exist') == False else instance.ai_user.team.id
			instance.save()

		if validated_data.get('project_manager_id'):
			instance.project_manager_id = validated_data.get('project_manager_id')
			instance.save()

		files_data = validated_data.pop("project_files_set")
		jobs_data = validated_data.pop("project_jobs_set")
		project_type = instance.project_type_id

		project, files, jobs= Project.objects.create_and_jobs_files_bulk_create_for_project(instance,\
							files_data, jobs_data,f_klass=File,\
							j_klass=Job)

		contents_data = validated_data.pop("proj_content_type",[])
		subjects_data = validated_data.pop("proj_subject",[])

		project,contents,subjects = Project.objects.create_content_and_subject_for_project(instance,\
							contents_data, subjects_data,\
							c_klass=ProjectContentType, s_klass = ProjectSubjectField)
		if project_type == 1 or project_type == 2:
			tasks = Task.objects.create_tasks_of_files_and_jobs_by_project(\
					project=project)
		return  project

	def to_representation(self, value):
		from ai_glex.serializers import GlossarySerializer
		from ai_glex.models import Glossary
		data = super().to_representation(value)
		try:
			ins = Glossary.objects.get(project_id = value.id)
			print(ins)
			glossary_serializer = GlossarySerializer(ins)
			data['glossary'] = glossary_serializer.data
		except:
			data['glossary'] = None
		return data


class InstructionfilesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Instructionfiles
        fields = "__all__"

class TaskAssignSerializer(serializers.ModelSerializer):
	task_info = TaskSerializer(required=False,many=True)
	# step = serializers.PrimaryKeyRelatedField(queryset=Steps.objects.all().values_list('pk', flat=True),required=False)
	class Meta:
		model = TaskAssign
		fields =('task_info','step','assign_to','mt_enable','mt_engine','pre_translate','status',)

class TaskAssignInfoNewSerializer(serializers.ModelSerializer):
	task_assign_info = TaskAssignSerializer(required=False)
	class Meta:
		model = TaskAssignInfo
		fields = ('instruction','assignment_id','deadline','total_word_count',\
				'mtpe_rate','mtpe_count_unit','currency','assigned_by','task_assign_info',)



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

    class Meta:
        model = TaskAssignInfo
        fields = ('id','instruction','files','step','instruction_files',\
                   'job','project','assigned_by','assignment_id','mt_engine_id','deadline',\
                   'assign_to','tasks','mtpe_rate','mtpe_count_unit','currency',\
                    'total_word_count','assign_to_details','assigned_by_details',\
                    'mt_enable','pre_translate','task_assign_detail')
        extra_kwargs = {
            'assigned_by':{'write_only':True},
            # 'assign_to':{'write_only':True}
             }

    def get_assign_to_details(self,instance):
	    if instance.task_assign.assign_to:
	        email = instance.task_assign.assign_to.email if instance.task_assign.assign_to.is_internal_member==True else None
	        try:avatar = instance.task_assign.assign_to.professional_identity_info.avatar_url
	        except:avatar = None
	        return {"id":instance.task_assign.assign_to_id,"name":instance.task_assign.assign_to.fullname,"email":email,"avatar":avatar}

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
        return {'step':step,'mt_enable':mt_enable,'pre_translate':pre_translate}

    def run_validation(self, data):
        if data.get('assign_to'):
           data["assign_to"] = json.loads(data["assign_to"])
        if data.get('step'):
           data["step"] = json.loads(data["step"])
        if data.get('mt_engine'):
           data['mt_engine_id'] = json.loads(data['mt_engine'])
        if data.get('mt_enable'):
           data['mt_enable'] = json.loads(data['mt_enable'])
        if data.get('pre_translate'):
           data['pre_translate'] = json.loads(data['pre_translate'])
        if data.get('task'): #and self.context['request']._request.method=='POST':
           data['tasks'] = [json.loads(task) for task in data.pop('task',[])]
        if data.get('files'):
           data['files'] = [{'instruction_file':file} for file in data['files']]
        data['assigned_by'] = self.context['request'].user.id
        print("validated data run validation----->",data)
        return super().run_validation(data)


    def create(self, data):
        print('validated data==>',data)
        task_list = data.pop('tasks')
        step = data.pop('step')
        assign_to = data.pop('assign_to')
        files = data.pop('files')
        mt_engine_id = data.pop('mt_engine_id',None)
        mt_enable = data.pop('mt_enable',None)
        pre_translate = data.pop('pre_translate',None)
        task_assign_list = [TaskAssign.objects.get(Q(task_id = task) & Q(step_id = step)) for task in task_list]
        task_assign_info = [TaskAssignInfo.objects.create(**data,task_assign = task_assign ) for task_assign in task_assign_list]
        [Instructionfiles.objects.create(**instruction_file,task_assign_info = assign) for instruction_file in files for assign in task_assign_info]
        task_assign_data = [TaskAssign.objects.filter(Q(task_id = task) & Q(step_id = step)).update(assign_to_id = assign_to) for task in task_list]
        if mt_engine_id:
           [TaskAssign.objects.filter(Q(task_id = task) & Q(step_id = step)).update(mt_engine_id=mt_engine_id) for task in task_list]
        if mt_enable:
           [TaskAssign.objects.filter(Q(task_id = task) & Q(step_id = step)).update(mt_enable = mt_enable) for task in task_list]
        if pre_translate:
           [TaskAssign.objects.filter(Q(task_id = task) & Q(step_id = step)).update(pre_translate = pre_translate) for task in task_list]
        return task_assign_info

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
	# task_assign_info = TaskAssignInfoSerializer(required=False)
	task_assign_info = serializers.SerializerMethodField(source = "get_task_assign_info")
	task_word_count = serializers.SerializerMethodField(source = "get_task_word_count")
	can_open = serializers.SerializerMethodField()
	# task_word_count = serializers.IntegerField(read_only=True, source ="task_details.first().task_word_count")
	# assigned_to = serializers.SerializerMethodField(source='get_assigned_to')

	class Meta:
		model = Task
		fields = \
			("id","filename", "source_language", "target_language", "project_name",\
			"document_url", "progress","task_assign_info","task_word_count",'can_open',)

	def get_can_open(self,obj):
		try:
			if obj.task_info.get(step_id = 1) :
				can_open = True
			elif obj.task_info.get(step_id = 1).get_status_display() == "Completed":
				can_open = True
			else:
				can_open = False
			return can_open
		except:
			return None


	def get_task_assign_info(self, obj):
		task_assign = obj.task_info.filter(task_assign_info__isnull=False)
		if task_assign:
			task_assign_info=[]
			for i in task_assign:
				try:task_assign_info.append(i.task_assign_info)
				except:pass
			return TaskAssignInfoSerializer(task_assign_info,many=True).data
		else: return None



	def get_task_word_count(self,instance):
		if instance.document_id:
			document = Document.objects.get(id = instance.document_id)
			return document.total_word_count
		else:
			try:
				task_detail = TaskDetails.objects.get(task_id = instance.id)
				return task_detail.task_word_count
			except:return None

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


class TaskDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskDetails
        fields = "__all__"


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
	class Meta:
		model = VendorLanguagePair
		fields = ('source_lang','target_lang',)

class HiredEditorDetailSerializer(serializers.Serializer):
	name = serializers.ReadOnlyField(source='hired_editor.fullname')
	id = serializers.ReadOnlyField(source='hired_editor_id')
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
			tr = VendorLanguagePair.objects.filter(Q(source_lang_id=i.source_language_id) & Q(target_lang_id=i.target_language_id) & Q(user_id = obj.hired_editor_id) &Q(deleted_at=None))
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
			tr = VendorLanguagePair.objects.filter(Q(source_lang_id=i.source_language_id) & Q(target_lang_id=i.target_language_id) & Q(user_id = obj.internal_member_id) &Q(deleted_at=None))
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
		request = self.context['request']
		qs = obj.team.owner.user_info.filter(role=2) if obj.team else obj.user_info.filter(role=2)
		ser = HiredEditorDetailSerializer(qs,many=True,context={'request': request}).data
		tt = []
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
		if 'task_assign' in data:
			task_assign_serializer = TaskAssignSerializer()
			task_assign_data = data.get('task_assign')
			if task_assign_data.get('assign_to'):
				segment_count=0 if instance.task.document == None else instance.task.get_progress.get('confirmed_segments')
				task_history = TaskAssignHistory.objects.create(task_assign =instance,previous_assign_id=instance.assign_to_id,task_segment_confirmed=segment_count)
			task_assign_serializer.update(instance, task_assign_data)
		if 'task_assign_info' in data:
			task_assign_info_serializer = TaskAssignInfoNewSerializer()
			task_assign_info_data = data.get('task_assign_info')
			try:task_assign_info_serializer.update(instance.task_assign_info,task_assign_info_data)
			except:pass
		if 'files' in data:
			[Instructionfiles.objects.create(**instruction_file,task_assign_info_id = instance.id) for instruction_file in data['files']]
		return data
