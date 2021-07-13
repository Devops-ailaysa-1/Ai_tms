from re import T
from rest_framework import serializers 
from .models import  Project, Job, File

class ProjectSerializer(serializers.ModelSerializer):
	class Meta:
		model = Project
		exclude = ("created_at", "ai_user","project_id")
		read_only_fields = ("project_dir_path", )

	def create(self, validated_data):
		ai_user = self.context["request"].user 
		project = Project.objects.create(**validated_data, ai_user=ai_user)
		return project

class JobSerializer(serializers.ModelSerializer):
	class Meta:
		model = Job
		fields = ("source_language", "target_language")
	def validate(self, data):
		print('validate--->', data)
		return super().validate(data)
class FileSerializer(serializers.ModelSerializer):
	class Meta:
		model = File
		fields = ("file","file_type","project")
		#read_only_fields=("file_id",)


# class ProjectSetupSerializer(serializers.ModelSerializer):
# 	project_name = serializers.CharField(required=False)
# 	job = JobSerializer(many=True)
# 	file = FileSerializer(many=True)

# 	class Meta:
# 		model = Project
# 		fields = ("project_name", "file","job")

# 	def create(self, validated_data):
# 		print("validated data",validated_data)
# 		ai_user = self.context["request"].user
# 		job_data = validated_data.pop("job")
# 		#file = validated_data.pop("file")
# 		file_data = validated_data.pop("file") 
# 		project = Project.objects.create(**validated_data, ai_user=ai_user)
# 		for job in job_data:
# 			Job.objects.create(**job, project=project)
# 		for file in file_data:
# 			File.objects.create(**file, project=project)
# 		File.objects.create(**file, project=project,file_type= 'TRANSLATABLE')
# 		return project




class ProjectSetupSerializer(serializers.ModelSerializer):
	project_name = serializers.CharField(required=False)
	job = JobSerializer(many=True)
	file = FileSerializer(many=True)

	def validate(self, data):
		print('validate--->', data)
		return super().validate(data)

	class Meta:
		model = Project
		fields = ("project_name", "file","job")

	def create(self, validated_data):
		print("validated data",validated_data)
		ai_user = self.context["request"].user
		job_data = validated_data.pop("job")
		#file = validated_data.pop("file")
		file_data = validated_data.pop("file") 
		project = Project.objects.create(**validated_data, ai_user=ai_user)
		for job in job_data:
			Job.objects.create(**job, project=project)
		for file in file_data:
			File.objects.create(**file, project=project)
		File.objects.create(**file, project=project,file_type= 'TRANSLATABLE')
		return project
