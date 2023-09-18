from django.core.mail import send_mail
import smtplib
from ai_pay.api_views import po_modify_weigted_count
from celery.utils.log import get_task_logger
import celery,re,pickle, copy
import djstripe
logger = get_task_logger(__name__)
from celery.decorators import task
from celery import shared_task
from datetime import date
from django.utils import timezone
from .models import AiUser,UserAttribute,HiredEditors,ExistingVendorOnboardingCheck
import datetime,os,json, collections
from djstripe.models import Subscription,Invoice,Charge
from ai_auth.Aiwebhooks import renew_user_credits_yearly
from notifications.models import Notification
from ai_auth import forms as auth_forms
from ai_marketplace.models import ProjectboardDetails
import requests, re
from contextlib import closing
from django.db import connection
from django.db.models import Q
from ai_workspace.models import Task
from ai_auth.api_views import resync_instances
import os, json
from ai_workspace_okapi.utils import set_ref_tags_to_runs, get_runs_and_ref_ids, get_translation
from ai_workspace.models import Task,MTonlytaskCeleryStatus
import os, json
from datetime import datetime, timedelta
from django.db.models import DurationField, F, ExpressionWrapper,Q
#from translate.storage.tmx import tmxfile
from celery_progress.backend import ProgressRecorder
from time import sleep
from django.core.management import call_command
import calendar
from ai_workspace.models import ExpressTaskHistory
from celery.exceptions import MaxRetriesExceededError

extend_mail_sent= 0

def striphtml(data):
    p = re.compile(r'<.*?>')
    return p.sub('', data)
# @shared_task
# def test_task():
#     print("this is task")

# @shared_task
# def email_send_task(sub, msg, from_email, to_mails_list):
#     send_mail(
#         sub, msg, from_email, to_mails_list
#         # html_message=msg_html,
#     )
#     return True

# @shared_task
# def send_dj_core_emails(conn, from_email, recipients, message, fail_silently=True):
#     try:
#         conn.sendmail(from_email, recipients, message.as_bytes(linesep='\r\n'))
#     except smtplib.SMTPException:
#         if not fail_silently:
#             raise
#         return False
#     return True


# def renew_yearly_expired_credits():
#     """
#     Deletes all Discounts that are more than a minute old
#     """
#     one_minute_ago = timezone.now() - timezone.timedelta(hour=1)
#     expired_discounts = Discount.objects.filter(
#         created_at__lte=one_minute_ago
#     )
#     expired_discounts.delete()

# @task
# def add(x, y):
#     return x + y


# subs =Subscription.objects.filter(billing_cycle_anchor__year='2021', billing_cycle_anchor__month='12',billing_cycle_anchor__month='10')

# for sub in subs:
#     time =1
#     tomorrow = datetime.utcnow() + timedelta(minutes=time)

#     time+=1
# @task
# def test_tar():
#     for r in range(0,10):
#         tomorrow = datetime.utcnow() + timedelta(minutes=1+r)
#         add.apply_async((r, r+2), eta=tomorrow)
@task(queue='low-priority')
def sync_invoices_and_charges(days):
    queryset = Invoice.objects.annotate(
            diff=ExpressionWrapper(timezone.now() - F('djstripe_updated'), output_field=DurationField())
            ).filter(diff__gt=timedelta(days))
    resync_instances(queryset)
    queryset = Charge.objects.annotate(
            diff=ExpressionWrapper(timezone.now() - F('djstripe_updated'), output_field=DurationField())
            ).filter(diff__gt=timedelta(days))
    resync_instances(queryset)
    
@task(queue='default')
def renewal_list():
    today = timezone.now() + timedelta(1)  
    last_day = calendar.monthrange(today.year,today.month)[1]
    if last_day == today.day:
        cycle_dates = [x for x in range(today.day,32)]
    else:
        cycle_dates = [today.day]
    subs =Subscription.objects.filter(billing_cycle_anchor__day__in =cycle_dates,status='active',plan__interval='year').filter(~Q(billing_cycle_anchor__month=today.month)).filter(~Q(current_period_end__year=today.year ,
                    current_period_end__month=today.month,current_period_end__day__in=cycle_dates))
    logger.info(f"renewal list count {subs.count}")
    for sub in subs:
        renew_user_credits.apply_async((sub.djstripe_id,),eta=sub.billing_cycle_anchor)

@task(queue='default')
def renew_user_credits(sub_id):
    sub =Subscription.objects.get(djstripe_id=sub_id)
    renew_user_credits_yearly(subscription=sub)

@task(queue='low-priority')
def delete_inactive_user_account():
    # AiUser.objects.filter(deactivation_date__date = date.today()).delete()
    users_list = AiUser.objects.filter(deactivation_date__lte = timezone.now())
    for i in users_list:
        i.is_active=False
        i.save()
        # dir = UserAttribute.objects.get(user_id=i.id).allocated_dir
        # os.system("rm -r " +dir)
        # i.delete()
    logger.info("Delete Inactive User")

@task(queue='low-priority')
def delete_express_task_history(): #30days
    queryset = ExpressTaskHistory.objects.annotate(
            diff=ExpressionWrapper(timezone.now() - F('created_at'), output_field=DurationField())
            ).filter(diff__gt=timedelta(30))
    queryset.delete()
    logger.info("Task History Deleted")


# @task
# def find_renewals():
@task(queue='low-priority')
def delete_hired_editors():
    HiredEditors.objects.filter(Q(status = 1)&Q(date_of_expiry__lte = timezone.now())).delete()
    print("deleted")
    logger.info("Delete Hired Editor")


