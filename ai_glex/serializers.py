from rest_framework import serializers
from ai_auth.models import AiUser
from .models import (   Glossary,TermsModel,Tbx_Download,GlossaryFiles,GlossaryTasks,
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


class TermsSerializer(serializers.ModelSerializer):
    class Meta:
        model = TermsModel
        fields ="__all__"


# class GlossaryTaskSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = GlossaryTasks
#         fields = "__all__"

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
        workflow = validated_data.get('workflow')
        original_validated_data = validated_data.copy()
        glossary_data = original_validated_data.pop('glossary')
        project = super().create(validated_data = original_validated_data)
        jobs = project.get_jobs
        glossary = Glossary.objects.create(**glossary_data,project=project)
        tasks = Task.objects.create_glossary_tasks_of_jobs(
                jobs=jobs,klass=Task)
        steps = [i.steps for i in WorkflowSteps.objects.filter(workflow=workflow)]
        if steps:
            task_assign = TaskAssign.objects.assign_task(steps=steps,project=project)
        return project

    def update(self, instance, validated_data):
        print("In update",validated_data)
        if 'glossary' in validated_data:
            glossary_serializer = self.fields['glossary']
            glossary_instance = instance.glossary_project
            # glossary_instance = Glossary.objects.get(project_id = instance.id)
            glossary_data = validated_data.pop('glossary')
            glossary_serializer.update(glossary_instance, glossary_data)
            tasks = Task.objects.create_glossary_tasks_of_jobs_by_project(\
                    project = instance)
        return super().update(instance, validated_data)
