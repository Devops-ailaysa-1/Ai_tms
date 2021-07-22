from django import forms
from .models import Project, Job, File
from ai_staff.models import Languages

class JobForm(forms.ModelForm):
    # project = forms.CharField(required=False)
	# source_language = forms.ChoiceField(choices=[(lang.id, lang.language) for lang in Languages.objects.all()])
	class Meta:
		model = Job
		fields = ( "source_language", "target_language")

class FileForm(forms.ModelForm):
    class Meta:
        model = File
        fields = ( "file", )

class ProjectForm(forms.ModelForm):
    project_name = forms.CharField(required=False)
    class Meta:
        model = Project
        fields = ( "project_name", )