@task(queue='low-priority')
def send_notification_email_for_unread_messages():
    query = Notification.objects.filter(Q(unread = True) & Q(emailed = False) & Q(verb= "Message"))
    try:
        queryset = query.order_by('recipient_id').distinct('recipient_id')
        email_list=[]
        for i in queryset:
           q1 = Notification.objects.filter(Q(unread=True)&Q(verb="Message")&Q(emailed=False)&Q(recipient_id = i.recipient_id))
           q2 = q1.order_by('actor_object_id').distinct('actor_object_id')
           details=[]
           for j in q2:
               actor_obj = AiUser.objects.get(id = j.actor_object_id)
               recent_message = striphtml(j.description) if j.description else None
               details.append({"From":actor_obj.fullname,"Message":recent_message})
           email = AiUser.objects.get(id = i.recipient_id).email
           email_list.append({"email":email,"details":details})
        auth_forms.unread_notification_mail(email_list)
        for k in query:
            k.emailed = True
            k.save()
        logger.info("unread_notification_mail")
    except:
        pass



@task(queue='default')
def email_send_subscription_extension():
    from .user_email_list import extend_list_1
    try:
        global extend_mail_sent
        mail_id=extend_list_1[extend_mail_sent]
        user = AiUser.objects.get(email=mail_id)
        auth_forms.user_trial_extend_mail(user)
        logger.info("email-sent succesfully")
        extend_mail_sent+=1
    except IndexError:
        logger.info("all-email-sent succesfully")



@task(queue='low-priority')
def existing_vendor_onboard_check():
    obj = ExistingVendorOnboardingCheck.objects.filter(mail_sent=False).first()
    if obj:
        status = auth_forms.existing_vendor_onboarding_mail(obj.user,obj.gen_password)
        user_email=obj.user.email
        if status:
            obj.mail_sent=True
            obj.mail_sent_time=timezone.now()
            obj.save()
            logger.info("succesfully sent mail ")
        else:
            logger.info("mail not sent ")
    else:
        logger.info("No record Found ")




@task(queue='low-priority')
def shortlisted_vendor_list_send_email_new(projectpost_id):# needs to include agency's projectowner
    from ai_vendor.models import VendorLanguagePair
    from ai_auth import forms as auth_forms
    instance = ProjectboardDetails.objects.get(id=projectpost_id)
    lang_pair = VendorLanguagePair.objects.none()
    jobs = instance.get_postedjobs
    steps = instance.get_services
    services = ', '.join(steps)
    for obj in jobs:
        if obj.src_lang_id == obj.tar_lang_id:
            query = VendorLanguagePair.objects.filter(Q(source_lang_id=obj.src_lang_id) | Q(target_lang_id=obj.tar_lang_id) & Q(deleted_at=None)).distinct('user')
        else:
            query = VendorLanguagePair.objects.filter(Q(source_lang_id=obj.src_lang_id) & Q(target_lang_id=obj.tar_lang_id) & Q(deleted_at=None)).distinct('user')
        lang_pair = lang_pair.union(query)
    res={}
    for obj in lang_pair:
        tt = obj.source_lang.language if obj.source_lang_id == obj.target_lang_id else obj.target_lang.language
        print(obj.user.fullname)
        if obj.user_id in res:
            res[obj.user_id].get('lang').append({'source':obj.source_lang.language,'target':tt})
        else:
            res[obj.user_id]={'name':obj.user.fullname,'user_email':obj.user.email,'lang':[{'source':obj.source_lang.language,'target':tt}],\
            'project_deadline':instance.proj_deadline.date().strftime("%d-%m-%Y"),'bid_deadline':instance.bid_deadline.date().strftime('%d-%m-%Y'),\
            'proj_post_title':instance.proj_name,'posted_by':instance.customer.fullname,'services':services}
    print("Res----------->",res)
    auth_forms.vendor_notify_post_jobs(res)
    print("mailsent")


@task(queue='default')
def check_dict(dict):
    print("dct------->",dict)
    dict1 = json.loads(dict)
    logger.info("RRRR",dict)

