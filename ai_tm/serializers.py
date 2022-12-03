from rest_framework import serializers

from .models import TmxFileNew, WordCountGeneral, UserDefinedRate, CharCountGeneral


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
	task_file = serializers.ReadOnlyField(source = 'tasks.file.filename')
	task_id = serializers.ReadOnlyField(source = 'tasks.id')
	task_lang_pair = serializers.ReadOnlyField(source = 'tasks.job.source_target_pair_names')
	char_detail = serializers.SerializerMethodField()
	weighted = serializers.SerializerMethodField()

	class Meta:
		model = WordCountGeneral
		fields = ('project','tasks','task_id','task_file','task_lang_pair','new_words','repetition','tm_100','tm_95_99',\
					'tm_85_94','tm_75_84','tm_50_74','tm_101','tm_102','raw_total','weighted','char_detail',)
		extra_kwargs = {"project":{"write_only": True},'tasks':{'write_only':True}}

	def get_weighted(self,obj):
		weighted = self.context.get('weighted')
		return weighted

	def get_char_detail(self,obj):
		char_weighted = self.context.get('char_weighted')
		char_count = obj.tasks.task_cc_general.last()
		return CharCountGeneralSerializer(char_count,context={'char_weighted':char_weighted}).data

class CharCountGeneralSerializer(serializers.ModelSerializer):
	weighted_char = serializers.SerializerMethodField()
	class Meta:
		model = CharCountGeneral
		fields = ('new_words','repetition','tm_100','tm_95_99',\
					'tm_85_94','tm_75_84','tm_50_74','tm_101','tm_102','raw_total','weighted_char',)

	def get_weighted_char(self,obj):
		weighted_char = self.context.get('char_weighted')
		return weighted_char

class UserDefinedRateSerializer(serializers.ModelSerializer):
	class Meta:
		model = UserDefinedRate
		fields = '__all__'
