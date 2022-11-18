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
		if not ('job_id') in data:
			raise serializers.ValidationError("Required fields missing!!!")
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
	#task_file = serializers.SerializerMethodField()
	#task_lang_pair = serializers.SerializerMethodField()
	class Meta:
		model = WordCountGeneral
		fields = ('project','task','new_words','repetition','tm_100','tm_95_99',\
					'tm_85_94','tm_75_84','tm_50_74','tm_101','tm_102','raw_total',)

class UserDefinedRateSerializer(serializers.ModelSerializer):
	class Meta:
		model = UserDefinedRate
		fields = '__all__'
