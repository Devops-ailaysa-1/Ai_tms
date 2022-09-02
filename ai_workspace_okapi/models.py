from django.db import models
# from ai_workspace.models import File, Job
# Create your models here.
from django.db.models.signals import post_save, pre_save
from .signals import set_segment_tags_in_source_and_target, create_segment_controller,translate_segments
import json
from ai_auth.models import AiUser
from ai_staff.models import LanguageMetaDetails, Languages, MTLanguageLocaleVoiceSupport, AilaysaSupportedMtpeEngines,MTLanguageSupport
from ai_workspace_okapi.utils import get_runs_and_ref_ids, set_runs_to_ref_tags
from django.utils.functional import cached_property
from django.db.models import Q, UniqueConstraint, CheckConstraint, F
from .managers import MergeSegmentManager
from django.apps import apps


class TaskStatus(models.Model):
    task = models.ForeignKey("ai_workspace.Task", on_delete=models.SET_NULL, null=True)

class TextUnit(models.Model):
    okapi_ref_translation_unit_id = models.TextField()
    document = models.ForeignKey("Document", on_delete=models.CASCADE, related_name=\
        "document_text_unit_set")

    # @property
    # def text_unit_segment_set_exclude_merge_dummies(self):
    #     return self.text_unit_segment_set.exclude(Q(is_merged=True)&Q(is_merge_start=False))

class MT_Engine(models.Model):
    engine_name = models.CharField(max_length=25,)

    def __str__(self):
        return self.engine_name

class TranslationStatus(models.Model):
    status_name = models.CharField(max_length=25)
    status_id = models.IntegerField()

    class Meta:
        verbose_name_plural = "Translation statuses"

    def __str__(self):
        return self.status_name

# class SegmentController(models.Model):
#     base_segment_id = models.BigIntegerField(unique=True)
#     related_model_string = models.TextField(default="ai_workspace_okapi.segment")
#     is_archived = models.BooleanField(default=False)
#     is_merged = models.BooleanField(default=False)
#
#     def get_segment(self):
#         return apps.get_model(self.related_model_string).objects\
#             .filter(id=self.base_segment_id).first()
#
#     def __add__(self, other):
#         print("---->", (self.base_segment_id + other.base_segment_id))
#
#     class Meta:
#         pass

class Segment(models.Model):
    source = models.TextField(blank=True)
    target = models.TextField(null=True, blank=True)
    temp_target = models.TextField(null=True, blank=True)
    coded_source = models.TextField(null=True, blank=True)
    tagged_source = models.TextField(null=True, blank=True)
    coded_brace_pattern = models.TextField(null=True, blank=True)
    coded_ids_sequence = models.TextField(null=True, blank=True)
    random_tag_ids = models.TextField(null=True, blank=True)
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
post_save.connect(translate_segments,sender=Segment)

class MT_RawTranslation(models.Model):

    SegmentStringChoices = (
        ("ai_workspace_okapi.segment", "Segment"),
        ("ai_workspace_okapi.mergesegment", "MergeSegment")
    )

    segment = models.OneToOneField(Segment, null=True, blank=True, on_delete=models.SET_NULL)
    mt_engine = models.ForeignKey(MT_Engine, null=True, blank=True, on_delete=models.SET_NULL)
    mt_raw = models.TextField()
    # segment_controller = models.OneToOneField(SegmentController, null=True, blank=True,
    #             on_delete=models.SET_NULL)
    reverse_string_for_segment = models.TextField(choices=SegmentStringChoices,
                default="ai_workspace_okapi.segment")
    task_mt_engine = models.ForeignKey(AilaysaSupportedMtpeEngines, null=True, blank=True, on_delete=models.SET_NULL)

    @property
    def target_language(self):
        return self.get_segment.text_unit.document.job.target_language_code

    # @property
    # def get_segment(self):
    #     return apps.get_model(self.reverse_string_for_segment).objects\
    #         .filter(mt_raw_translation=self).first()

class Comment(models.Model):
    comment = models.TextField()
    segment = models.ForeignKey(Segment, on_delete=models.CASCADE, related_name=\
        "segment_comments_set")
    #user = models.ForeignKey(AiUser, on_delete=models.SET_NULL, related_name = 'comment_user')

