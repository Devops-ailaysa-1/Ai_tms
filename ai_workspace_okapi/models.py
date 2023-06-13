import json
import re

from django.db import models
from django.db.models import Q
from django.db.models.signals import post_save
from django.utils.functional import cached_property

from ai_auth.models import AiUser
from ai_staff.models import LanguageMetaDetails, Languages, MTLanguageLocaleVoiceSupport, AilaysaSupportedMtpeEngines, \
    MTLanguageSupport
from ai_workspace_okapi.utils import get_runs_and_ref_ids, set_runs_to_ref_tags, split_check
from .signals import set_segment_tags_in_source_and_target, translate_segments


class TaskStatus(models.Model):
    task = models.ForeignKey("ai_workspace.Task", on_delete=models.SET_NULL, null=True)

class TextUnit(models.Model):
    okapi_ref_translation_unit_id = models.TextField()
    document = models.ForeignKey("Document", on_delete=models.CASCADE, related_name=\
        "document_text_unit_set")

    @property
    def text_unit_segment_set_exclude_merge_dummies(self):
        return self.text_unit_segment_set.exclude(Q(is_merged=True)&Q(is_merge_start=False))

    @property
    def owner_pk(self):
        return self.document.owner_pk

    @property
    def task_obj(self):
        return self.document.task_obj

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

class BaseSegment(models.Model):
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

    class Meta:
        ordering = ['id',]
        abstract = True

    @property
    def has_comment(self):
        if split_check(self.id):
            merge_seg = MergeSegment.objects.filter(id=self.id).first()
            if merge_seg:
                return merge_seg.segments.first().segment_comments_set.all().count()>0
            else:
                return self.segment_comments_set.all().count()>0
        else:
            seg = SplitSegment.objects.filter(id=self.id).first()
            return seg.split_segment_comments_set.all().count()>0


    @property
    def get_id(self):
        return self.id

    @property
    def coded_ids_aslist(self):
        return json.loads(self.coded_ids_sequence)

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
    @property
    def owner_pk(self):
        return self.text_unit.owner_pk

    @property
    def task_obj(self):
        return self.text_unit.task_obj

    def save(self, *args, **kwargs):
        return super(BaseSegment, self).save(*args, **kwargs)

# post_save.connect(set_segment_tags_in_source_and_target, sender=Segment)
# post_save.connect(translate_segments,sender=Segment)

class Segment(BaseSegment):
    is_merged = models.BooleanField(default=False, null=True)
    is_merge_start = models.BooleanField(default=False, null=True)
    is_split = models.BooleanField(default=False, null=True)

    @property
    def get_merge_target_if_have(self):
        if self.is_split in [False, None]:
            print(self)
            print("tt------>",self.get_active_object().coded_target)
            return self.get_active_object().coded_target
        else:
            split_segs = SplitSegment.objects.filter(segment_id = self.id).order_by('id')
            target_joined = ""
            for split_seg in split_segs:
                if split_seg.target != None:
                    target_joined += split_seg.target
                else:
                    target_joined += split_seg.source
            return set_runs_to_ref_tags(self.coded_source, target_joined, get_runs_and_ref_ids( \
                self.coded_brace_pattern, self.coded_ids_aslist))

    @property
    def get_mt_raw_target_if_have(self):
        if self.is_split in [False, None]:
            print('self------>',self)
            seg = self.get_active_object().id
            print("seg------->",seg)
            try:
                mt_raw = Segment.objects.get(id=seg).seg_mt_raw.mt_raw
            except:
                mt_raw = ''
            print("RR---------------->",mt_raw)
            #return mt_raw
            return set_runs_to_ref_tags(self.coded_source, mt_raw, get_runs_and_ref_ids( \
                self.coded_brace_pattern, self.coded_ids_aslist))
        else:
            print("Inside else------->",self)
            split_segs = SplitSegment.objects.filter(segment_id = self.id).order_by('id')
            target_joined = ""
            for split_seg in split_segs:
                if split_seg.mt_raw_split_segment != None:
                    target_joined += split_seg.mt_raw_split_segment.first().mt_raw
                else:
                    target_joined += split_seg.source
            print("RR----------------->",target_joined)
            return set_runs_to_ref_tags(self.coded_source, target_joined, get_runs_and_ref_ids( \
                self.coded_brace_pattern, self.coded_ids_aslist))


    @property
    def get_merge_segment_count(self):
        count = 0
        if self.is_merged and self.is_merge_start:
            count = MergeSegment.objects.get(id=self.id).segments.all().count() - 1
        return count

    def get_active_object(self):
        if self.is_merged and self.is_merge_start:
            return MergeSegment.objects.get(id=self.id)
        return self

    @property
    def get_parent_seg_id(self):
        return self.id

