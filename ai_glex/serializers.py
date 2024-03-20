from rest_framework import serializers
from ai_auth.models import AiUser
from .models import (   Glossary,TermsModel,Tbx_Download,GlossaryFiles,\
                        GlossaryTasks,GlossarySelected,MyGlossary,GlossaryMt\
                    )
from rest_framework.validators import UniqueValidator
from ai_workspace.serializers import JobSerializer,ProjectQuickSetupSerializer
from ai_workspace.models import Project,File,Job,Task,TaskAssign,WorkflowSteps
import json


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

    # def create(self,validated_data):
        
    #     return super().create(self,validated_data)



class MyGlossarySerializer(serializers.ModelSerializer):
    class Meta:
        model = MyGlossary
        fields = "__all__"

class TermsSerializer(serializers.ModelSerializer):
    class Meta:
        model = TermsModel
        fields ="__all__"

class GlossarySelectedSerializer(serializers.ModelSerializer):
    glossary_name = serializers.ReadOnlyField(source="glossary.project.project_name")
    class Meta:
        model = GlossarySelected
        fields = ('id','project','glossary','glossary_name',)

class GlossaryMtSerializer(serializers.ModelSerializer):
    class Meta:
        model = GlossaryMt
        fields = "__all__"

class GlossarySetupSerializer(ProjectQuickSetupSerializer):
    glossary = GlossarySerializer(required= False)
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
        tasks = Task.objects.create_glossary_tasks_of_jobs(
                jobs=jobs,klass=Task)
        task_assign = TaskAssign.objects.assign_task(project=project)
        return project

    def update(self, instance, validated_data):
        print("In update----------->",validated_data)
        if 'glossary' in validated_data:
            glossary_serializer = self.fields['glossary']
            glossary_instance = instance.glossary_project
            # glossary_instance = Glossary.objects.get(project_id = instance.id)
            glossary_data = validated_data.pop('glossary')
            glossary_serializer.update(glossary_instance, glossary_data)
            # tasks = Task.objects.create_glossary_tasks_of_jobs_by_project(\
            #         project = instance)
        # task_assign = TaskAssign.objects.assign_task(project=instance)
        return super().update(instance, validated_data)



class GlossaryListSerializer(serializers.ModelSerializer):
    glossary_name = serializers.CharField(source = 'project_name')
    glossary_id = serializers.CharField(source = 'glossary_project.id')
    source_lang = serializers.SerializerMethodField()
    target_lang = serializers.SerializerMethodField()
    #source_lang = serializers.CharField(source = 'project_jobs_set.first().source_language.language')
    class Meta:
        model = Glossary
        fields = ("glossary_id", "glossary_name","source_lang", "target_lang",)

    def get_source_lang(self,obj):
        return obj.project_jobs_set.first().source_language.language

    def get_target_lang(self,obj):
         return [job.target_language.language for job in obj.project_jobs_set.all()]

class WholeGlossaryTermSerializer(serializers.ModelSerializer):
    term_id = serializers.ReadOnlyField(source = 'id')
    sl_term = serializers.ReadOnlyField(source='sl_term')
    tl_term = serializers.ReadOnlyField(source='tl_term')
    pos = serializers.ReadOnlyField(source='pos')
    glossary_name = serializers.ReadOnlyField(source='glossary.project.project_name')
    job = serializers.ReadOnlyField(source='job.source_target_pair_names')
    task_id = serializers.ReadOnlyField(source='job.job_tasks_set.all().first()')

    class Meta:
        fields = ('term_id','sl_term','tl_term','pos','glossary_name','job','task_id',)