class Document(models.Model):
    file = models.ForeignKey("ai_workspace.File", on_delete=models.CASCADE,
        related_name="file_document_set")
    job = models.ForeignKey("ai_workspace.Job", on_delete=models.CASCADE,
        related_name="file_job_set")
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
    def segments_for_workspace(self):
        return self.get_segments().exclude(Q(source__exact='')|(Q(is_merged=True)
                    & (Q(is_merge_start__isnull=True) | Q(is_merge_start=False)))).order_by("id")

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
    def download_audio_output_file(self):
        try:
            voice_pro = self.job.project.voice_proj_detail
            if self.job.project.voice_proj_detail.project_type_sub_category_id == 2:
                locale_list = MTLanguageLocaleVoiceSupport.objects.filter(language__language = self.job.target_language)
                return [{"locale":i.language_locale.locale_code,'has_male':i.has_male,\
                        'has_female':i.has_female,"voice_type":i.voice_type,"voice_name":i.voice_name}\
                        for i in locale_list] if locale_list else []
            elif self.job.project.voice_proj_detail.project_type_sub_category_id == 1:
                if self.job.target_language!=None:
                    txt_to_spc = MTLanguageSupport.objects.filter(language__language = self.job.target_language).first().text_to_speech
                    if txt_to_spc:
                        locale_list = MTLanguageLocaleVoiceSupport.objects.filter(language__language = self.job.target_language)
                        return [{"locale":i.language_locale.locale_code,'has_male':i.has_male,\
                                'has_female':i.has_female,"voice_type":i.voice_type,"voice_name":i.voice_name}\
                                for i in locale_list] if locale_list else []
                    else: return False
                else:return False
        except:
            return None

    # @property
    # def download_audio_output_choices(self):
    #     try:
    #         voice_pro = self.job.project.voice_proj_detail
    #         if self.job.project.voice_proj_detail.project_type_sub_category_id == 2:
    #             return True
    #         else:
    #             return False
    #     except:
    #         return None


    @property
    def mt_usage(self):
        return sum([len(seg.source) for seg in self.segments.all()\
                if hasattr(seg, "mt_rawtranslation")])

    @property
    def doc_credit_check_open_alert(self):
        total_credit_left = self.created_by.credit_balance.get("total_left")
        open_alert = False if (self.total_word_count < total_credit_left) else True
        return open_alert

    @property
    def is_first_doc_view(self):
        user = self.job.project.ai_user.id
        ai_user_first_doc_id = Document.objects.filter(
            job__project__ai_user_id=user).first().id
        return True if self.id == ai_user_first_doc_id else False

    @property
    def assign_detail(self):
        from ai_workspace.models import Task,TaskAssign
        task = Task.objects.filter(document=self).first().id
        if TaskAssign.objects.filter(task_id = task).filter(task_assign_info__isnull=False):
            rr = TaskAssign.objects.filter(task_id = task)
            return [{'assign_to_id':i.assign_to.id,'step_id':i.step.id,'task':i.task_id,'status':i.status} for i in rr]
        else:
            return []

    @property
    def show_mt(self):
        from ai_workspace.models import Task,TaskAssign
        mt_enable = Task.objects.filter(document=self).first().task_info.filter(step_id=1).first().mt_enable
        if mt_enable:return True
        else:return False



class FontSize(models.Model):
    ai_user = models.ForeignKey(AiUser, on_delete=models.CASCADE,
                                   related_name="user_font_size_set")
    font_size = models.IntegerField()
    language = models.ForeignKey(Languages, on_delete=models.CASCADE,
                                 related_name="language_font_size_set")

# class MergeSegment(BaseSegment):
#     segments = models.ManyToManyField(Segment, related_name=\
#         "segments_merge_segments_set")
#     text_unit = models.ForeignKey(TextUnit, on_delete=models.CASCADE,
#         related_name="text_unit_merge_segment_set")
#
#     def update_segments(self, segs):
#         self.source = "".join([seg.source for seg in segs])
#         # self.target = "".join([seg.target for seg in segs])
#         self.target = ""
#         self.coded_source = "".join([seg.coded_source for seg in segs])
#         # self.temp_target = "".join([seg.temp_target for seg in segs])
#         self.temp_target = ""
#         self.target_tags = "".join([seg.target_tags for seg in segs])
#         self.tagged_source = "".join([seg.tagged_source for seg in segs])
#         self.coded_brace_pattern = "".join([seg.coded_brace_pattern for seg in segs])
#         self.status_id = None
#         ids_seq = []
#         for seg in segs:
#             ids_seq+=json.loads(seg.coded_ids_sequence)
#         self.coded_ids_sequence = json.dumps(ids_seq)
#
#         random_ids = []
#         for seg in segs:
#             random_ids+=json.loads(seg.random_tag_ids)
#         self.random_tag_ids = json.dumps(random_ids)
#
#         self.okapi_ref_segment_id = segs[0].okapi_ref_segment_id
#         self.save()
#         self.update_segment_is_merged_true(segs=segs)
#         return self
#
#     def delete(self, using=None, keep_parents=False):
#         for seg in self.segments.all():
#             seg.is_merged = False
#             seg.is_merge_start = False
#             seg.status_id = None
#             seg.temp_target = ""
#             seg.target = ""
#             seg.save()
#
#         return  super(MergeSegment, self).delete(using=using,
#             keep_parents=keep_parents)
#
#     objects = MergeSegmentManager()
#
#     @property
#     def is_merged(self):
#         return True
#
#     def update_segment_is_merged_true(self,segs):
#         segs[0].is_merge_start = True
#         for seg  in segs:
#             seg.is_merged = True
#             seg.save()
#
#     @property
#     def validate_record(self):
#         return all([segment.text_unit.id==self.text_unit.id for segment
#             in self.segments.all()])
#     @property
#     def is_merged(self):
#         return True
#
#     # class Meta:
#     #     constraints = [
#     #         CheckConstraint(
#     #             check = Q(text_unit=F('segments__text_unit')),
#     #             name = 'check_start_date',
#     #         ),
#     #     ]
#
# class SplitSegment(models.Model):
#     pass
#



class SegmentHistory(models.Model):
    segment = models.ForeignKey(Segment, on_delete=models.CASCADE, related_name="segment_history")
    target = models.TextField(null=True, blank=True)
    status = models.ForeignKey(TranslationStatus, null=True, blank=True, on_delete=models.SET_NULL, related_name="segment_status")
    user =  models.ForeignKey(AiUser, null=True, on_delete=models.SET_NULL,related_name="edited_by")
    created_at = models.DateTimeField(auto_now_add=True)
