from rest_framework import serializers
from ai_auth.models import AiUser
from .models import ( Glossary,TermsModel,Tbx_Download,GlossaryFiles,GlossaryTasks,GlossarySelected,
                     MyGlossary,GlossaryMt)  
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

    def create(self, validated_data):
        from ai_glex.signals import update_words_from_template
        instance = GlossaryFiles.objects.create(**validated_data)
        celery_id = update_words_from_template.apply_async(args=(instance.id,))
        instance.celery_id = celery_id
        instance.status  = "PENDING"
        instance.save()
        return instance


class MyGlossarySerializer(serializers.ModelSerializer):
    class Meta:
        model = MyGlossary
        fields = "__all__"

class TermsSerializer(serializers.ModelSerializer):
    #edit_allowed = serializers.SerializerMethodField()

    class Meta:
        model = TermsModel
        fields ="__all__" 
        # fields = ('sl_term', 'tl_term', 'pos', 'sl_definition', 'tl_definition', 'context', 'note', 
        #           'sl_source', 'tl_source', 'gender', 'termtype', 'geographical_usage', 'usage_status', 
        #           'term_location', 'created_date', 'modified_date', 'glossary', 'file', 'job', 'edit_allowed', )
    

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
        original_validated_data = validated_data.copy() ### for project create with project_type 3
        glossary_data = original_validated_data.pop('glossary')
        project = super().create(validated_data = original_validated_data)
        jobs = project.get_jobs
        glossary = Glossary.objects.create(**glossary_data,project=project)
        tasks = Task.objects.create_glossary_tasks_of_jobs(jobs=jobs,klass=Task)
        task_assign = TaskAssign.objects.assign_task(project=project)
        return project

    def update(self, instance, validated_data):
    
        if 'glossary' in validated_data:
            glossary_serializer = self.fields['glossary']
            glossary_instance = instance.glossary_project
            glossary_data = validated_data.pop('glossary')
            glossary_serializer.update(glossary_instance, glossary_data)

        return super().update(instance, validated_data)



class GlossaryListSerializer(serializers.ModelSerializer):
    glossary_name = serializers.CharField(source = 'project_name')
    glossary_id = serializers.CharField(source = 'glossary_project.id')
    source_lang = serializers.SerializerMethodField()
    target_lang = serializers.SerializerMethodField()
    project_id = serializers.CharField(source = 'individual_gloss_project.id')
    
    class Meta:
        model = Glossary
        fields = ("glossary_id", "glossary_name","source_lang", "target_lang","project_id")

    def get_source_lang(self,obj):
        return obj.project_jobs_set.first().source_language.language

    def get_target_lang(self,obj):
         return [job.target_language.language for job in obj.project_jobs_set.all() if job.job_tasks_set.all()] 

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

from ai_workspace.models import FileTermExtracted

class CeleryStatusForTermExtractionSerializer(serializers.ModelSerializer):
    file_name = serializers.ReadOnlyField(source='file_extraction.filename')
    term_model_file = serializers.ReadOnlyField(source='file_extraction.id')

    class Meta:
        model = FileTermExtracted
        fields = ("id",'status','celery_id','done_extraction','term_model_file','file_name','task')
