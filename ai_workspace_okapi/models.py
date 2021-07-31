from django.db import models
# from ai_workspace.models import File, Job
# Create your models here.
from django.db.models.signals import post_save, pre_save
from .signals import set_segment_tags_in_source_and_target
import json

class TaskStatus(models.Model):
    task = models.ForeignKey("ai_workspace.Task", on_delete=models.SET_NULL, null=True)

class TextUnit(models.Model):
    okapi_ref_translation_unit_id = models.TextField()
    document = models.ForeignKey("Document", on_delete=models.CASCADE, related_name="document_text_unit_set")

class MT_Engine(models.Model):
    engine_name = models.CharField(max_length=25,)

class TranslationStatus(models.Model):
    status_name = models.CharField(max_length=25)
    status_id = models.IntegerField()

class Segment(models.Model):
    source = models.TextField()
    target = models.TextField(null=True, blank=True)
    coded_source = models.TextField(null=True, blank=True)
    tagged_source = models.TextField(null=True, blank=True)
    coded_brace_pattern = models.TextField(null=True, blank=True)
    coded_ids_sequence = models.TextField(null=True, blank=True)
    target_tags = models.TextField(null=True, blank=True)
    okapi_ref_segment_id = models.CharField(max_length=50)
    status = models.ForeignKey(TranslationStatus, null=True, blank=True, on_delete=models.SET_NULL)
    text_unit = models.ForeignKey(TextUnit, on_delete=models.CASCADE, related_name="text_unit_segment_set")
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey("ai_auth.AiUser", on_delete=models.SET_NULL, null=True)
    # segment_count = models.TextField(null=True, blank=True)

    @property
    def coded_ids_aslist(self):
        return json.loads(self.coded_ids_sequence)

    class Meta:
        managed = False

    @property
    def target_language_code(self):
        return self.text_unit.document.job.target_language_code
    #
    # def segment_count(self):
    #     return self.text_unit

post_save.connect(set_segment_tags_in_source_and_target, sender=Segment)

class MT_RawTranslation(models.Model):

    segment = models.OneToOneField(Segment, null=True, blank=True, on_delete=models.SET_NULL)
    mt_engine = models.ForeignKey(MT_Engine, null=True, blank=True, on_delete=models.SET_NULL)
    mt_raw = models.TextField()

    @property
    def target_language(self):
        return self.segment.text_unit.document.job.target_language_code

class Comment(models.Model):
    comment = models.TextField()
    segment = models.ForeignKey(Segment, on_delete=models.CASCADE)


class Document(models.Model):
    file = models.ForeignKey("ai_workspace.File", on_delete=models.CASCADE, related_name="file_document_set")
    job = models.ForeignKey("ai_workspace.Job", on_delete=models.CASCADE, related_name="file_job_set")
    total_word_count = models.IntegerField()
    total_char_count = models.IntegerField()
    total_segment_count = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey("ai_auth.AiUser", on_delete=models.SET_NULL, null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=("file", "job"), name= \
                "file + job combination should be unique")
        ]

    def get_user_email(self):
        return self.created_by.email

    def get_segments(self):
        return Segment.objects.filter(text_unit__document__id = self.id)

    @property
    def segments(self):
        return self.get_segments()