post_save.connect(set_segment_tags_in_source_and_target, sender=Segment)
post_save.connect(translate_segments,sender=Segment)
# post_save.connect(create_segment_controller, sender=Segment)

class MergeSegment(BaseSegment):
    segments = models.ManyToManyField(Segment, related_name=\
        "segments_merge_segments_set")
    text_unit = models.ForeignKey(TextUnit, on_delete=models.CASCADE,
        related_name="text_unit_merge_segment_set")
    is_split = models.BooleanField(default=False, null=True, blank=True)

    def update_segments(self, segs):
        self.source = "".join([seg.source for seg in segs])
        self.target = ""
        self.coded_source = "".join([seg.coded_source for seg in segs])
        self.temp_target = ""
        self.target_tags = "".join([seg.target_tags for seg in segs])
        self.tagged_source = "".join([seg.tagged_source for seg in segs])
        self.coded_brace_pattern = "".join([seg.coded_brace_pattern for seg in segs])
        self.status_id = None
        ids_seq = []
        for seg in segs:
            ids_seq+=json.loads(seg.coded_ids_sequence)
        self.coded_ids_sequence = json.dumps(ids_seq)

        random_ids = []
        for seg in segs:
            random_ids+=json.loads(seg.random_tag_ids)
        self.random_tag_ids = json.dumps(random_ids)

        self.okapi_ref_segment_id = segs[0].okapi_ref_segment_id
        self.save()
        self.update_segment_is_merged_true(segs=segs)
        return self

    def delete(self, using=None, keep_parents=False):
        for seg in self.segments.all():
            seg.is_merged = False
            seg.is_merge_start = False
            seg.status_id = None
            seg.temp_target = ""
            seg.target = ""
            seg.save()

        # Resetting the raw MT once a merged segment is restored
        first_seg_in_merge = self.segments.all().first()
        try: MT_RawTranslation.objects.get(segment_id=first_seg_in_merge.id).delete()
        except: print("No translation done for merged segment yet !!!")

        # Clearing the relations between MergeSegment and Segment
        self.segments.clear()

        return  super(MergeSegment, self).delete(using=using,
            keep_parents=keep_parents)

    # objects = MergeSegmentManager()

    @property
    def is_merged(self):
        return True

    def update_segment_is_merged_true(self,segs):
        segs[0].is_merge_start = True
        for seg  in segs:
            seg.is_merged = True
            seg.save()

    @property
    def validate_record(self):
        return all([segment.text_unit.id==self.text_unit.id for segment
            in self.segments.all()])

    @property
    def get_parent_seg_id(self):
        return self.id


class SplitSegment(BaseSegment):

    segment = models.ForeignKey(Segment, related_name = "split_segment_set", \
                                on_delete=models.CASCADE, null=True)
    text_unit = models.ForeignKey(TextUnit, on_delete=models.CASCADE,
                                  related_name="text_unit_split_segment_set")
    is_first = models.BooleanField(default=False, null=True)
    is_split = models.BooleanField(default=True, null=True)

    @property
    def get_parent_seg_id(self):
        return self.segment_id

    def remove_tags(self, tagged_source):

        tgt_tags = re.findall(f'</?\d+>', str(tagged_source))
        target_tags = ""
        for tag in tgt_tags:
            target_tags = target_tags + tag

        string = re.sub(f'</?\d+>', "", str(tagged_source))
        return str(string), str(target_tags)
    def update_segments(self, tagged_source, is_first=None):
        self.tagged_source = str(tagged_source)
        self.source, self.target_tags = self.remove_tags(tagged_source)
        self.is_first = True if is_first != None else False
        self.random_tag_ids = "[]"
        self.save()