@task(queue='high-priority')
def write_segments_to_db(validated_str_data, document_id): #validated_data

    decoder = json.JSONDecoder(object_pairs_hook=collections.OrderedDict)
    validated_data = decoder.decode(validated_str_data)


    text_unit_ser_data = validated_data.pop("text_unit_ser", [])
    text_unit_ser_data2 = copy.deepcopy(text_unit_ser_data)

    from ai_workspace_okapi.models import Document
    from ai_workspace.api_views import UpdateTaskCreditStatus
    from ai_workspace_okapi.api_views import MT_RawAndTM_View,remove_random_tags
    from ai_workspace_okapi.models import TranslationStatus

    document = Document.objects.get(id=document_id)

    pr_obj = document.job.project
    if pr_obj.pre_translate == True:
        target_get = True
        mt_engine = pr_obj.mt_engine_id
        user = pr_obj.ai_user
    else:target_get = False

    # USING SQL BATCH INSERT

    text_unit_sql = 'INSERT INTO ai_workspace_okapi_textunit (okapi_ref_translation_unit_id, document_id) VALUES {}'.format(
        ', '.join(['(%s, %s)'] * len(text_unit_ser_data)),
    )
    tu_params = []
    for text_unit in text_unit_ser_data:
        tu_params.extend([text_unit["okapi_ref_translation_unit_id"], document_id])

    with closing(connection.cursor()) as cursor:
        cursor.execute(text_unit_sql, tu_params)

    seg_params = []
    seg_count = 0

    from ai_workspace_okapi.models import TextUnit, Segment

    for text_unit in text_unit_ser_data:
        text_unit_id = TextUnit.objects.get(
            Q(okapi_ref_translation_unit_id=text_unit["okapi_ref_translation_unit_id"]) & \
            Q(document_id=document_id)).id
        segs = text_unit.pop("segment_ser", [])

        for seg in segs:
            seg_count += 1
            tagged_source, _, target_tags = (
                set_ref_tags_to_runs(seg["coded_source"],
                                     get_runs_and_ref_ids(seg["coded_brace_pattern"],
                                                          json.loads(seg["coded_ids_sequence"])))
            )
            #target = "" if seg["target"] is None else seg["target"]
            if target_get == False:
                seg['target'] = ""
                seg['temp_target'] = ""
                status_id = None
            else:
                initial_credit = user.credit_balance.get("total_left")
                consumable_credits = MT_RawAndTM_View.get_consumable_credits(document,None,seg['source']) if seg['source']!='' else 0
                if initial_credit > consumable_credits:
                    try:
                        mt = get_translation(mt_engine,str(seg["source"]),document.source_language_code,document.target_language_code,document.owner_pk,cc=consumable_credits)
                        if str(target_tags) != '':
                            random_tags = json.loads(seg["random_tag_ids"])
                            if random_tags == []:tags = str(target_tags)
                            else:tags = remove_random_tags(str(target_tags),random_tags)
                            seg['temp_target'] = mt + tags
                            seg['target'] = mt + tags
                        else:
                            seg['temp_target'] = mt
                            seg['target'] = mt
                        status_id = TranslationStatus.objects.get(status_id=103).id
                        #debit_status, status_code = UpdateTaskCreditStatus.update_credits(user, consumable_credits)
                    except:
                        seg['target']=""
                        seg['temp_target']=""
                        status_id=None
                else:
                    seg['target']=""
                    seg['temp_target']=""
                    status_id=None
            seg_params.extend([str(seg["source"]), seg['target'], seg['temp_target'], str(seg["coded_source"]), str(tagged_source), \
                               str(seg["coded_brace_pattern"]), str(seg["coded_ids_sequence"]), str(target_tags),
                               str(text_unit["okapi_ref_translation_unit_id"]), \
                               timezone.now(), status_id, text_unit_id, str(seg["random_tag_ids"])])

            # seg_params.extend([(seg["source"]), target, "", (seg["coded_source"]), (tagged_source), \
            #                    (seg["coded_brace_pattern"]), (seg["coded_ids_sequence"]), (target_tags),
            #                    (text_unit["okapi_ref_translation_unit_id"]), \
            #                    timezone.now(), text_unit_id, (seg["random_tag_ids"])])

    segment_sql = 'INSERT INTO ai_workspace_okapi_segment (source, target, temp_target, coded_source, tagged_source, \
                               coded_brace_pattern, coded_ids_sequence, target_tags, okapi_ref_segment_id, updated_at, status_id, text_unit_id, random_tag_ids) VALUES {}'.format(
        ', '.join(['(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'] * seg_count))

    with closing(connection.cursor()) as cursor:
        cursor.execute(segment_sql, seg_params)

    logger.info("segments wrriting completed")


    if target_get == True:
        mt_params = []
        count = 0
        segments = Segment.objects.filter(text_unit__document=document) #####Need to check this##########
        for i in segments:
            if i.target != "":
                count += 1
                mt_params.extend([re.sub(r'<[^>]+>', "", i.target),mt_engine,mt_engine,i.id])

        mt_raw_sql = "INSERT INTO ai_workspace_okapi_mt_rawtranslation (mt_raw, mt_engine_id, task_mt_engine_id,segment_id)\
        VALUES {}".format(','.join(['(%s, %s, %s, %s)'] * count))
        if mt_params:
            with closing(connection.cursor()) as cursor:
                cursor.execute(mt_raw_sql, mt_params)
    logger.info("mt_raw wrriting completed")


@task(queue='high-priority')
def mt_only(project_id,token,task_id=None):
    from ai_workspace.models import Project,Task
    from ai_workspace_okapi.api_views import DocumentViewByTask
    from ai_workspace_okapi.serializers import DocumentSerializerV2
    pr = Project.objects.get(id=project_id)
    print("Task------->",task_id)
    print("celerytask-------->",mt_only.request.id)
    print("PRE TRANSLATE-------------->",pr.pre_translate)
    if pr.pre_translate == True:
        if task_id:
            tasks = Task.objects.filter(id=task_id)
        else:
            tasks = pr.get_mtpe_tasks
        print("TASKS Inside CELERY----->",tasks)
        [MTonlytaskCeleryStatus.objects.create(task_name = 'mt_only',task_id = i.id,status=1,celery_task_id=mt_only.request.id) for i in tasks]
        for i in tasks:
            print("I------------->",i)
            document = DocumentViewByTask.create_document_for_task_if_not_exists(i)
            try:
                if document.get('msg') != None:pass
            except:pass
            print("this is mt-only functions tasks")
            # doc = DocumentSerializerV2(document).data
            # print(doc)
            tt = MTonlytaskCeleryStatus.objects.create(task_name = 'mt_only',task_id = i.id,status=2,celery_task_id=mt_only.request.id)
            print("TT------->",tt)
    logger.info('mt-only')




