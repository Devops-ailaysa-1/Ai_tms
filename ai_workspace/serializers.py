from rest_framework import serializers 
from .models import AilzaUser, Project

class ProjectSerializer(serializers.ModelSerializer):
	class Meta:
		model = Project
		exclude = ("project_dir_path", "created_at")