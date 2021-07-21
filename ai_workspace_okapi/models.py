from django.db import models
# from ai_workspace.models import File, Job
# Create your models here.

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
            models.UniqueConstraint(fields=("file", "job"), name=\
                "file + job combination should be unique")
        ]

class TaskStatus(models.Model):
    task = models.ForeignKey("ai_workspace.Task", on_delete=models.SET_NULL, null=True)

class TextUnit(models.Model):
    okapi_ref_translation_unit_id = models.TextField()

class MT_Engine(models.Model):
    ''''''

class TranslationStatus(models.Model):
    status_name = models.CharField(max_length=25)
    status_id = models.IntegerField()


class Segment(models.Model):
    source = models.TextField()
    target = models.TextField(null=True, blank=True)
    coded_source = models.TextField(null=True, blank=True)
    coded_brace_pattern = models.TextField(null=True, blank=True)
    coded_ids_sequence = models.TextField(null=True, blank=True)
    target_tags = models.TextField(null=True, blank=True)
    okapi_ref_segment_id = models.CharField(max_length=50)
    status = models.ForeignKey(TranslationStatus, null=True, blank=True, on_delete=models.SET_NULL)
    text_unit = models.ForeignKey(TextUnit, on_delete=models.CASCADE)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey("ai_auth.AiUser", on_delete=models.SET_NULL, null=True)

class MT_RawTranslation(models.Model):

    segment = models.ForeignKey(Segment, null=True, blank=True, on_delete=models.SET_NULL)
    mt_engine = models.ForeignKey(MT_Engine, null=True, blank=True, on_delete=models.SET_NULL)
    mt_raw = models.TextField()

class Comment(models.Model):
    comment = models.TextField()
    segment = models.ForeignKey(Segment, on_delete=models.CASCADE)