# @task
# def mt_only(project_id,token):
#     from ai_workspace.models import Project,Task
#     from ai_workspace_okapi.api_views import DocumentViewByTask
#     from ai_workspace_okapi.serializers import DocumentSerializerV2
#     pr = Project.objects.get(id=project_id)
#     print("celerytask-------->",mt_only.request.id)
#     print("PRE TRANSLATE-------------->",pr.pre_translate)
#     if pr.pre_translate == True:
#         tasks = pr.get_mtpe_tasks
#         print("TASKS Inside CELERY----->",tasks)
#         print("this is mt-only functions projects")
#         #[MTonlytaskCeleryStatus.objects.get_or_create(task_name = 'mt_only',task_id = i.id,status=1,defaults={'celery_task_id':mt_only.request.id}) for i in pr.get_mtpe_tasks]
#         for i in pr.get_mtpe_tasks:
#             print("I------------->",i)
#             mt_obj = MTonlytaskCeleryStatus.objects.filter(task_name = 'mt_only',task_id = i.id).last()
#             if not mt_obj or mt_obj.status == 2:
#                 print("New")
#                 created = MTonlytaskCeleryStatus.objects.create(task_name = 'mt_only',task_id = i.id,status=1,celery_task_id = mt_only.request.id)
#                 document = DocumentViewByTask.create_document_for_task_if_not_exists(i)
#             else:
#                 print("Inside Else")
#                 print("sts--->",mt_obj.status) 
#                 print("doc-------->",mt_obj.task.document)
#             try:
#                 if document.get('msg') != None:pass
#             except:pass
#             print("this is mt-only functions tasks")
#             tt = MTonlytaskCeleryStatus.objects.create(task_name = 'mt_only',task_id = i.id,status=2,celery_task_id=mt_only.request.id)
#             print("TT------->",tt)
#     logger.info('mt-only')
# # @task
# @shared_task(bind=True)
# def mt_only(self, project_id,token):
# # def mt_only(project_id, token):
#     from ai_workspace.models import Project,Task
#     from ai_workspace_okapi.api_views import DocumentViewByTask
#     from ai_workspace_okapi.serializers import DocumentSerializerV2
#     pr = Project.objects.get(id=project_id)
#
#     progress_recorder = ProgressRecorder(self)
#     # progress_recorder = ProgressRecorder()
#
#
#     if pr.pre_translate == True:
#         tasks = pr.get_mtpe_tasks
#
#         [MTonlytaskCeleryStatus.objects.create(task_name = 'mt_only',task_id = i.id,status=1,\
#                                                celery_task_id=mt_only.request.id) for i in pr.get_mtpe_tasks]
#         j = 1
#         for i in pr.get_mtpe_tasks:
#             document = DocumentViewByTask.create_document_for_task_if_not_exists(i)
#             doc = DocumentSerializerV2(document).data
#             sleep(20)
#
#             progress_recorder.set_progress(j, len(pr.get_mtpe_tasks), f'MT ongoing for {i}')
#             j += 1
#
#             MTonlytaskCeleryStatus.objects.create(task_name = 'mt_only',task_id = i.id,status=2,celery_task_id=mt_only.request.id)
#
#     return "Finished Pre-translation"

@task(queue='high-priority')
def write_doc_json_file(doc_data, task_id):

    from ai_workspace.serializers import TaskSerializer
    task = Task.objects.get(id=task_id)
    data = TaskSerializer(task).data
    from ai_workspace_okapi.api_views import DocumentViewByTask
    DocumentViewByTask.correct_fields(data)
    params_data = {**data, "output_type": None}

    source_file_path = params_data["source_file_path"]
    path_list = re.split("source/", source_file_path)
    if not os.path.exists(os.path.join(path_list[0], "doc_json")):
        os.mkdir(os.path.join(path_list[0], "doc_json"))
    doc_json_path = path_list[0] + "doc_json/" + path_list[1] + ".json"

    with open(doc_json_path, "w") as outfile:
        json.dump(doc_data, outfile)
    logger.info("Document json data written as a file")


@task(queue='high-priority')
def text_to_speech_long_celery(consumable_credits,user_id,file_path,task_id,language,voice_gender,voice_name):
    from ai_workspace.api_views import text_to_speech_task,long_text_source_process
    obj = Task.objects.get(id=task_id)
    user = AiUser.objects.get(id=user_id)
    MTonlytaskCeleryStatus.objects.create(task_id = obj.id,status=1,celery_task_id=text_to_speech_long_celery.request.id,task_name = "text_to_speech_long_celery")
    #tt = text_to_speech_task(obj,language,gender,user,voice_name)
    tt = long_text_source_process(consumable_credits,user,file_path,obj,language,voice_gender,voice_name)
    #MTonlytaskCeleryStatus.objects.create(task_id = obj.id,status=2,celery_task_id=text_to_speech_celery.request.id,task_name = "text_to_speech_celery")

    logger.info("Text to speech called")
    # if tt.status_code == 400:
    #     return tt.status_code



@task(queue='high-priority')
def google_long_text_file_process_cel(consumable_credits,document_user_id,file_path,task_id,target_language,voice_gender,voice_name):
    from ai_workspace_okapi.api_views import long_text_process
    document_user = AiUser.objects.get(id = document_user_id)
    obj = Task.objects.get(id=task_id)
    MTonlytaskCeleryStatus.objects.create(task_id=obj.id,status=1,task_name='google_long_text_file_process_cel',celery_task_id=google_long_text_file_process_cel.request.id)
    tr = long_text_process(consumable_credits,document_user,file_path,obj,target_language,voice_gender,voice_name)
    #MTonlytaskCeleryStatus.objects.create(task_id=task.id,status=2,task_name='google_long_text_file_process_cel',celery_task_id=google_long_text_file_process_cel.request.id)
    logger.info("Text to speech document called")


@task(queue='high-priority')
def transcribe_long_file_cel(speech_file,source_code,filename,task_id,length,user_id,hertz):
    from ai_workspace.api_views import transcribe_long_file
    obj = Task.objects.get(id = task_id)
    user = AiUser.objects.get(id = user_id)
    MTonlytaskCeleryStatus.objects.create(task_id=obj.id,status=1,task_name='transcribe_long_file_cel',celery_task_id=transcribe_long_file_cel.request.id)
    transcribe_long_file(speech_file,source_code,filename,obj,length,user,hertz)
    logger.info("Transcribe called")




