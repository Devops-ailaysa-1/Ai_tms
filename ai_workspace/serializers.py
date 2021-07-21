from rest_framework import serializers
from ai_workspace.models import  Project, Job, File, TempFiles, TempProject, Templangpair
import json
import pickle

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

class JobSerializer(DynamicFieldsModelSerializer):
	project = serializers.IntegerField(required=False, source="project_id")
	class Meta:
		model = Job
		fields = ("project", "source_language", "target_language")

class FileSerializer(serializers.ModelSerializer):
	project = serializers.IntegerField(required=False, source="project_id")
	class Meta:
		model = File
		fields = ("file_type", "file", "project")

class ProjectSetupSerializer(serializers.ModelSerializer):
	jobs = JobSerializer(many=True, source="project_jobs_set", allowed_fields=("source_language",))
	files = FileSerializer(many=True, source="project_files_set")
	project_name = serializers.CharField(required=False)

	class Meta:
		model = Project
		fields = ("project_name", "jobs", "files")
		write_only_fields = ("jobs", "files")

	def run_validation(self, data):
			# data = pickle.dumps(self.initial_data['jobs'])
			# with open("my-data.pkl", "wb") as f:
			# 	f.write(data)
		# if not isinstance(data['jobs'],dict ):
		# 	try:
		# 		data['jobs'] = json.loads(data['jobs'])
		# 	except:
		# 		raise serializers.ValidationError("jobs is not json loaded type!!!")
		# data['files'] = [{"file":file, "file_type":14} for file in data['files']]
			# self.initial_data['files'] = [{"file"}]
		return data

	def create(self, validated_data):
		ai_user = self.context["request"].user
		project_jobs_set = validated_data.pop("project_jobs_set")
		project_files_set = validated_data.pop("project_files_set")
		project = Project.objects.create(**validated_data,  ai_user=ai_user)
		[project.project_jobs_set.create(**job_data) for job_data in  project_jobs_set]
		[project.project_files_set.create(**file_data) for file_data in project_files_set]
		# project.save()
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
