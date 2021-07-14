from rest_framework import serializers
from .models import  Project, Job, File
import json

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
		fields = ("project", "source_language", "target_language")

class FileSerializer(serializers.ModelSerializer):
	project = serializers.IntegerField(required=False, source="project_id")
	class Meta:
		model = File
		fields = ("file_type", "file", "project")

class ProjectSetupSerializer(serializers.ModelSerializer):
	jobs = JobSerializer(many=True, source="project_jobs_set")
	files = FileSerializer(many=True, source="project_files_set")
	project_name = serializers.CharField(required=False)

	class Meta:
		model = Project
		fields = ("project_name", "jobs", "files")

	def is_valid(self, *args, **kwargs):
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