@task(queue='high-priority')
def pre_translate_update(task_id):
    from ai_workspace.models import Task, TaskAssign
    from ai_workspace_okapi.models import Document,Segment,TranslationStatus,MT_RawTranslation,MtRawSplitSegment
    from ai_workspace.api_views import UpdateTaskCreditStatus
    from ai_workspace_okapi.api_views import MT_RawAndTM_View,get_tags
    from ai_workspace_okapi.models import MergeSegment,SplitSegment
    #from ai_workspace_okapi.api_views import DocumentViewByTask
    from itertools import chain

    task = Task.objects.get(id=task_id)
    MTonlytaskCeleryStatus.objects.create(task_id = task_id,task_name='pre_translate_update',status=1,celery_task_id=pre_translate_update.request.id)
    user = task.job.project.ai_user
    mt_engine = task.job.project.mt_engine_id
    task_mt_engine_id = TaskAssign.objects.get(Q(task=task) & Q(step_id=1)).mt_engine.id
    # if task.document == None:
    #     document = DocumentViewByTask.create_document_for_task_if_not_exists(task)
    segments = task.document.segments_for_find_and_replace
    merge_segments = MergeSegment.objects.filter(text_unit__document=task.document)
    split_segments = SplitSegment.objects.filter(text_unit__document=task.document)

    final_segments = list(chain(segments, merge_segments, split_segments))

    update_list, update_list_for_merged,update_list_for_split = [],[],[]
    mt_segments, mt_split_segments = [],[]
    
    for seg in final_segments:###############Need to revise####################

        if seg.target == '' or seg.target==None:
            initial_credit = user.credit_balance.get("total_left")
            consumable_credits = MT_RawAndTM_View.get_consumable_credits(task.document, seg.id, None)
            if initial_credit > consumable_credits:
                try:
                    mt = get_translation(mt_engine, seg.source, task.document.source_language_code, task.document.target_language_code,user_id=task.owner_pk,cc=consumable_credits)
                    tags = get_tags(seg)
                    if tags:
                        seg.target = mt + tags
                        seg.temp_target = mt + tags
                    else:
                        seg.target = mt
                        seg.temp_target = mt
                    seg.status_id = TranslationStatus.objects.get(status_id=103).id
                    #debit_status, status_code = UpdateTaskCreditStatus.update_credits(user, consumable_credits)
                    if type(seg) is SplitSegment:
                        mt_split_segments.append(seg)
                    else:mt_segments.append(seg)
                except:
                    seg.target = ''
                    seg.temp_target = ''
                    seg.status_id=None
            else:
                MTonlytaskCeleryStatus.objects.create(task_id = task_id,task_name='pre_translate_update',status=1,celery_task_id=pre_translate_update.request.id,error_type="Insufficient Credits")
                break
            if type(seg) is Segment:
                update_list.append(seg)
            elif type(seg) is SplitSegment:
                update_list_for_split.append(seg)
            elif type(seg) is MergeSegment:
                update_list_for_merged.append(seg)

    Segment.objects.bulk_update(update_list,['target','temp_target','status_id'])
    MergeSegment.objects.bulk_update(update_list_for_merged,['target','temp_target','status_id'])
    SplitSegment.objects.bulk_update(update_list_for_split,['target','temp_target','status_id'])

    instances = [
            MT_RawTranslation(
                mt_raw= re.sub(r'<[^>]+>', "", i.target),
                mt_engine_id = mt_engine,
                task_mt_engine_id = mt_engine,
                segment_id= i.id,
            )
            for i in mt_segments
        ]

    MT_RawTranslation.objects.bulk_create(instances, ignore_conflicts=True)

    instances_1 = [
            MtRawSplitSegment(
                mt_raw= re.sub(r'<[^>]+>', "", i.target),
                split_segment_id= i.id,
            )
            for i in mt_split_segments
        ]
    MtRawSplitSegment.objects.bulk_create(instances_1, ignore_conflicts=True)
    #MTonlytaskCeleryStatus.objects.create(task_id = task_id,status=2,celery_task_id=pre_translate_update.request.id)
    logger.info("pre_translate_update")


@task(queue='low-priority')
def update_untranslatable_words(untranslatable_file_id):
    from ai_qa.models import Untranslatable,UntranslatableWords
    file = Untranslatable.objects.get(id=untranslatable_file_id)
    UntranslatableWords.objects.filter(file_id = untranslatable_file_id).update(job=file.job)
    logger.info("untranslatable words updated")

@task(queue='low-priority')
def update_forbidden_words(forbidden_file_id):
    from ai_qa.models import Forbidden,ForbiddenWords
    file = Forbidden.objects.get(id=forbidden_file_id)
    ForbiddenWords.objects.filter(file_id = forbidden_file_id).update(job=file.job)
    logger.info("forbidden words updated")

@task(queue='high-priority')
def project_analysis_property(project_id, retries=0, max_retries=3):
    logger.info("Executing high-priority task")
    from ai_workspace.api_views import ProjectAnalysisProperty
    from ai_workspace.models import Project
    proj = Project.objects.get(id=project_id)
    print("tasks-------->",proj.get_tasks)
    task = proj.get_tasks[0]
    try:
        obj = MTonlytaskCeleryStatus.objects.create(task_id=task.id, project_id=proj.id,status=1,task_name='project_analysis_property',celery_task_id=project_analysis_property.request.id)
        print("GG------->",obj)
        ProjectAnalysisProperty.get(project_id)
        logger.info("analysis property called")
    except Exception as e:
        print(f'Error in task: {e}')
        retries += 1
        print("Retry Count--------->",retries)
        if retries > max_retries:
            raise MaxRetriesExceededError("Maximum retries reached.") from e
            logger.info("retries exceeded")



@task(queue='medium-priority')
def analysis(tasks,project_id):
    from ai_workspace.models import Project,Task
    from ai_tm.models import WordCountGeneral,WordCountTmxDetail,CharCountGeneral
    from ai_tm.api_views import get_json_file_path,get_tm_analysis,get_word_count
    proj = Project.objects.get(id=project_id)
    for task_id in tasks:
        MTonlytaskCeleryStatus.objects.create(task_name = 'analysis',task_id = task_id,status=1,celery_task_id=analysis.request.id)
        task = Task.objects.get(id=task_id)
        file_path = get_json_file_path(task)
        doc_data = json.load(open(file_path))
        if type(doc_data) == str:
            doc_data = json.loads(doc_data)
        raw_total = doc_data.get('total_word_count')
        tm_analysis,files_list = get_tm_analysis(doc_data,task.job)
        #print("Tm Analysis----------->",tm_analysis)
        if tm_analysis:
            word_count = get_word_count(tm_analysis,proj,task)
            print("WordCount------------>",word_count)
        else:
            word_count = WordCountGeneral.objects.create(project_id =project_id,tasks_id=task.id,\
                        new_words=doc_data.get('total_word_count'),raw_total=raw_total)
            char_count = CharCountGeneral.objects.create(project_id =project_id,tasks_id=task.id,\
                        new_words=doc_data.get('total_char_count'),raw_total=doc_data.get('total_char_count'))
        [WordCountTmxDetail.objects.create(word_count=word_count,tmx_file_id=i,tmx_file_obj_id=i) for i in files_list]
        MTonlytaskCeleryStatus.objects.create(task_name = 'analysis',task_id = task.id,status=2,celery_task_id=analysis.request.id)
    logger.info("Analysis completed")


