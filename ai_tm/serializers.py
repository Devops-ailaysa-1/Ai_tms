from rest_framework import serializers

from .models import TmxFileNew, WordCountGeneral, UserDefinedRate


class TmxFileSerializer(serializers.ModelSerializer):

	class Meta:
	    model = TmxFileNew
	    fields = ("id", "project", "tmx_file", "job", "filename")

	def save_update(self):
	    return super().save()

	@staticmethod
	def prepare_data(data):
		if not (("project_id" in data) and ("tmx_file" in data)) :
			raise serializers.ValidationError("Required fields missing!!!")
		project = data["project_id"]
		job = data.get("job_id", None)
		#tmx_file = data.get("tmx_file")
		return [{"project": project, "job": job, "tmx_file": tmx_file} for tmx_file in data['tmx_file']]


	# @staticmethod
	# def prepare_data(data):
	# 	if not (("project_id" in data) and ("tmx_file" in data)) :
	# 		raise serializers.ValidationError("Required fields missing!!!")
	# 	project = data["project_id"]
	# 	job = data.get("job_id", None)
	# 	tmx_file = data.get("tmx_file")
	# 	return {"project": project, "job": job, "tmx_file": tmx_file}


class WordCountGeneralSerializer(serializers.ModelSerializer):
	class Meta:
		model = WordCountGeneral
		fields = "__all__"

class UserDefinedRateSerializer(serializers.ModelSerializer):
	class Meta:
		model = UserDefinedRate
		fields = '__all__'
