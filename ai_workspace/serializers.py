from ai_staff.serializer import AiSupportedMtpeEnginesSerializer
from ai_staff.models import AilaysaSupportedMtpeEngines, SubjectFields
from rest_framework import serializers
from .models import Project, Job, File, ProjectContentType, Tbxfiles,\
		ProjectSubjectField, TempFiles, TempProject, Templangpair, Task, TmxFile,\
		ReferenceFiles, TbxFile, TbxTemplateFiles, TaskCreditStatus
import json
import pickle,itertools
from ai_workspace_okapi.utils import get_file_extension, get_processor_name
from ai_marketplace.models import AvailableVendors
from django.shortcuts import reverse
from rest_framework.validators import UniqueTogetherValidator
from ai_auth.models import AiUser
from ai_auth.validators import project_file_size

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
		print("run_validation")
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
				  "file", "job", "version", "assign_to", 'output_file_path',
				  "source_language_id", "target_language_id", "extension", "processor_name"
				  )

		extra_kwargs = {
			"file":{"write_only": True},
			"job": {"write_only": True},
			"version": {"write_only": True},
			"assign_to": {"write_only": True},
		}

		validators = [
			UniqueTogetherValidator(
				queryset=Task.objects.all(),
				fields=['file', 'job', 'version']
			)
		]
	def run_validation(self,data):
		if self.context['request']._request.method == 'POST':
			assign_to = int(self.context.get("assign_to"))
			print(assign_to)
			customer_id = self.context.get("customer")
			print(customer_id)
			if assign_to != customer_id:
				vendors = AvailableVendors.objects.filter(customer_id = customer_id).values_list('vendor_id',flat = True)
				if assign_to not in (list(vendors)):
					raise serializers.ValidationError({"message":"This vendor is not hired vendor for customer"})
		return super().run_validation(data)


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
	project_name = serializers.CharField(required=False,allow_null=True)
	# ai_user = serializers.IntegerField(required=False)

	class Meta:
		model = Project
		fields = ("id", "project_name", "jobs", "files")#,'ai_user')

	def run_validation(self,data):
		if data.get('target_languages')!=None:
			comparisons = [source == target for (source, target) in itertools.product(data['source_language'],data['target_languages'])]
			if True in comparisons:
				raise serializers.ValidationError({"msg":"source and target languages should not be same"})
		return super().run_validation(data)

	def to_internal_value(self, data):
		data["project_name"] = data.get("project_name", [None])[0]
		data["jobs"] = [{"source_language": data.get("source_language", [None])[0], "target_language":\
			target_language} for target_language in data.get("target_languages", [])]
		print("files-->",data['files'])
		data['files'] = [{"file": file, "usage_type": 1} for file in data.pop('files', [])]

		return super().to_internal_value(data=data)


	def create(self, validated_data):
		print("data-->",validated_data)
		if self.context.get("request")!=None:
			ai_user = self.context.get("request", None).user
		else:
		 	ai_user = self.context.get("ai_user", None)
		project, files, jobs = Project.objects.create_and_jobs_files_bulk_create(
			validated_data, files_key="project_files_set", jobs_key="project_jobs_set", \
			f_klass=File,j_klass=Job, ai_user=ai_user)

		tasks = Task.objects.create_tasks_of_files_and_jobs(
			files=files, jobs=jobs, project=project, klass=Task)  # For self assign quick setup run)
		return  project

	def update(self, instance, validated_data):

		instance.project_name = validated_data.get("project_name",\
								instance.project_name)
		instance.save()

		files_data = validated_data.pop("project_files_set")
		jobs_data = validated_data.pop("project_jobs_set")

		project, files, jobs = Project.objects.create_and_jobs_files_bulk_create_for_project(instance,\

		files_data, jobs_data, f_klass=File, j_klass=Job)
		tasks = Task.objects.create_tasks_of_files_and_jobs_by_project(\
			project=project)  # For self assign quick setup run)

		return  project

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

	class Meta:
		model = Task
		fields = \
			("id","filename", "source_language", "target_language", "project_name",\
			"document_url", "progress")

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