@task(queue='medium-priority')
def count_update(job_id):
    from ai_workspace.models import Task
    from ai_tm.api_views import get_weighted_char_count,get_weighted_word_count,notify_word_count
    task_obj = Task.objects.filter(job_id=job_id)
    for obj in task_obj:
        for assigns in obj.task_info.filter(task_assign_info__isnull = False):
            existing_wc = assigns.task_assign_info.billable_word_count
            existing_cc = assigns.task_assign_info.billable_char_count
            word_count = get_weighted_word_count(obj)
            print("wc----------->",word_count)
            char_count = get_weighted_char_count(obj)
            print("cc------------>",char_count)
            if assigns.task_assign_info.account_raw_count == False:
                if assigns.status == 1:
                    assigns.task_assign_info.billable_word_count = word_count
                    assigns.task_assign_info.billable_char_count = char_count
                    assigns.task_assign_info.save()
                    po_modify_weigted_count([assigns.task_assign_info])
                    if assigns.task_assign_info.mtpe_count_unit_id != None:
                        if assigns.task_assign_info.mtpe_count_unit_id == 1:
                            print("######################",existing_wc,existing_cc,word_count,char_count)
                            if existing_wc != word_count:
                                print("Inside if calling notify")
                                notify_word_count(assigns,word_count,char_count)
                        else:
                            print("$$$$$$$$$$$$$$$$$$$$$$$$")
                            if existing_cc != char_count:
                                print("Inside else calling notify")
                                notify_word_count(assigns,word_count,char_count)
                    #print("wc,cc--------->",assigns.task_assign_info.billable_word_count,assigns.task_assign_info.billable_char_count)
    logger.info('billable count updated')



@task(queue='high-priority')
def mt_raw_update(task_id):
    from ai_workspace.models import Task, TaskAssign
    from ai_workspace_okapi.models import Document,Segment,TranslationStatus,MT_RawTranslation,MtRawSplitSegment
    from ai_workspace.api_views import UpdateTaskCreditStatus
    from ai_workspace_okapi.api_views import MT_RawAndTM_View,get_tags
    from ai_workspace_okapi.models import MergeSegment,SplitSegment
    #from ai_workspace_okapi.api_views import DocumentViewByTask
    from itertools import chain

    task = Task.objects.get(id=task_id)
    MTonlytaskCeleryStatus.objects.create(task_id = task_id,task_name='mt_raw_update',status=1,celery_task_id=mt_raw_update.request.id)
    user = task.job.project.ai_user
    print("AiUser--->",user)
    mt_engine = task.job.project.mt_engine_id
    task_mt_engine_id = TaskAssign.objects.get(Q(task=task) & Q(step_id=1)).mt_engine.id
    segments = task.document.segments_for_find_and_replace
    merge_segments = MergeSegment.objects.filter(text_unit__document=task.document)
    split_segments = SplitSegment.objects.filter(text_unit__document=task.document)

    final_segments = list(chain(segments, merge_segments, split_segments))

    update_list, update_list_for_merged,update_list_for_split = [],[],[]
    mt_segments, mt_split_segments = [],[]
    
    for seg in final_segments:###############Need to revise####################
        try:
            if (type(seg) is Segment) or (type(seg) is MergeSegment):
                mt_raw = seg.seg_mt_raw
            else:
                if seg.mt_raw_split_segment.exists() == False:
                    mt_raw = None
                else:
                    mt_raw = seg.mt_raw_split_segment.first().mt_raw
        except:
            mt_raw = None
        print("Seg---------->",seg) 
        print("MtRw---------->",mt_raw)
        if mt_raw == None:
            print("Inside mt raw none")
            if seg.target == '' or seg.target==None:
                print("**********************")
                initial_credit = user.credit_balance.get("total_left")
                print("Intial Credit------------->",initial_credit)
                consumable_credits = MT_RawAndTM_View.get_consumable_credits(task.document, seg.id, None)
                if initial_credit > consumable_credits:
                    try:
                        mt = get_translation(mt_engine, seg.source, task.document.source_language_code, task.document.target_language_code,user_id=task.owner_pk,cc=consumable_credits)
                        tags = get_tags(seg)
                        if tags:
                            seg.target = mt + tags
                            seg.temp_target = mt + tags
                        else:
                            seg.target = mt
                            seg.temp_target = mt
                        seg.status_id = TranslationStatus.objects.get(status_id=103).id
                        #debit_status, status_code = UpdateTaskCreditStatus.update_credits(user, consumable_credits)
                        if type(seg) is SplitSegment:
                            mt_split_segments.append({'seg':seg,'mt':mt})
                        else:mt_segments.append({'seg':seg,'mt':mt})
                    except:
                        seg.target = ''
                        seg.temp_target = ''
                        seg.status_id=None
                else:
                    MTonlytaskCeleryStatus.objects.create(task_id = task_id,task_name='mt_raw_update',status=1,celery_task_id=mt_raw_update.request.id,error_type="Insufficient Credits")
                    print("Insufficient")
                    break
                if type(seg) is Segment:
                    update_list.append(seg)
                elif type(seg) is SplitSegment:
                    update_list_for_split.append(seg)
                elif type(seg) is MergeSegment:
                    update_list_for_merged.append(seg)
            else:
                initial_credit = user.credit_balance.get("total_left")
                consumable_credits = MT_RawAndTM_View.get_consumable_credits(task.document, seg.id, None)
                if initial_credit > consumable_credits:
                    mt = get_translation(mt_engine, seg.source, task.document.source_language_code, task.document.target_language_code,user_id=task.owner_pk,cc=consumable_credits)
                    if type(seg) is SplitSegment:
                        mt_split_segments.append({'seg':seg,'mt':mt})
                    else:mt_segments.append({'seg':seg,'mt':mt})
                else:
                    print("Insufficient credits")
                
    print("UL->",mt_segments)
    Segment.objects.bulk_update(update_list,['target','temp_target','status_id'])
    MergeSegment.objects.bulk_update(update_list_for_merged,['target','temp_target','status_id'])
    SplitSegment.objects.bulk_update(update_list_for_split,['target','temp_target','status_id'])
    print("mt----------?",mt_segments)
    instances = [
            MT_RawTranslation(
                mt_raw= re.sub(r'<[^>]+>', "", i['mt']),
                mt_engine_id = mt_engine,
                task_mt_engine_id = mt_engine,
                segment_id= i['seg'].id,
            )
            for i in mt_segments
        ]

    tt = MT_RawTranslation.objects.bulk_create(instances, ignore_conflicts=True)
    print("norm and merg--------->",tt)
    print("mt_split------------->",mt_split_segments)
    instances_1 = [
            MtRawSplitSegment(
                mt_raw= re.sub(r'<[^>]+>', "", i['mt']),
                split_segment_id= i['seg'].id,
            )
            for i in mt_split_segments
        ]
    tr = MtRawSplitSegment.objects.bulk_create(instances_1, ignore_conflicts=True)
    print("split-------->",tr)
    #MTonlytaskCeleryStatus.objects.create(task_id = task_id,status=2,celery_task_id=pre_translate_update.request.id)
    logger.info("mt_raw_update")







