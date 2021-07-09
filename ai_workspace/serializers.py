from rest_framework import serializers 
from .models import  Project

class ProjectSerializer(serializers.ModelSerializer):
	class Meta:
		model = Project
		exclude = ("project_dir_path", "created_at")