class MT_RawTranslation(models.Model):

    segment = models.OneToOneField(Segment, null=True, blank=True, on_delete=models.SET_NULL,related_name='seg_mt_raw')
    mt_engine = models.ForeignKey(AilaysaSupportedMtpeEngines, null=True, blank=True, on_delete=models.SET_NULL,related_name="segment_mt_engine")
    mt_raw = models.TextField()
    task_mt_engine = models.ForeignKey(AilaysaSupportedMtpeEngines, null=True, blank=True, on_delete=models.SET_NULL,related_name="mt_engine_task")

    @property
    def target_language(self):
        return self.get_segment.text_unit.document.job.target_language_code
    
    @property
    def owner_pk(self):
        return self.segment.owner_pk

    @property
    def task_obj(self):
        return self.segment.task_obj

class MtRawSplitSegment(models.Model):
    split_segment = models.ForeignKey(SplitSegment, related_name = "mt_raw_split_segment", \
                                      on_delete = models.CASCADE, null=True)
    mt_raw = models.TextField(null=True, blank=True)
class Comment(models.Model):
    comment = models.TextField()
    segment = models.ForeignKey(Segment, on_delete=models.CASCADE, related_name=\
        "segment_comments_set")
    split_segment = models.ForeignKey(SplitSegment, on_delete=models.CASCADE, null=True, blank=True, \
                    related_name="split_segment_comments_set")
    #user = models.ForeignKey(AiUser, on_delete=models.SET_NULL, related_name = 'comment_user')

    @property
    def owner_pk(self):
        return self.segment.owner_pk

    @property
    def task_obj(self):
        return self.segment.task_obj

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
    def segments_for_find_and_replace(self):
        return self.get_segments().exclude(Q(source__exact='')|(Q(is_merged=True))|Q(is_split=True)).order_by("id")

    @property
    def segments_with_blank(self):
        return self.get_segments().filter(source__exact='').order_by("id")

    def split_segment_count(self):
        return self.get_segments().filter(is_split=True).count()

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
    def project_type_sub_category(self):
        try:
            return self.job.project.voice_proj_detail.project_type_sub_category_id
        except:
            return None

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
            if self.job.project.voice_proj_detail.project_type_sub_category_id == 2:##text_to_speech
                locale_list = MTLanguageLocaleVoiceSupport.objects.filter(language__language = self.job.target_language)
                return [{"locale":i.language_locale.locale_code,'gender':i.gender,\
                        "voice_type":i.voice_type,"voice_name":i.voice_name}\
                        for i in locale_list] if locale_list else []
            elif self.job.project.voice_proj_detail.project_type_sub_category_id == 1:##speech_to_text
                if self.job.target_language!=None:
                    txt_to_spc = MTLanguageSupport.objects.filter(language__language = self.job.target_language).first().text_to_speech
                    if txt_to_spc:
                        locale_list = MTLanguageLocaleVoiceSupport.objects.filter(language__language = self.job.target_language)
                        return [{"locale":i.language_locale.locale_code,'gender':i.gender,\
                                "voice_type":i.voice_type,"voice_name":i.voice_name}\
                                for i in locale_list] if locale_list else []
                    else: return False
                else:return False
        except:
            return None

    @property
    def converted_audio_file_exists(self):
        from ai_workspace.models import Task,TaskTranscriptDetails
        try:
            voice_pro = self.job.project.voice_proj_detail
            #if self.job.project.voice_proj_detail.project_type_sub_category_id != 1:
            task = Task.objects.filter(document=self).first()
            task_transcript = TaskTranscriptDetails.objects.filter(task=task).last()
            if task_transcript and (task_transcript.translated_audio_file!='') and (task_transcript.translated_audio_file!=None):
                return True
            else:
                return False
            #else:return None
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
        from ai_workspace_okapi.api_views import get_empty_segments
        total_credit_left = self.created_by.credit_balance.get("total_left")
        if get_empty_segments(self) == True:
            open_alert = False if (self.total_word_count < total_credit_left) else True
        else:
            open_alert = False
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
            rr = TaskAssign.objects.filter(task_id = task).filter(task_assign_info__isnull=False)
            return [{'assign_to_id':i.assign_to.id,'step_id':i.step.id,'task':i.task_id,'status':i.status,'reassigned':i.reassigned} for i in rr]
        else:
            return []

    @property
    def show_mt(self):
        from ai_workspace.models import Task
        mt_enable = Task.objects.filter(document=self).first().task_info.filter(step_id=1).first().mt_enable
        if mt_enable:return True
        else:return False

    @property
    def owner_pk(self):
        return self.job.project.owner_pk

    @property
    def task_obj(self):
        return self.task_set.last()

