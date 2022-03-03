from rest_framework import serializers
from ai_auth.models import AiUser
from .models import (   Glossary,TermsModel,Tbx_Download,GlossaryFiles,GlossaryTasks,
                    )
from rest_framework.validators import UniqueValidator
from ai_workspace.serializers import JobSerializer,ProjectQuickSetupSerializer
from ai_workspace.models import Project,File,Job


class GlossarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Glossary
        fields = ('id','primary_glossary_source_name','details_of_PGS',\
                 'source_Copyright_owner','notes','usage_permission',\
                 'public_license',)

class GlossaryFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = GlossaryFiles
        fields = "__all__"


class GlossarySetupSerializer(ProjectQuickSetupSerializer):
    glossary = GlossarySerializer()
    # glossary_files = GlossaryFileSerializer(required= False,many= True,allow_null= True)

    class Meta(ProjectQuickSetupSerializer.Meta):
        fields = ProjectQuickSetupSerializer.Meta.fields + ('glossary',)

    def to_internal_value(self, data):
        glossary = {}
        for key in GlossarySerializer.Meta.fields:
            if key in data:
                glossary[key] = data.pop(key)[0]
        data['glossary'] = glossary
        return super().to_internal_value(data)


    def create(self, validated_data):
        original_validated_data = validated_data.copy()
        glossary_data = original_validated_data.pop('glossary')
        project = super().create(validated_data = original_validated_data)
        jobs = project.get_jobs
        glossary = Glossary.objects.create(**glossary_data,project=project)
        tasks = GlossaryTasks.objects.create_tasks_of_glossary_and_jobs(
                jobs=jobs, glossary=glossary,klass=GlossaryTasks)
        return glossary

    def update(self, instance, validated_data):
        print("In update",validated_data)
        if 'glossary' in validated_data:
            glossary_serializer = self.fields['glossary']
            glossary_instance = Glossary.objects.get(project_id = instance.id)
            glossary_data = validated_data.pop('glossary')
            glossary_serializer.update(glossary_instance, glossary_data)
            tasks = GlossaryTasks.objects.create_tasks_of_glossary_and_jobs_by_project(\
                    project = instance, glossary = glossary_instance)
        return super().update(instance, validated_data)

# class FileUploadSerializer(serializers.ModelSerializer):
#
#     class Meta:
#         model = UploadFilesModel
#         exclude = ('user','glossary',)

# class GlossarySerializer(serializers.ModelSerializer):
#     files  = FileSerializer(required=False, many=True, source='uploadfile', write_only=True)
#
#     class Meta:
#         model = Glossary
#         fields = ('id','glossary_Name','source_Langauge','target_Langauge',
#                 'primary_glossary_source_name','details_of_PGS','subject_field',
#                 'source_Copyright_owner','notes','usage_permission','public_license',
#                 'modified_date','user','files',)
#
#     def to_internal_value(self, data):
#         data['user'] = self.context.get("request").user.id
#         if data.get('files'):
#             data["files"] = [{"uploadfile":file} for file in data.get('files',[])]
#         return super().to_internal_value(data=data)
#
#     def create(self, validated_data):
#         files = validated_data.pop('uploadfile',None)
#         glossary = Glossary.objects.create(**validated_data)
#         if files:
#            [glossary.files.create(**file_data,user=validated_data.get('user')) for file_data in  files]
#         return glossary



# class TermsSerializer(serializers.ModelSerializer):
#     glossary_str = serializers.ReadOnlyField(source='glossary.glossary_Name')
#     class Meta:
#         model = TermsModel
#         fields = ('id','sl_term','tl_term','pos','sl_definition','tl_definition',
#                 'context','note','sl_source','tl_source','gender','termtype',
#                 'geographical_usage','usage_status','term_location','glossary',
#                 'glossary_str','upload_file',)
#
#         extra_kwargs = {'glossary':{"write_only":True},
#         }