@task(queue='medium-priority')
def weighted_count_update(receiver,sender,assignment_id):
    from ai_workspace import forms as ws_forms
    from ai_workspace.models import TaskAssignInfo
    from ai_tm.api_views import get_weighted_char_count,get_weighted_word_count,notify_word_count
    task_assgn_objs = TaskAssignInfo.objects.filter(assignment_id = assignment_id)
    task_assign_obj_ls=[]
    for obj in task_assgn_objs:
        existing_wc = obj.task_assign.task_assign_info.billable_word_count
        existing_cc = obj.task_assign.task_assign_info.billable_char_count
        if obj.account_raw_count == False:
            word_count = get_weighted_word_count(obj.task_assign.task)
            char_count = get_weighted_char_count(obj.task_assign.task)
        else:
            word_count = obj.task_assign.task.task_word_count
            char_count = obj.task_assign.task.task_char_count
        obj.billable_char_count =  char_count
        obj.billable_word_count = word_count
        obj.save()

        if existing_wc != word_count and existing_cc != char_count:
            task_assign_obj_ls.append(obj)

        try:
            if receiver !=None and sender!=None:
                print("------------------POST-----------------------------------")
                Receiver = AiUser.objects.get(id = receiver)
                receivers = []
                receivers =  Receiver.team.get_project_manager if (Receiver.team and Receiver.team.owner.is_agency) else []
                receivers.append(Receiver)
                print("Receivers in TaskAssign----------->", receivers)
                Sender = AiUser.objects.get(id = sender)
                hired_editors = Sender.get_hired_editors if Sender.get_hired_editors else []
                for i in [*set(receivers)]:
                    if i in hired_editors or (i.team and i.team.owner) in hired_editors:
                        ws_forms.task_assign_detail_mail(i,assignment_id)
            else:
                print("------------------------PUT------------------------------")
                assigns = task_assgn_objs[0].task_assign
                if assigns.task_assign_info.mtpe_count_unit_id != None:
                    if assigns.task_assign_info.mtpe_count_unit_id == 1:
                        if existing_wc != word_count:
                            notify_word_count(assigns,word_count,char_count)
                    else:
                        if existing_cc != char_count:
                            notify_word_count(assigns,word_count,char_count)
        except:
            print("<---------Notification error------------->")
            pass
    logger.info('billable count updated and mail sent')

    if len(task_assign_obj_ls) != 0:
         po_modify_weigted_count(task_assign_obj_ls)


@task
def check_test():
    sleep(1000)
# @task
# def get_word_count_cel(tm_analysis,proj,task,raw_total):
#     from ai_tm.api_views import get_word_count
#     MTonlytaskCeleryStatus.objects.create(task_name = 'analysis',task_id = task,status=1,celery_task_id=analysis.request.id)
#     word_count = get_word_count(tm_analysis,proj,task,raw_total)
#     print("WordCount------------>",word_count)
#     logger.info("Analysis completed")


@task(queue='low-priority')
def backup_media():
    if os.getenv('MEDIA_BACKUP')=='True':   
        call_command('mediabackup','--clean')
    logger.info("backeup of mediafiles successfull.")
    
@task(queue='default')
def mail_report():
    from ai_auth.reports import AilaysaReport
    report = AilaysaReport()
    report.report_generate()
    report.send_report()

@task(queue='low-priority')
def record_api_usage(provider,service,uid,email,usage):
    from ai_auth.utils import record_usage
    record_usage(provider,service,uid,email,usage)

