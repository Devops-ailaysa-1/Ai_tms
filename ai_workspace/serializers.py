from ai_staff.serializer import AiSupportedMtpeEnginesSerializer
from ai_staff.models import AilaysaSupportedMtpeEngines, SubjectFields
from rest_framework import serializers
from ai_workspace.models import  Project, Job, File, ProjectContentType, ProjectSubjectField, TempFiles, TempProject, Templangpair
import json
import pickle

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
		fields = ("id","project", "source_language", "target_language")
		read_only_fields=("id",)

class FileSerializer(serializers.ModelSerializer):
	project = serializers.IntegerField(required=False, source="project_id")
	class Meta:
		model = File
		fields = ("id","usage_type", "file", "project","filename")
		read_only_fields=("id","filename",)

class ProjectSetupSerializer(serializers.ModelSerializer):
	jobs = JobSerializer(many=True, source="project_jobs_set")
	files = FileSerializer(many=True, source="project_files_set")
	project_name = serializers.CharField(required=False)

	class Meta:
		model = Project
		fields = ("project_name", "jobs", "files")

	def is_valid(self, *args, **kwargs):
		# data = pickle.dumps(self.initial_data['jobs'])
		# with open("my-data.pkl", "wb") as f:
		# 	f.write(data)

		print("type initial data-->", type(self.initial_data['jobs']))
		print("initial data--->", self.initial_data['jobs'])
		if not isinstance( self.initial_data['jobs'],dict ):
			self.initial_data['jobs'] = json.loads(self.initial_data['jobs'])
		self.initial_data['files'] = [{"file":file, "file_type":14} for file in self.initial_data['files']]
		# self.initial_data['files'] = [{"file"}]
		return super().is_valid(*args, **kwargs)

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
	#project = serializers.PrimaryKeyRelatedField(many=True,read_only = True)
	#subject = serializers.PrimaryKeyRelatedField(many=True,read_only = True)
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
	jobs = JobSerializer(many=True, source="project_jobs_set")
	files = FileSerializer(many=True, source="project_files_set")
	subjects =ProjectSubjectSerializer(many=True, source="proj_subject",required=False)
	contents =ProjectContentTypeSerializer(many=True, source="proj_content_type",required=False)
	project_name = serializers.CharField(required=False)
	# proj_mt_engine = serializers.PrimaryKeyRelatedField(queryset =AilaysaSupportedMtpeEngines.objects.all(),required=False)

	class Meta:
		model = Project
		fields = ("id","ai_project_id","project_name", "jobs", "files","contents","subjects","mt_engine")
		read_only_fields = ("id","ai_project_id")
		extra_kwargs = {
			"mt_engine":{
				"required": False
			}
		}
	def run_validation(self, data):
		print("run_validation")
		return super().run_validation(data=data)

	def is_valid(self, *args, **kwargs):
		# data = pickle.dumps(self.initial_data['jobs'])
		# with open("my-data.pkl", "wb") as f:
		# 	f.write(data)

		print("type initial data-->", type(self.initial_data['jobs']))
		print("initial data--->", self.initial_data['jobs'])
		#print("initial data--->subjects", self.initial_data['subjects'])
		#print("initial data--->contents", self.initial_data['contents'])
		if not isinstance( self.initial_data['jobs'],dict ):
			self.initial_data['jobs'] = json.loads(self.initial_data['jobs'])

		if isinstance( self.initial_data.get('subjects', None), str ):
			self.initial_data['subjects'] = json.loads(self.initial_data['subjects'])

		if isinstance( self.initial_data.get('contents', None), str ):
			self.initial_data['contents'] = json.loads(self.initial_data['contents'])

		self.initial_data['files'] = [{"file":file, "usage_type":1} for file in self.initial_data['files']]
		# self.initial_data['files'] = [{"file"}]
		return super().is_valid(*args, **kwargs)

	def create(self, validated_data):
		ai_user = self.context["request"].user
		todel=self.context.get("delete",None)
		project_jobs_set = validated_data.pop("project_jobs_set")
		project_files_set = validated_data.pop("project_files_set")
		proj_subject, proj_content_type = None, None 
		if "proj_subject" in validated_data:
			proj_subject = validated_data.pop("proj_subject")
		if "proj_content_type" in validated_data:
			proj_content_type = validated_data.pop("proj_content_type")

		#if todel:

			


		project = Project.objects.create(**validated_data,  ai_user=ai_user)
		[project.project_jobs_set.create(**job_data) for job_data in  project_jobs_set]
		[project.project_files_set.create(**file_data) for file_data in project_files_set]
		if proj_subject:
			[project.proj_subject.create(**sub_data) for sub_data in  proj_subject]
		if proj_content_type:
			[project.proj_content_type.create(**content_data) for content_data in  proj_content_type]
		# project.save()
		return project

	def update(self, instance, validated_data):
		pk=instance.id
		print("update pk",pk)
		todel=self.context.get("delete",None)
		project_jobs_set = validated_data.pop("project_jobs_set")
		project_files_set = validated_data.pop("project_files_set")
		proj_subject, proj_content_type = None, None 
		if "proj_subject" in validated_data:
			proj_subject = validated_data.pop("proj_subject")
		if "proj_content_type" in validated_data:
			proj_content_type = validated_data.pop("proj_content_type")
		if todel:
			if todel.get('subjetcs_del'):
				[File.objects.filter(project=instance.id,**file_id).delete() for file_id in todel.get('subjetcs_del') ]

		project = Project.objects.update_or_create(**validated_data,  id=instance.id)
		[project.project_jobs_set.create(**job_data) for job_data in  project_jobs_set]
		[project.project_files_set.create(**file_data) for file_data in project_files_set]
		if proj_subject:
			[project.proj_subject.create(**sub_data) for sub_data in  proj_subject]
		if proj_content_type:
			[project.proj_content_type.create(**content_data) for content_data in  proj_content_type]
		return project



class TemplangpairSerializer(serializers.ModelSerializer):
	project = serializers.CharField(required=False,source="temp_proj_langpair")
	class Meta:
		model = Templangpair
		fields = ( "project","temp_src_lang", "temp_tar_lang")

class TempFileSerializer(serializers.ModelSerializer):
	project = serializers.CharField(required=False,source="temp_proj_file")
	class Meta:
		model = TempFiles
		fields = ("project", "files_temp")




class TempProjectSetupSerializer(serializers.ModelSerializer):
	langpair = TemplangpairSerializer(many=True, source="temp_proj_langpair")
	tempfiles = TempFileSerializer(many=True, source="temp_proj_file")

	class Meta:
		model = TempProject
		fields = ( "temp_proj_id","langpair", "tempfiles")
		read_only_fields = ("temp_proj_id", )


	def is_valid(self, *args, **kwargs):
		print("intial-->",self.initial_data )
		self.initial_data['langpair'] = json.loads(self.initial_data['langpair'])
		self.initial_data['tempfiles'] = [{"files_temp":file} for file in self.initial_data['tempfiles']]
		# self.initial_data['files'] = [{"file"}]
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


