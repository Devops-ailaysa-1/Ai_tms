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
    from ai_marketplace.api_views import unit_price_float_format
    task_assgn_objs = TaskAssignInfo.objects.filter(assignment_id = assignment_id)
    ins = TaskAssignInfo.objects.filter(assignment_id = assignment_id).first()
    file_detail = []
    for i in task_assgn_objs:
        billable_word_count = i.billable_word_count if i.billable_word_count!=None else i.task_assign.task.task_word_count
        billable_char_count = i.billable_char_count if i.billable_char_count!=None else i.task_assign.task.task_char_count
        if i.task_assign.task.job.project.project_type_id == 3:
            out = []
        elif i.mtpe_count_unit.unit == 'Word' or i.mtpe_count_unit.unit == 'Hour' or i.mtpe_count_unit.unit == 'Fixed':
            out = [{"file":i.task_assign.task.file.filename,"words":i.task_assign.task.task_word_count,"billable_word_count":billable_word_count,"unit":i.mtpe_count_unit.unit}]
        elif i.mtpe_count_unit.unit == 'Char':
            out = [{"file":i.task_assign.task.file.filename,"characters":i.task_assign.task.task_char_count,"billable_char_count":billable_char_count,"unit":i.mtpe_count_unit.unit}]
        file_detail.extend(out)
    print("FileDetail----------------->",file_detail)
    work = 'Post Editing' if ins.task_assign.step.id == 1 else 'Reviewing' 
    context = {'name':Receiver.fullname,'project':ins.task_assign.task.job.project,'job':ins.task_assign.task.job.source_target_pair_names, 'rate':str(unit_price_float_format(ins.mtpe_rate))+'('+ins.currency.currency_code+')'+' per '+ins.mtpe_count_unit.unit,
    'files':file_detail,'deadline':ins.deadline.date().strftime('%d-%m-%Y') if ins.deadline else None, 'work':work}
    msg_html = render_to_string("assign_detail_mail.html", context)
    send_mail(
        "Regarding Assigned Task Detail Info",None,
        settings.DEFAULT_FROM_EMAIL,
        [Receiver.email],
        #['thenmozhivijay20@gmail.com',],
        html_message=msg_html,
    )
    print("assign detail mailsent>>")


def task_assign_ven_status_mail(task_assign,task_ven_status):
    context = {'name':task_assign.task_assign_info.assigned_by.fullname,'task':task_assign.task.ai_taskid,'step':task_assign.step.name,'task_ven_status':task_ven_status,'assign_to':task_assign.assign_to.fullname,'project':task_assign.task.job.project}
    email = task_assign.task_assign_info.assigned_by.email

    msg_html = render_to_string("task_assign_ven_status_mail.html",context)
    send_mail(
        'Task Assign Vendor Status',None,
        settings.DEFAULT_FROM_EMAIL,
        [email],
        html_message=msg_html,
    )
    print("assign vendor status-->>>")