from ai_glex import models as glex_model
from tablib import Dataset
@task(queue='high-priority')
def update_words_from_template_task(file_ids):
    print("File Ids--->",file_ids)
    for i in file_ids:
        instance = glex_model.GlossaryFiles.objects.get(id=i)
        glossary_obj = instance.project.glossary_project#glex_model.Glossary.objects.get(project_id = instance.project_id)
        dataset = Dataset()
        imported_data = dataset.load(instance.file.read(), format='xlsx')
        if instance.source_only == False and instance.job.source_language != instance.job.target_language:
            for data in imported_data:
                if data[2]:
                    try:
                        value = glex_model.TermsModel(
                                # data[0],          #Blank column
                                data[1],            #Autoincremented in the model
                                data[2].strip(),    #SL term column
                                data[3].strip() if data[3] else data[3],    #TL term column
                                data[4], data[5], data[6], data[7], data[8], data[9],
                                data[10], data[11], data[12], data[13], data[14], data[15]
                        )
                    except:
                        value = glex_model.TermsModel(
                                # data[0],          #Blank column
                                data[1],            #Autoincremented in the model
                                data[2].strip(),    #SL term column
                                data[3].strip() if data[3] else data[3], )
                    value.glossary_id = glossary_obj.id
                    value.file_id = instance.id
                    value.job_id = instance.job_id
                    value.save()
                    #print("ID----------->",value.id)
        else:
            for data in imported_data:
                print("Data in else------->",data)
                if data[2]:
                        value = glex_model.TermsModel(
                                # data[0],          #Blank column
                                data[1],            #Autoincremented in the model
                                data[2].strip()
                                )
                value.glossary_id = glossary_obj.id
                value.file_id = instance.id
                value.job_id = instance.job_id
                value.save()
                #print("ID----------->",value.id)
        print("Terms Uploaded")


def diff_month(d1, d2):
    return (d1.year - d2.year) * 12 + d1.month - d2.month

@task(queue='low-priority')
def sync_user_details_bi(test=False,is_vendor=False):
    from ai_auth.reports import AilaysaReport
    from ai_bi.models import AiUserDetails,UsedLangPairs
    users = AiUser.objects.all()
    rep = AilaysaReport()
    users = rep.get_users(is_vendor=is_vendor,test=test)
    

    for user in users:
        data  = dict()
        data2 = dict()
        data = {
            "email":user.email,
            "fullname":user.fullname,
            "country":user.country.name if user.country!=None else None,
            "is_staff":user.is_staff,
            "is_active": user.is_active,
            "deactivation_date":user.deactivation_date,
            "date_joined":user.date_joined,
            "last_login":user.last_login,
            "deactivate":user.deactivate,
            "is_vendor":user.is_vendor,
            "is_agency":user.is_agency,
            "is_internal_member":user.is_internal_member,
            "first_login":user.first_login,
            "currency_based_on_country":user.currency_based_on_country.currency if user.currency_based_on_country!=None else None,
            "signup_age":abs(diff_month(user.date_joined,timezone.now()))
            }
        sub = rep.get_user_subscription(user)
        if sub!=None:
            data.update({
            "subscription_name":sub.plan.product.name,
            "subscription_status":sub.status,
            "subscription_start":sub.current_period_start,
            "subscription_end":sub.current_period_end
            })
        credits = rep.get_user_credits(user)
        if credits != None:
            data.update({
            "intial_credits":credits[0],
            "credits_left":credits[2],
            "credits_consumed":credits[1]
            })

        proj_counts = rep.get_project_counts(user)
        if proj_counts!=None:
            data.update({
            "projects_created":proj_counts[0],
            "documents_created":proj_counts[1],
            "pdf_conversion":proj_counts[2],
            "blogs_created":proj_counts[3],
            })
        
        # obj, created =AiUserDetails.objects.using("bi").update_or_create(**data)

        # try:
        #     user_det = AiUserDetails.objects.get(email=user.email)
        # except AiUserDetails.DoesNotExist:
        #     user_det = AiUserDetails(**data)
        #     user_det.save(using="bi")



        objs = AiUserDetails.objects.using("bi").filter(email=data["email"])
        if objs.count() != 0:
            objs.using("bi").update(**data)
        else:
            user_det = AiUserDetails(**data)
            user_det.save(using="bi")

        user_det = AiUserDetails.objects.using("bi").get(email=data["email"])
        lang_pairs = rep.get_language_pair_used(user)
        if len(lang_pairs) != 0:
            # data['language_pairs_used']=','.join(lang_pairs)
            for lang in lang_pairs:
                data2['user_detail'] = user_det
                pairs = lang.split('->')
                data2['source_lang'] = pairs[0]
                if len(pairs)!=1:
                    data2['target_lang'] = pairs[1]
                user_lang = UsedLangPairs(**data2)
                user_lang.save(using="bi")


def proz_list_send_email(projectpost_id):
    instance = ProjectboardDetails.objects.get(id=projectpost_id)
    jobs = instance.get_postedjobs
    steps = instance.get_services
    services = ', '.join(steps)
    headers = {'X-Proz-API-Key': os.getenv("PROZ-KEY"),}
    limit = 25
    for obj in jobs:
        source_lang = obj.source_language_id
        target_lang = obj.target_language_id
        lang_pair = get_proz_lang_pair(source_lang,target_lang)
        offset = (int(page) - 1) * int(limit)
        params = {
            'language_service_id':1,
            'language_pair':lang_pair,
            'limit':limit,
            'offset':offset
            }
        integration_api_url = "https://api.proz.com/v2/freelancer-matches"
        response = requests.request("GET", integration_api_url, headers=headers, params=params)
        if response and response.get('success') == 1:
            uuids = []
            for vendor in response.get('data'):
                uuids.append(vendor.get('freelancer').get('uuid'))
        user = instance.customer
        message = 'Customer Posted project with this language pair. project_title '+instance.proj_name+ ' with biddeadline '+instance.bid_deadline.date().strftime('%d-%m-%Y')+ '. You can bid the project and win. Visit Ailaysa for more details.'
        subject = request.POST.get('subject', 'Message from Ailaysa Test' )
        headers = {'X-Proz-API-Key': os.getenv("PROZ-KEY"),}
        url = "https://api.proz.com/v2/messages"
        payload = {'recipient_uuids': uuids,
                    'sender_email': user.email ,
                    'body': message,
                    'subject': subject,
                    'sender_name': user.fullname}
        print("Payload------------->",payload)
        #response = requests.request("POST", url, headers=headers, data=payload)
    return Response({'msg':'email sent'})