class SegmentPageSize(models.Model):
    ai_user = models.ForeignKey(AiUser, on_delete=models.CASCADE,
                                   related_name="user_default_page_size")
    page_size = models.IntegerField()


class FontSize(models.Model):
    ai_user = models.ForeignKey(AiUser, on_delete=models.CASCADE,
                                   related_name="user_font_size_set")
    font_size = models.IntegerField()
    language = models.ForeignKey(Languages, on_delete=models.CASCADE,
                                 related_name="language_font_size_set")
    
    @property
    def owner_pk(self):
        return self.ai_user.id


class SegmentHistory(models.Model):
    segment=models.ForeignKey(Segment, on_delete=models.CASCADE, related_name="segment_history")
    split_segment = models.ForeignKey(SplitSegment, on_delete=models.CASCADE, null=True, blank=True, related_name="split_segment_history")
    target=models.TextField(null=True, blank=True)
    #step = models.ForeignKey(Steps, on_delete=models.CASCADE,null=True,blank=True,related_name="seg_save_step")
    status=models.ForeignKey(TranslationStatus, null=True, blank=True, on_delete=models.SET_NULL, related_name="segment_status")
    user=models.ForeignKey(AiUser, null=True, on_delete=models.SET_NULL,related_name="edited_by")
    created_at=models.DateTimeField(auto_now_add=True)
    
    # sentense_diff_result=models.CharField(max_length=1000,null=True,blank=True)
    # save_type=models.CharField(max_length=100,blank=True,null=True)

class SelflearningAsset(models.Model):
    user=models.ForeignKey(AiUser, on_delete=models.CASCADE)
    target_language=models.ForeignKey(Languages,related_name='selflearning_target',on_delete=models.CASCADE)
    source_word=models.CharField(max_length=100,null=True,blank=True)
    edited_word=models.CharField(max_length=100,null=True,blank=True)

    def __str__(self) -> str:
        return self.source_word+'--'+self.edited_word
    
# from ai_workspace_okapi.api_views import update_self_learning
# post_save.connect(update_self_learning, sender=SegmentHistory)


class SegmentDiff(models.Model):
    # segment=models.ForeignKey(Segment, on_delete=models.CASCADE, related_name="main_segment")
    seg_history=models.ForeignKey(SegmentHistory,on_delete=models.CASCADE, related_name="segment_difference")
    sentense_diff_result=models.CharField(max_length=3000,null=True,blank=True)
    created_at=models.DateTimeField(auto_now_add=True)
    # edited_at=models.DateTimeField(auto_now=True)
    # status=models.ForeignKey(TranslationStatus,null=True, blank=True, on_delete=models.SET_NULL,related_name="segmentdiff_status")
    save_type=models.CharField(max_length=100,blank=True,null=True)

    def __str__(self) -> str:
        return self.sentense_diff_result
