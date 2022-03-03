from django.db import models
# from ai_workspace.models import File, Job
# Create your models here.
from django.db.models.signals import post_save, pre_save
from .signals import set_segment_tags_in_source_and_target
import json
from ai_auth.models import AiUser
from ai_staff.models import LanguageMetaDetails, Languages
from ai_workspace_okapi.utils import get_runs_and_ref_ids, set_runs_to_ref_tags
from django.utils.functional import cached_property

class TaskStatus(models.Model):
    task = models.ForeignKey("ai_workspace.Task", on_delete=models.SET_NULL, null=True)

class TextUnit(models.Model):
    okapi_ref_translation_unit_id = models.TextField()
    document = models.ForeignKey("Document", on_delete=models.CASCADE, related_name=\
        "document_text_unit_set")

class MT_Engine(models.Model):
    engine_name = models.CharField(max_length=25,)

class TranslationStatus(models.Model):
    status_name = models.CharField(max_length=25)
    status_id = models.IntegerField()

    def __str__(self):
        return self.status_name

class Segment(models.Model):
    source = models.TextField(blank=True)
    target = models.TextField(null=True, blank=True)
    temp_target = models.TextField(null=True, blank=True)
    coded_source = models.TextField(null=True, blank=True)
    tagged_source = models.TextField(null=True, blank=True)
    coded_brace_pattern = models.TextField(null=True, blank=True)
    coded_ids_sequence = models.TextField(null=True, blank=True)
    target_tags = models.TextField(null=True, blank=True)
    okapi_ref_segment_id = models.CharField(max_length=50)
    status = models.ForeignKey(TranslationStatus, null=True, blank=True, on_delete=\
        models.SET_NULL)
    text_unit = models.ForeignKey(TextUnit, on_delete=models.CASCADE, related_name=\
        "text_unit_segment_set")
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey("ai_auth.AiUser", on_delete=models.SET_NULL, null=True)
    # segment_count = models.TextField(null=True, blank=True)

    class Meta:
        ordering = ['id',]

    @property
    def has_comment(self):
        return self.segment_comments_set.all().count()>0

    @property
    def get_id(self):
        return self.id

    @property
    def coded_ids_aslist(self):
        return json.loads(self.coded_ids_sequence)

    #class Meta:
    #    managed = False

    @property
    def target_language_code(self):
        return self.text_unit.document.job.target_language_code

    @property
    def tm_fetch_configs(self):
        return self.text_unit.document.tm_fetch_configs

    @property
    def get_temp_target(self):
        return '' if self.temp_target == None else self.temp_target

    @property
    def coded_target(self):
        return  set_runs_to_ref_tags( self.coded_source, self.target, get_runs_and_ref_ids(\
            self.coded_brace_pattern, self.coded_ids_aslist ) )


    def save(self, *args, **kwargs):
        return super(Segment, self).save(*args, **kwargs)

post_save.connect(set_segment_tags_in_source_and_target, sender=Segment)

# class TempTargetSave(models.Model):
#     segment = models.OneToOneField(Segment, null=True, on_delete=models.CASCADE,
#                                    related_name="segment_temp_target")
#     target = models.TextField(null=True, blank=True)
#
#     @property
#     def get_target(self):
#         return '' if self.target == None else self.target

class MT_RawTranslation(models.Model):

    segment = models.OneToOneField(Segment, null=True, blank=True, on_delete=models.SET_NULL)
    mt_engine = models.ForeignKey(MT_Engine, null=True, blank=True, on_delete=models.SET_NULL)
    mt_raw = models.TextField()

    @property
    def target_language(self):
        return self.segment.text_unit.document.job.target_language_code

class Comment(models.Model):
    comment = models.TextField()
    segment = models.ForeignKey(Segment, on_delete=models.CASCADE, related_name=\
        "segment_comments_set")

class Document(models.Model):
    file = models.ForeignKey("ai_workspace.File", on_delete=models.CASCADE, related_name=\
        "file_document_set")
    job = models.ForeignKey("ai_workspace.Job", on_delete=models.CASCADE, related_name=\
        "file_job_set")
    total_word_count = models.IntegerField()
    total_char_count = models.IntegerField()
    total_segment_count = models.IntegerField()
    google_api_cost_est = models.IntegerField(null=True) #Estimation
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey("ai_auth.AiUser", on_delete=models.SET_NULL, null=True)

    class Meta:
        constraints = [ models.UniqueConstraint(fields=("file", "job"),\
                name="file + job combination should be unique") ]

    def save(self, *args, **kwargs):
        if self.google_api_cost_est == None:
            self.google_api_cost_est = round(self.total_char_count * (20 / 1000000), 3)
        return super().save(*args, **kwargs)

    def get_user_email(self):
        return self.created_by.email

    def get_segments(self):
        return Segment.objects.filter(text_unit__document__id=self.id)

    @property
    def segments_without_blank(self):
        return self.get_segments().exclude(source__exact='').order_by("id")

    @property
    def segments_with_blank(self):
        return self.get_segments().filter(source__exact='').order_by("id")

    @property
    def segments(self):
        return self.get_segments()

    @property
    def source_language_id(self):
        return self.job.source_language.id

    @property
    def target_language_id(self):
        return self.job.target_language.id

    @property
    def source_language_code(self):
        return self.job.source_language.locale.first().locale_code

    @property
    def target_language_code(self):
        return self.job.target_language.locale.first().locale_code

    @property
    def project(self):
        return self.job.project.id

    @property
    def doc_credit_debit_user(self):
        project = self.job.project
        if project.team:
            return project.team.owner
        else:
            return project.ai_user

    @cached_property
    def tm_fetch_configs(self):
        return dict(threshold=self.job.project.threshold,\
            max_hits=self.job.project.max_hits)

    @property
    def source_language(self):
        return str(self.job.source_language)

    @property
    def target_language(self):
        return str(self.job.target_language)

    @property
    def target_language_script(self):
        target_lang_id = self.job.target_language.id
        return LanguageMetaDetails.objects.get(language_id=target_lang_id).lang_name_in_script

    @property
    def source_language_id(self):
        return self.job.source_language.id

    @property
    def target_language_id(self):
        return self.job.target_language.id

    @property
    def source_language_code(self):
        return self.job.source_language.locale.first().locale_code

    @property
    def target_language_code(self):
        return self.job.target_language.locale.first().locale_code

    @property
    def project(self):
        return self.job.project.id

    @property
    def mt_usage(self):
        return sum([len(seg.source) for seg in self.segments.all()\
                if hasattr(seg, "mt_rawtranslation")])

    @property
    def doc_credit_check_open_alert(self):
        total_credit_left = self.created_by.credit_balance
        open_alert = False if (self.total_word_count < total_credit_left) else True
        return open_alert

    @property
    def is_first_doc_view(self):
        user = self.job.project.ai_user.id
        ai_user_first_doc_id = Document.objects.filter(job__project__ai_user_id=user).first().id
        return True if self.id == ai_user_first_doc_id else False

class FontSize(models.Model):
    ai_user = models.ForeignKey(AiUser, on_delete=models.CASCADE,
                                   related_name="user_font_size_set")
    font_size = models.IntegerField()
    language = models.ForeignKey(Languages, on_delete=models.CASCADE,
                                 related_name="language_font_size_set")
