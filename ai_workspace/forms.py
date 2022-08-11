from django import forms
from .models import Project, Job, File, Task, VersionChoices, Version
from ai_staff.models import Languages
from ai_auth.models import AiUser
from django.conf import settings
from django.template.loader import render_to_string
from django.core.mail import send_mail
from ai_staff.models import Languages
import json
from decimal import *
from ai_workspace.models import TaskAssignInfo

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

class LoginForm(forms.Form):
    email = forms.EmailField(required=True);
    password = forms.CharField(required=True, widget=forms.PasswordInput())

    class Meta:
        fields = (
            "email", "password"
        )

class TaskForm(forms.ModelForm):
    file = forms.ModelChoiceField(queryset=File.objects.all())
    job = forms.ModelChoiceField(queryset=Job.objects.all())
    version = forms.ModelChoiceField(queryset=Version.objects.all())
    assign_to = forms.ModelChoiceField(queryset=AiUser.objects.filter(
                    userattribute__user_type__type="vendor") .all())
    class Meta:
        model = Task
        fields = (
            "file", "job", "version", "assign_to",
        )

        extra_kwargs = {
            "file": {"write_only": True},
            "job": {"write_only": True},
            "version": {"write_only": True},
            "assign_to": {"write_only": True},
        }

    def is_valid(self):
        valid = super().is_valid()
        if not valid:
            return valid
        # set_ ids
        self.cleaned_data = { k:v.id for k, v in self.cleaned_data.items()}
        return valid

class TaskListForm(forms.Form):
    tasks = forms.ModelChoiceField(queryset=Task.objects.all())

    class Meta:
        fields = (
            "tasks",
        )

class ProjectFormv2(forms.ModelForm):
    source_language = forms.ModelChoiceField(queryset=Languages.objects.all())
    target_languages = forms.ModelMultipleChoiceField(queryset=Languages.objects.all())
    files = forms.FileField(widget=forms.ClearableFileInput(attrs={"multiple": True}))

    class Meta:
        model = Project
        fields = (
            "files", "source_language", "target_languages"
        )

    def is_valid(self):
        valid = super().is_valid()
        if not valid:
            return valid
        self.cleaned_data["source_language"] = json.dumps(self.cleaned_data["source_language"].id)
        self.cleaned_data["target_languages"] = json.dumps([tl.id for tl in self.cleaned_data["target_languages"]])
        self.cleaned_data["files"] = self.files.getlist("files")
        return valid
        # self.cleaned_data


def task_assign_detail_mail(Receiver,assignment_id):
    task_assgn_objs = TaskAssignInfo.objects.filter(assignment_id = assignment_id)
    ins = TaskAssignInfo.objects.filter(assignment_id = assignment_id).first()
    file_detail = []
    for i in task_assgn_objs:
        if i.mtpe_count_unit.unit == 'Word' or 'Hour' or 'Total':
            out = [{"file":i.task.file.filename,"words":i.task.task_word_count,"unit":i.mtpe_count_unit.unit}]
        elif i.mtpe_count_unit.unit == 'Char':
            out = [{"file":i.task.file.filename,"characters":i.task.task_char_count,"unit":i.mtpe_count_unit.unit}]
        file_detail.extend(out)
    context = {'name':Receiver.fullname,'project':ins.task.job.project,'job':ins.task.job.source_target_pair_names, 'rate':str(ins.mtpe_rate.quantize(Decimal("0.00")))+'('+ins.currency.currency_code+')'+' per '+ins.mtpe_count_unit.unit,
    'files':file_detail,'deadline':ins.deadline.date().strftime('%d-%m-%Y')}
    msg_html = render_to_string("assign_detail_mail.html", context)
    send_mail(
        "Regarding Assigned Task Detail Info",None,
        settings.DEFAULT_FROM_EMAIL,
        [Receiver.email],
        #['thenmozhivijay20@gmail.com',],
        html_message=msg_html,
    )
    print("assign detail mailsent>>")


def task_assign_ven_status_mail(task,task_ven_status):
    context = {'name':task.task_assign_info.assigned_by.fullname,'task':task.ai_taskid,'task_ven_status':task_ven_status,'assign_to':task.assign_to.fullname,'project':task.job.project}
    print("CONTEXT-------------->",context)
    email = task.task_assign_info.assigned_by.email
    msg_html = render_to_string("task_assign_ven_status_mail.html",context)
    send_mail(
        'Task Assign Vendor Status',None,
        settings.DEFAULT_FROM_EMAIL,
        [email],
        html_message=msg_html,
    )
    print("assign vendor status-->>>")
