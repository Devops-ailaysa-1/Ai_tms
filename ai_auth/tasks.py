from ai_pay.api_views import po_modify_weigted_count
from celery.utils.log import get_task_logger
import celery,re,pickle, copy
import djstripe
logger = get_task_logger('django')
from celery.decorators import task
from ai_openai.utils import get_consumable_credits_for_openai_text_generator
from celery import shared_task, group, chord
from datetime import date
from django.utils import timezone
from .models import AiUser,UserAttribute,HiredEditors,ExistingVendorOnboardingCheck,PurchasedUnits,CareerSupportAI,AilaysaCallCenter
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
from ai_workspace.models import Task, TrackSegmentsBatchStatus,TrackSegmentsBatchStatus
from ai_workspace.enums import BatchStatus
from ai_auth.api_views import resync_instances
import os, json
from ai_workspace_okapi.utils import set_ref_tags_to_runs, get_runs_and_ref_ids, get_translation
from ai_workspace.models import Task,MTonlytaskCeleryStatus, Project
import os, json
from datetime import datetime, timedelta
from django.db.models import DurationField, F, ExpressionWrapper,Q
#from translate.storage.tmx import tmxfile
from time import sleep
from django.core.management import call_command
import calendar
from ai_workspace.models import ExpressTaskHistory
from celery.exceptions import MaxRetriesExceededError
from ai_auth.signals import purchase_unit_renewal
from django.conf import settings
from django.db import transaction
from django_celery_results.models import TaskResult
from django.db import connection
from ai_workspace.enums import AdaptiveFileTranslateStatus, BatchStatus
import time
from django.db.models.functions import Lower
from ai_workspace.utils import AdaptiveSegmentTranslator

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
    subs =Subscription.objects.filter(billing_cycle_anchor__day__in =cycle_dates,status='active',plan__interval='year').filter(
                                ~Q(billing_cycle_anchor__month=today.month)).filter(~Q(current_period_end__year=today.year,
                                current_period_end__month=today.month,current_period_end__day__in=cycle_dates))
    logger.info(f"renewal list count {subs.count}")
    for sub in subs:
        renew_user_credits.apply_async((sub.djstripe_id,),eta=sub.billing_cycle_anchor)

@task(queue='default')
def renew_user_credits(sub_id):
    sub =Subscription.objects.get(djstripe_id=sub_id)
    renew_user_credits_yearly(subscription=sub)

@task(queue='default')
def renewal_list_daily_renewal():
    today = timezone.now() + timedelta(1)  
    last_day = calendar.monthrange(today.year,today.month)[1]
    if last_day == today.day:
        cycle_dates = [x for x in range(today.day,32)]
    else:
        cycle_dates = [today.day]
    # subs =Subscription.objects.filter(billing_cycle_anchor__day__in =cycle_dates,status='active',plan__interval='year').filter(~Q(billing_cycle_anchor__month=today.month)).filter(~Q(current_period_end__year=today.year ,
    #                 current_period_end__month=today.month,current_period_end__day__in=cycle_dates))
    pu_list =PurchasedUnits.objects.filter(~Q(expiry__year=today.year,
                    expiry__month=today.month,expiry__day__in=cycle_dates)).filter(purchase_pack__recurring='daily')
    logger.info(f"renewal list count {pu_list.count}")
    for pu in pu_list:
        created_at_time =  pu.buyed_at.time()
        execute_at = datetime.combine(today.date(), created_at_time, tzinfo=pu.buyed_at.tzinfo)
        renew_purchase_units.apply_async((pu.id,),eta=execute_at)


@task(queue='default')
def renew_purchase_units(pu_id):
    pu =PurchasedUnits.objects.get(id=pu_id)
    purchase_unit_renewal(pu_instance=pu)

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
    '''
    This task is to delete instant_task_history after 30 days
    '''
    queryset = ExpressTaskHistory.objects.annotate(
            diff=ExpressionWrapper(timezone.now() - F('created_at'), output_field=DurationField())
            ).filter(diff__gt=timedelta(30))
    queryset.delete()
    logger.info("Task History Deleted")


# @task
# def find_renewals():
@task(queue='low-priority')
def delete_hired_editors():
    '''
    This is to delete hired editors invite if he didn't accept for more than 7 days.
    '''
    HiredEditors.objects.filter(Q(status = 1)&Q(date_of_expiry__lte = timezone.now())).delete()    
    logger.info("Delete Hired Editor")


@task(queue='low-priority')
def send_notification_email_for_unread_messages():
    '''
    This task is to send notification to the users when they have unread messages in chat.
    '''
    from ai_workspace.api_views import AddStoriesView
    query = Notification.objects.filter(Q(unread = True) & Q(emailed = False) & Q(verb= "Message"))
    try:
        queryset = query.order_by('recipient_id').distinct('recipient_id')
        email_list=[]
        for i in queryset:
            q1 = Notification.objects.filter(Q(unread=True)&Q(verb="Message")&Q(emailed=False)&Q(recipient_id = i.recipient_id))
            q2 = q1.order_by('actor_object_id').distinct('actor_object_id')
            #if not AddStoriesView.check_user_dinamalar(i.recipient):
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
def existing_vendor_onboard_check(): # For Vendor check. Not using now
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
def send_bootcamp_mail(obj_id):
    '''
    This task is to send thanks message to the user after registering in camp
    and notification mail to hr that user is registered.
    '''
    from .models import MarketingBootcamp
    from ai_auth import forms as auth_forms
    instance = MarketingBootcamp.objects.get(id=obj_id)
    if instance.file:
        file_path = instance.file.path
    else:
        file_path = None
    sent = auth_forms.bootcamp_marketing_ack_mail(user_name = instance.name,
                                            user_email=instance.email,
                                            file_path=file_path)
    auth_forms.bootcamp_marketing_response_mail(user_name=instance.name,
                                                user_email=instance.email)
    if sent:
        logger.info("Mail sent")
    else:
        logger.info('Mail Not sent')


@task(queue='low-priority')
def send_career_mail(obj_id):
    '''
    This task is to send thanks message to the user after submitting career form
    and notification mail to hr that user is registered.
    '''
    from ai_auth.api_views import send_email, career_support_thank_mail
    instance = CareerSupportAI.objects.get(id=obj_id)
    subject = "New Registration for AI/ML Openings"
    template = 'career_support_email.html'
    email = 'hr@ailaysa.com'
    context = {'name':instance.name,'email':instance.email,'college':instance.college,'applied_for':instance.get_apply_for_display(),'file':instance.cv_file}
    send_email(subject,template,context,email)
    career_support_thank_mail(instance.name,instance.email)


##### delete this ailaysa instance after email sent to admin
def delete_ailaysa_call_center_instance(instance):
    file_path = []
    for i in instance.ailaysa_call_ctr.all():
        file_path.append(i.file.path)
    
    instance.delete()
    for i in file_path:
        os.remove(i)

@task(queue='low-priority')
def send_ailaysa_call_center(obj_id):
    from ai_auth.api_views import send_email
    instance = AilaysaCallCenter.objects.get(id=obj_id)

    template_detail = 'ailaysa_call_center_details.html'
    email = 'sales@langsmart.com'
    cc = 'senthil.nathan@ailaysa.com'

    context_for_sales = {'name':instance.name,'email':instance.email,
               'company_name':instance.company_name,'address':instance.address,'service_type':instance.service_type,
               'source_language':instance.source_language,'target_language':instance.target_language,
               'service_description':instance.service_description,
               'phone_number':instance.phone_number,'whatsapp_number': instance.whatsapp_number,
               'file':instance.ailaysa_call_ctr.all()}
    
    subject_contact_sale = "Sales ({})".format(instance.name) 
    send_email(subject_contact_sale,template_detail,context_for_sales,email,cc)
    delete_ailaysa_call_center_instance(instance=instance)





@task(queue='low-priority')
def shortlisted_vendor_list_send_email_new(projectpost_id):# needs to include agency's projectowner
    '''
    This task is to send email to all the shortlisted vendors about project post in marketplace
    '''
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
        if obj.user_id in res:
            res[obj.user_id].get('lang').append({'source':obj.source_lang.language,'target':tt})
        else:
            res[obj.user_id]={'name':obj.user.fullname,'user_email':obj.user.email,'lang':[{'source':obj.source_lang.language,'target':tt}],\
            'project_deadline':instance.proj_deadline.date().strftime("%d-%m-%Y"),'bid_deadline':instance.bid_deadline.date().strftime('%d-%m-%Y'),\
            'proj_post_title':instance.proj_name,'posted_by':instance.customer.fullname,'services':services}
    auth_forms.vendor_notify_post_jobs(res)
    logger.info("mailsent")



@task(queue='high-priority')
def write_segments_to_db(validated_str_data, document_id): #validated_data

    '''
    To write segments from Json file(okapi) to segments database.
    '''

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
    '''
    This function is for pre-translation flow called in project creation
    '''
    from ai_workspace.models import Project,Task
    from ai_workspace_okapi.api_views import DocumentViewByTask
    from ai_workspace_okapi.serializers import DocumentSerializerV2
    pr = Project.objects.get(id=project_id)

    if pr.pre_translate == True:
        if task_id:
            tasks = Task.objects.filter(id=task_id)
        else:
            tasks = pr.get_mtpe_tasks

        [MTonlytaskCeleryStatus.objects.create(task_name = 'mt_only',task_id = i.id,status=1,celery_task_id=mt_only.request.id) for i in tasks]
        for i in tasks:
            document = DocumentViewByTask.create_document_for_task_if_not_exists(i)
            try:
                if document.get('msg') != None:pass
            except:pass

            tt = MTonlytaskCeleryStatus.objects.create(task_name = 'mt_only',task_id = i.id,status=2,celery_task_id=mt_only.request.id)

    logger.info('mt-only')


@task(queue='high-priority')
def write_doc_json_file(doc_data, task_id):
    '''
    writing doc_data from spring endpoint to json file for furthur processing
    '''
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
    '''
    This celery task is for processing long source text to speech by splitting and calling google t2s API
    '''
    from ai_workspace.api_views import text_to_speech_task,long_text_source_process
    obj = Task.objects.get(id=task_id)
    user = AiUser.objects.get(id=user_id)
    MTonlytaskCeleryStatus.objects.create(task_id = obj.id,status=1,celery_task_id=text_to_speech_long_celery.request.id,task_name = "text_to_speech_long_celery")
    tt = long_text_source_process(consumable_credits,user,file_path,obj,language,voice_gender,voice_name)
    logger.info("Text to speech called")




@task(queue='high-priority')
def google_long_text_file_process_cel(consumable_credits,document_user_id,file_path,task_id,target_language,voice_gender,voice_name):
    '''
    This celery task is for processing long text to speech by splitting and calling google t2s API
    '''
    from ai_workspace_okapi.api_views import long_text_process
    document_user = AiUser.objects.get(id = document_user_id)
    obj = Task.objects.get(id=task_id)
    MTonlytaskCeleryStatus.objects.create(task_id=obj.id,status=1,task_name='google_long_text_file_process_cel',celery_task_id=google_long_text_file_process_cel.request.id)
    tr = long_text_process(consumable_credits,document_user,file_path,obj,target_language,voice_gender,voice_name)
    logger.info("Text to speech document called")


@task(queue='high-priority')
def transcribe_long_file_cel(speech_file,source_code,filename,task_id,length,user_id,hertz):
    '''
    This celery task is for processing long speech file to text by calling google s2t API
    '''
    from ai_workspace.api_views import transcribe_long_file
    obj = Task.objects.get(id = task_id)
    user = AiUser.objects.get(id = user_id)
    MTonlytaskCeleryStatus.objects.create(task_id=obj.id,status=1,task_name='transcribe_long_file_cel',celery_task_id=transcribe_long_file_cel.request.id)
    transcribe_long_file(speech_file,source_code,filename,obj,length,user,hertz)
    logger.info("Transcribe called")

@task(queue='high-priority', max_retries=2, default_retry_delay=60)
def translate_file_task_cel(task_id):
    '''
    This celery task is for processing file as by calling 'Document translate API of google'
    and return the translated file
    '''
    from ai_workspace.api_views import translate_file_process
    MTonlytaskCeleryStatus.objects.create(task_id=task_id,status=1,task_name='translate_file_task_cel',celery_task_id=translate_file_task_cel.request.id)
    translate_file_process(task_id)
    logger.info('File Translate called')

@task(queue='high-priority')
def pre_translate_update(task_id):

    '''
    This celery task is called when pre-translate option is updated after project creation
    '''

    from ai_workspace.models import Task, TaskAssign
    from ai_workspace_okapi.models import Document,Segment,TranslationStatus,MT_RawTranslation,MtRawSplitSegment
    from ai_workspace.api_views import UpdateTaskCreditStatus
    from ai_workspace_okapi.api_views import MT_RawAndTM_View,get_tags
    from ai_workspace_okapi.models import MergeSegment,SplitSegment
    #from ai_workspace_okapi.api_views import DocumentViewByTask
    from itertools import chain

    task = Task.objects.get(id=task_id)
    MTonlytaskCeleryStatus.objects.create(task_id=task_id, task_name='pre_translate_update', status=1, celery_task_id=pre_translate_update.request.id)
    user = task.job.project.ai_user
    mt_engine = task.job.project.mt_engine_id
    task_mt_engine_id = TaskAssign.objects.filter(Q(task=task) & Q(step_id=1)).first().mt_engine.id
    # if task.document == None:
    #     document = DocumentViewByTask.create_document_for_task_if_not_exists(task)
    segments = task.document.segments_for_find_and_replace
    merge_segments = MergeSegment.objects.filter(text_unit__document=task.document)
    split_segments = SplitSegment.objects.filter(text_unit__document=task.document)

    final_segments = list(chain(segments, merge_segments, split_segments))

    update_list, update_list_for_merged,update_list_for_split = [],[],[]
    mt_segments, mt_split_segments = [],[]

    is_adaptive = task.job.project.isAdaptiveTranslation
    
    for seg in final_segments:

        if seg.target == '' or seg.target == None:
            initial_credit = user.credit_balance.get("total_left")
            consumable_credits = MT_RawAndTM_View.get_consumable_credits(task.document, seg.id, None)
            if initial_credit > consumable_credits:
                try:
                    if task.job.project.project_type_id == 8:
                        mt = get_translation(mt_engine, seg.source, task.document.source_language_code, task.document.target_language_code,\
                                             user_id=task.owner_pk,cc=consumable_credits,format_='html')
                    else:
                        # If it is normal translation
                        if not is_adaptive:
                            mt = get_translation(mt_engine, seg.source, task.document.source_language_code, task.document.target_language_code,\
                                                 user_id=task.owner_pk,cc=consumable_credits)
                        # If the translation is Adaptive
                        else:
                            mt_original = get_translation(mt_engine, seg.source, task.document.source_language_code, task.document.target_language_code,\
                                                 user_id=task.owner_pk,cc=consumable_credits)
                            mt = replace_with_gloss(seg.source, mt_original, task)
                    tags = get_tags(seg)
                    if tags:
                        seg.target = mt + tags
                        seg.temp_target = mt + tags
                    else:
                        seg.target = mt
                        seg.temp_target = mt
                    seg.status_id = TranslationStatus.objects.get(status_id=103).id
                    
                    if type(seg) is SplitSegment:
                        mt_split_segments.append(seg)
                    else:mt_segments.append(seg)
                except:
                    seg.target = ''
                    seg.temp_target = ''
                    seg.status_id=None
            else:
                MTonlytaskCeleryStatus.objects.create(task_id = task_id,task_name='pre_translate_update',status=1,celery_task_id=pre_translate_update.request.id,\
                                                      error_type="Insufficient Credits")
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
                mt_only = re.sub(r'<[^>]+>', "", i.target),
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
                mt_only= re.sub(r'<[^>]+>', "", i.target),
                split_segment_id= i.id,
            )
            for i in mt_split_segments
        ]
    MtRawSplitSegment.objects.bulk_create(instances_1, ignore_conflicts=True)
    logger.info("pre_translate_update")

########################### QA Related Tasks ###########################################
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

#########################################################################################

@task(queue='high-priority')
def project_analysis_property(project_id, retries=0, max_retries=3):
    '''
    This task is to execute project analysis property for the tasks
    '''
    logger.info("Executing high-priority task")
    from ai_workspace.api_views import ProjectAnalysisProperty
    from ai_workspace.models import Project
    proj = Project.objects.get(id=project_id)
    task = proj.get_tasks[0]
    try:
        obj = MTonlytaskCeleryStatus.objects.create(task_id=task.id, project_id=proj.id,status=1,task_name='project_analysis_property',celery_task_id=project_analysis_property.request.id)
        ProjectAnalysisProperty.get(project_id)
        logger.info("analysis property called")
    except Exception as e:
        logger.error(f'Error in task: {e}')
        retries += 1
        if retries > max_retries:
            logger.info("retries exceeded")
            raise MaxRetriesExceededError("Maximum retries reached.") from e
            

##################################### Tasks Related to ai_tm ##################################

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
        if tm_analysis:
            word_count = get_word_count(tm_analysis,proj,task)
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
            char_count = get_weighted_char_count(obj)
            if assigns.task_assign_info.account_raw_count == False:
                if assigns.status == 1:
                    assigns.task_assign_info.billable_word_count = word_count
                    assigns.task_assign_info.billable_char_count = char_count
                    assigns.task_assign_info.save()
                    po_modify_weigted_count([assigns.task_assign_info])
                    if assigns.task_assign_info.mtpe_count_unit_id != None:
                        if assigns.task_assign_info.mtpe_count_unit_id == 1:
                            if existing_wc != word_count:
                                notify_word_count(assigns,word_count,char_count)
                        else:
                            if existing_cc != char_count:
                                notify_word_count(assigns,word_count,char_count)
    logger.info('billable count updated')


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
                Receiver = AiUser.objects.get(id = receiver)
                receivers = []
                receivers =  Receiver.team.get_project_manager if (Receiver.team and Receiver.team.owner.is_agency) else []
                receivers.append(Receiver)
                Sender = AiUser.objects.get(id = sender)
                hired_editors = Sender.get_hired_editors if Sender.get_hired_editors else []
                for i in [*set(receivers)]:
                    if i in hired_editors or (i.team and i.team.owner) in hired_editors:
                        ws_forms.task_assign_detail_mail(i,assignment_id)
            else:
                assigns = task_assgn_objs[0].task_assign
                if assigns.task_assign_info.mtpe_count_unit_id != None:
                    if assigns.task_assign_info.mtpe_count_unit_id == 1:
                        if existing_wc != word_count:
                            notify_word_count(assigns,word_count,char_count)
                    else:
                        if existing_cc != char_count:
                            notify_word_count(assigns,word_count,char_count)
        except Exception as e:
            logger.error(f'Error in notify: {e}')
            pass
    logger.info('billable count updated and mail sent')

    if len(task_assign_obj_ls) != 0:
         po_modify_weigted_count(task_assign_obj_ls)


############################ For wordchoice ############################################

OPEN_AI_GPT_MODEL_REPLACE = settings.OPEN_AI_GPT_MODEL_REPLACE  

from ai_staff.models import InternalFlowPrompts
import openai

def gloss_prompt(gloss_list):
    prompt_list= []
    for count,term in enumerate(gloss_list):
        gloss_prompt_concat = "{}. {} (source: {}) → {}".format(count+1, term.sl_term.strip(), 
                                                                term.sl_term_translate.strip(),
                                                                term.tl_term.strip())
        if term.pos:
            pos_prompt = " and POS tag is {}".format(term.pos)
            gloss_prompt_concat = gloss_prompt_concat+pos_prompt
        prompt_list.append(gloss_prompt_concat)
    return "\n".join(prompt_list)

def tamil_gloss(gloss_list):
    prompt_list = []
    for term in gloss_list:
        prompt_list.append(term.sl_term.strip())
    return ",".join(prompt_list)

def tamil_correction(tar_seg,terms_trans_dict):
     
    messages=[{"role": "system", "content": """Your task is to modify a provided Tamil sentence based on specific guidelines. Here's the necessary information you'll need to execute the task:
    Please remember to focus on splitting the original word into its root and morphological parts. Once that is done, replace the original word in the sentence with the modified root of the original word while keeping the morphological structure intact.
    output:  provide only the modified sentence.
    do not generate anything else. no feedback or intermediate steps."""},
                {"role": "user", "content":tar_seg+"\n\n"+",".join(terms_trans_dict) }]
    print("messages",messages)
    completion = openai.ChatCompletion.create(model=OPEN_AI_GPT_MODEL_REPLACE,messages=messages)
    res = completion["choices"][0]["message"]["content"]
    return res

def tamil_morph_prompt(src_seg ,tar_seg, gloss_list,lang_code,src_lang,tar_lang):   # 
    from ai_openai.utils import gemini_model_generative 

    terms_trans_dict = {}

    gloss_list_sl_term = tamil_gloss(gloss_list)
    content = src_seg+"\n\n"+tar_seg+"\nword list: "+gloss_list_sl_term
    # if lang_code == 38: # for italian language
    #     content_prompt = """You're a highly skilled translator and linguist specializing in translations between the source and target languages. You have a knack for accurately mapping words between them while adhering strictly to grammatical forms, ensuring precision without any abbreviations or short forms.
    #                         Your task is to process the given source text along with its translation and a provided word list.
    #                         Here are the details you'll need to consider:
    #                         Source {} text: {}
    #                         {} translation: {}
    #                         Word list: {}
    #                         For each listed word, fetch the exact corresponding term from the translation, maintaining the same tense and form. If no matching terms are present, leave the response empty or "".
    #                         Output format: source word: target word (if present next term pair separate with a comma), otherwise, leave empty.don't give any acknowledgment give only the result.""".format(src_lang , src_seg ,tar_lang,tar_seg,gloss_list_sl_term)
    #     res = gemini_model_generative(content_prompt)
    #else:
    content_prompt = """i will provide you the source english text, its relative translation and word list
        fetch out the relative translated word from the translation for the english word in the list.
        output: generate the source english word and the fetched tamil word. do not generate feedback or anything else.
        output format: english word : tamil word in comma seperated
            """
    messages=[{"role": "system", "content":content_prompt },{"role": "user", "content":content }]
    
    completion = openai.ChatCompletion.create(model=OPEN_AI_GPT_MODEL_REPLACE,messages=messages)
    res = completion["choices"][0]["message"]["content"]
    for i in res.split(","):
        terms_trans = i.strip().split(":")
 
        if terms_trans[0].strip():
            sl_term = terms_trans[0].strip()
 
            term_instance = gloss_list.filter(sl_term=sl_term).last()
            if term_instance:
                terms_trans_dict[terms_trans[1].strip()] = term_instance.tl_term
    return terms_trans_dict


def replace_mt_with_gloss(src, raw_mt, gloss, source_language, target_language):
    from ai_staff.models import LanguageGrammarPrompt
    from ai_openai.utils import gemini_model_generative 
    from ai_staff.models import ExtraReplacePrompt
    tar_lang_id = [77] #38,
    src_lang = source_language.language
    tar_lang = target_language.language
    tar_lang_id_to_check = target_language.id
    internal_flow_instance = InternalFlowPrompts.objects.get(name='replace_mt_with_gloss')
    prompt_phrase = internal_flow_instance.prompt_phrase

    gloss_list = gloss_prompt(gloss)

    if tar_lang_id_to_check in tar_lang_id:
        gloss_list = tamil_morph_prompt(src,raw_mt,gloss,tar_lang_id_to_check,src_lang,tar_lang)

    replace_prompt = prompt_phrase.format(tar_lang, src_lang, src,  tar_lang, raw_mt,gloss_list, tar_lang)
    extra_prompt = ExtraReplacePrompt.objects.filter(internal_prompt=internal_flow_instance,language=target_language)

    if extra_prompt:
        replace_prompt = replace_prompt + extra_prompt.last().prompt
    
    completion = openai.ChatCompletion.create(model=OPEN_AI_GPT_MODEL_REPLACE,messages=[{"role": "user", 
                                                                                            "content": replace_prompt}])    
    res = completion["choices"][0]["message"]["content"]

    lang_gram_prompt = LanguageGrammarPrompt.objects.filter(language=target_language)

    if lang_gram_prompt:
        tamil_morph_result = ""
        lang_gram_prompt = lang_gram_prompt.last() ### only for tamil language
        if tar_lang_id_to_check  == 77: # tamil id 
            lang_code = source_language.locale_code
            tamil_morph_result = tamil_morph_prompt(src,raw_mt,gloss,lang_code,src_lang,tar_lang)
        res = gemini_model_generative(lang_gram_prompt.prompt.format(raw_mt,str(tamil_morph_result),res)) #src_lang,src,raw_mt ,gloss, 

        
        # Credit calculation

        # prompt_usage = completion['usage']
        # total_token = prompt_usage['total_tokens']
        # consumed_credits = get_consumable_credits_for_openai_text_generator(total_token)
        # debit_status, status_code = UpdateTaskCreditStatus.update_credits(user, consumed_credits)

    # except:
    #     logger.error("error in process ing adaptive prompt")
    #     res = raw_mt
    return res 



def replace_with_gloss(src, raw_mt, task):
    
    from ai_glex.models import GlossarySelected, Glossary
    from ai_workspace_okapi.api_views import check_source_words

    final_mt = raw_mt
    proj = task.job.project

    # if GlossarySelected.objects.filter(project=proj, glossary__project__project_type_id=10).exists():
    
    # Checking if a glossary is added from Assets or
    # or if a glossary is created on the fly

    if GlossarySelected.objects.filter(project=proj).exists() or \
        (Glossary.objects.filter(file_translate_glossary=proj).exists()):

        gloss, source_language, target_language = check_source_words(src, task)

        if gloss:
            final_mt = replace_mt_with_gloss(src, raw_mt, gloss, source_language, target_language)
    return final_mt
    

@task(queue='high-priority')
def adaptive_translate(task_id,segments):
    from ai_workspace_okapi.models import Segment, TranslationStatus
    from ai_workspace.models import Task
    from ai_workspace.api_views import UpdateTaskCreditStatus
    from ai_workspace_okapi.api_views import MT_RawAndTM_View
    track_seg = None
    try:
        task = Task.objects.get(id=task_id)
        user = task.job.project.ai_user
        MTonlytaskCeleryStatus.objects.create(task_id=task_id, task_name="adaptive_translate", status=1, celery_task_id=adaptive_translate.request.id)
        user = task.job.project.ai_user
        # Convert JSON data back to Segment objects
        segment_ids = [segment["id"] for segment in segments]
        print('segment_ids',segment_ids)
        final_segments = Segment.objects.filter(id__in=segment_ids)
        print("final_segments",final_segments[0].id,final_segments[len(final_segments)-1].id)
        track_seg = TrackSegmentsBatchStatus.objects.create(celery_task_id=adaptive_translate.request.id,document=task.document,
                                                        seg_start_id=final_segments[0].id,seg_end_id=final_segments[len(final_segments)-1].id,
                                                        project=task.proj_obj,status=BatchStatus.ONGOING)
        # Initialize translator
        translator = AdaptiveSegmentTranslator(
            task.document.source_language_code,
            task.document.target_language_code,
            settings.ANTHROPIC_API_KEY,
            settings.ANTHROPIC_MODEL_NAME,
            gloss_terms=None
        )
        
        # segments_to_process = []
        # consumable_credits = 0
        # for segment in final_segments:
        #     if not segment.target:
        #         segments_to_process.append({
        #             "segment_id": segment.id,
        #             "source": segment.source,
        #             "tagged_source": segment.tagged_source
        #         })
        #         consumable_credits += MT_RawAndTM_View.get_adaptive_consumable_credits(task.document, segment.id, None)
        # print('consumable_credits',consumable_credits)
        # # Translate segments in batch
        # translated_segments = translator.process_batch(segments_to_process)

        # segment_ids = [seg["segment_id"] for seg in translated_segments]
        # print('segment_ids',segment_ids)
        # segment_objs = Segment.objects.in_bulk(segment_ids)
        # print('segment_objs',len(segment_objs))
        

        # update_list = []
        # initial_credit = user.credit_balance.get("total_left")
        # if initial_credit > consumable_credits:
        
        #     for segment in translated_segments:
        #         print('final_translation',segment["final_translation"])
        #         segment_id = segment["segment_id"]
        #         final_text = segment["final_translation"]
        #         if segment_id in segment_objs:
        #             seg_obj = segment_objs[segment_id]
        #             if not seg_obj.target:
        #                 try:        
        #                     seg_obj.temp_target = final_text
        #                     seg_obj.target = final_text
        #                     seg_obj.status_id = TranslationStatus.objects.get(status_id=103).id
        #                     update_list.append(seg_obj)
        #                 except Exception as e:
        #                     logger.error(f"Error processing segment {seg_obj.id}: {e}")
        #                     seg_obj.target = ''
        #                     seg_obj.temp_target = ''
        #                     seg_obj.status_id = None
        #                     continue
                        
        #     # Bulk update all segments and debet credits
        #     Segment.objects.bulk_update(update_list, ["target","temp_target", "status_id"])
        #     UpdateTaskCreditStatus.update_credits(user, consumable_credits)
        #     # Update batch status
        #     track_seg.status = BatchStatus.COMPLETED
        #     track_seg.save()
        #     logger.info("Adaptive segment translation completed successfully.")
        
        #mock code 
        segments_to_process = []
        consumable_credits = 0
        for segment in final_segments:
            if not segment.target:
                segments_to_process.append({
                    "segment_id": segment.id,
                    "source": segment.source,
                    "tagged_source": segment.tagged_source
                })
                consumable_credits += MT_RawAndTM_View.get_adaptive_consumable_credits(task.document, segment.id, None)
        print('consumable_credits',consumable_credits)
        # Translate segments in batch
        # translated_segments = translator.process_batch(segments_to_process)

        segment_ids = [seg.id for seg in final_segments]
        print('segment_ids',segment_ids)
        segment_objs = Segment.objects.in_bulk(segment_ids)
        print('segment_objs',len(segment_objs))
        

        update_list = []
        initial_credit = user.credit_balance.get("total_left")
        if initial_credit > consumable_credits:
        
            for segment in final_segments:
                import time
                segment_id = segment.id
                # final_text = segment["final_translation"]
                if segment_id in segment_objs:
                    seg_obj = segment_objs[segment_id]
                    if not seg_obj.target:
                        try:        
                            time.sleep(3)
                            seg_obj.temp_target = "test"
                            seg_obj.target = "test"
                            seg_obj.status_id = TranslationStatus.objects.get(status_id=103).id
                            update_list.append(seg_obj)
                        except Exception as e:
                            logger.error(f"Error processing segment {seg_obj.id}: {e}")
                            seg_obj.target = ''
                            seg_obj.temp_target = ''
                            seg_obj.status_id = None
                            continue
                        
            # Bulk update all segments and debet credits
            Segment.objects.bulk_update(update_list, ["target","temp_target", "status_id"])
            # UpdateTaskCreditStatus.update_credits(user, consumable_credits)
            # Update batch status
            track_seg.status = BatchStatus.COMPLETED
            track_seg.save()
            logger.info("Adaptive segment translation completed successfully.")
            
        else:
            logger.info(f"Insufficient credits for segment {seg_obj.id}")
            MTonlytaskCeleryStatus.objects.create(
                task_id=task_id, task_name="adaptive_translate", status=1, 
                celery_task_id=adaptive_translate.request.id, error_type="Insufficient Credits"
            )
            logger.info("Insufficient credits")
            if track_seg:
                track_seg.delete()

    except Exception as e:
        logger.error(f"Batch task failed: {e}")
        if track_seg:
            track_seg.delete()


@task(queue='high-priority')
def mt_raw_update(task_id,segments):

    '''
    This task is mainly used for get_mt (mt-only download) for the source files.
    This is called for page-wise translation.
    '''

    from ai_workspace.models import Task, TaskAssign
    from ai_workspace_okapi.models import Document,Segment,TranslationStatus,MT_RawTranslation,MtRawSplitSegment
    from ai_workspace.api_views import UpdateTaskCreditStatus
    from ai_workspace_okapi.api_views import MT_RawAndTM_View,get_tags
    from ai_workspace_okapi.models import MergeSegment,SplitSegment
    from itertools import chain

    task = Task.objects.get(id=task_id)
    MTonlytaskCeleryStatus.objects.create(task_id=task_id, task_name='mt_raw_update', status=1,celery_task_id=mt_raw_update.request.id)
    user = task.job.project.ai_user
    mt_engine = task.job.project.mt_engine_id
    task_mt_engine_id = TaskAssign.objects.filter(Q(task=task) & Q(step_id=1)).first().mt_engine.id
    isAdaptiveTranslation = task.job.project.isAdaptiveTranslation
    if segments == None:
        segments = task.document.segments_for_find_and_replace
        merge_segments = MergeSegment.objects.filter(text_unit__document=task.document)
        split_segments = SplitSegment.objects.filter(text_unit__document=task.document)
        final_segments = list(chain(segments, merge_segments, split_segments))
    else:
        final_segments = segments

    update_list, update_list_for_merged, update_list_for_split = [],[],[]
    mt_segments, mt_split_segments = [],[]
    
    for seg in final_segments:###############Need to revise####################
        try:
            if (type(seg) is Segment):# or (type(seg) is MergeSegment):
                mt_raw = seg.seg_mt_raw
            elif (type(seg) is MergeSegment):
                mt_raw = seg.segments.first().seg_mt_raw
            else:
                if seg.mt_raw_split_segment.exists() == False:
                    mt_raw = None
                else:
                    mt_raw = seg.mt_raw_split_segment.first().mt_raw
        except:
            mt_raw = None
    
        if mt_raw == None:
            if seg.target == '' or seg.target == None:
                initial_credit = user.credit_balance.get("total_left")
                consumable_credits = MT_RawAndTM_View.get_consumable_credits(task.document, seg.id, None)
                if initial_credit > consumable_credits:
                    try:
                        
                        if isAdaptiveTranslation:
                            # Adapting glossary
                            raw_mt = get_translation(mt_engine, seg.source, task.document.source_language_code, task.document.target_language_code, \
                                                    user_id=task.owner_pk, cc=consumable_credits)
                            mt = replace_with_gloss(seg.source,raw_mt,task)
                        else:
                            # Without adapting glossary
                            mt = get_translation(mt_engine, seg.source, task.document.source_language_code, task.document.target_language_code,user_id=task.owner_pk,cc=consumable_credits)
                            raw_mt = mt

                        tags = get_tags(seg)

                        if tags:
                            seg.target = mt + tags
                            seg.temp_target = mt + tags
                        else:
                            seg.target = mt
                            seg.temp_target = mt
                        seg.status_id = TranslationStatus.objects.get(status_id=103).id
                        if type(seg) is SplitSegment:
                            mt_split_segments.append({'seg':seg,'mt':mt, "mt_only":raw_mt})
                        
                        # Previous else block    
                        # else:mt_segments.append({'seg':seg,'mt':mt})
                        else:mt_segments.append({'seg':seg,'mt':mt, "mt_only":raw_mt})
                    except:
                        seg.target = ''
                        seg.temp_target = ''
                        seg.status_id=None
                else:
                    MTonlytaskCeleryStatus.objects.create(task_id = task_id,task_name='mt_raw_update',status=1,celery_task_id=mt_raw_update.request.id,\
                                                          error_type="Insufficient Credits")
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
                    
                    if isAdaptiveTranslation:
                        # Adapting glossary
                        raw_mt = get_translation(mt_engine, seg.source, task.document.source_language_code, task.document.target_language_code, \
                                                user_id=task.owner_pk, cc=consumable_credits)
                        mt = replace_with_gloss(seg.source,raw_mt,task)
                    else:
                        # Without adapting glossary
                        mt = get_translation(mt_engine, seg.source, task.document.source_language_code, task.document.target_language_code,user_id=task.owner_pk,cc=consumable_credits)
                        raw_mt = mt

                    if type(seg) is SplitSegment:
                        mt_split_segments.append({'seg':seg,'mt':mt, "mt_only":raw_mt})
                    else:mt_segments.append({'seg':seg,'mt':mt, "mt_only":raw_mt})
                else:
                    logger.info("Insufficient credits")
                
    
    Segment.objects.bulk_update(update_list,['target','temp_target','status_id'])
    MergeSegment.objects.bulk_update(update_list_for_merged,['target','temp_target','status_id'])
    SplitSegment.objects.bulk_update(update_list_for_split,['target','temp_target','status_id'])
    
    instances = [
            MT_RawTranslation(
                mt_raw= re.sub(r'<[^>]+>', "", i['mt']),
                mt_only = re.sub(r'<[^>]+>', "", i['mt_only']),
                mt_engine_id = mt_engine,
                task_mt_engine_id = mt_engine,
                segment_id= i['seg'].id,
            )
            for i in mt_segments
        ]

    tt = MT_RawTranslation.objects.bulk_create(instances, ignore_conflicts=True)

    instances_1 = [
            MtRawSplitSegment(
                mt_raw= re.sub(r'<[^>]+>', "", i['mt']),
                mt_only = re.sub(r'<[^>]+>', "", i['mt_only']),
                split_segment_id= i['seg'].id,
            )
            for i in mt_split_segments
        ]
    tr = MtRawSplitSegment.objects.bulk_create(instances_1, ignore_conflicts=True)
   
    logger.info("mt_raw_update")


@task
def check_test():
    sleep(1000)



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

# @task(queue='high-priority')
# def update_words_from_template_task(file_ids):
    
#     for i in file_ids:
#         instance = glex_model.GlossaryFiles.objects.get(id=i)
#         glossary_obj = instance.project.glossary_project#glex_model.Glossary.objects.get(project_id = instance.project_id)
#         dataset = Dataset()
#         imported_data = dataset.load(instance.file.read(), format='xlsx')
#         if instance.source_only == False and instance.job.source_language != instance.job.target_language:
#             for data in imported_data:
#                 if data[2]:
#                     try:
#                         value = glex_model.TermsModel(
#                                 # data[0],          #Blank column
#                                 data[1],            #Autoincremented in the model
#                                 data[2].strip(),    #SL term column
#                                 data[3].strip() if data[3] else data[3],    #TL term column
#                                 data[4], data[5], data[6], data[7], data[8], data[9],
#                                 data[10], data[11], data[12], data[13], data[14], data[15]
#                         )
#                     except:
#                         value = glex_model.TermsModel(
#                                 # data[0],          #Blank column
#                                 data[1],            #Autoincremented in the model
#                                 data[2].strip(),    #SL term column
#                                 data[3].strip() if data[3] else data[3], )
#                     value.glossary_id = glossary_obj.id
#                     value.file_id = instance.id
#                     value.job_id = instance.job_id
#                     value.save()
#                     #print("ID----------->",value.id)
#         else:
#             for data in imported_data:
            
#                 if data[2]:
#                         value = glex_model.TermsModel(
#                                 # data[0],          #Blank column
#                                 data[1],            #Autoincremented in the model
#                                 data[2].strip()
#                                 )
#                 value.glossary_id = glossary_obj.id
#                 value.file_id = instance.id
#                 value.job_id = instance.job_id
#                 value.save()
#                 #print("ID----------->",value.id)
#         print("Terms Uploaded")


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
            "signup_age":abs(diff_month(user.date_joined,timezone.now())),
            "from_campaign":None if user.user_campaign.last()==None else user.user_campaign.last().campaign_name.campaign_name
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

        project_types = ",".join(rep.get_project_type(user))
        data.update({
            "project_types":project_types,
        })
        objs = AiUserDetails.objects.using("bi").filter(email=data["email"])
        if objs.count() != 0:
            objs.using("bi").update(**data)
        else:
            user_det = AiUserDetails(**data)
            user_det.save(using="bi")

        user_det = AiUserDetails.objects.using("bi").get(email=data["email"])
        lang_pairs = rep.get_language_pair_used(user)
        if len(lang_pairs) != 0:
            for lang in lang_pairs:
                data2['user_detail'] = user_det
                pairs = lang.split('->')
                data2['source_lang'] = pairs[0]
                if len(pairs)!=1:
                    data2['target_lang'] = pairs[1]
                user_lang = UsedLangPairs(**data2)
                user_lang.save(using="bi")


def proz_list_send_email(projectpost_id):
    from ai_marketplace.api_views import get_proz_lang_pair
    from rest_framework.response import Response
    '''
    This task is to notify proz users about available projectpost. In this we are calling proz-API
    by sending the custom message. Person from proz approves and forward it.(Is the flow)
    '''
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
        integration_api_url = os.getenv("PROZ_URL")+"freelancer-matches"
        response = requests.request("GET", integration_api_url, headers=headers, params=params)
        if response and response.get('success') == 1:
            uuids = []
            for vendor in response.get('data'):
                uuids.append(vendor.get('freelancer').get('uuid'))
        user = instance.customer
        message = 'Customer Posted project with this language pair. project_title '+instance.proj_name+ ' with biddeadline '+instance.bid_deadline.date().strftime('%d-%m-%Y')+ '. You can bid the project and win. Visit Ailaysa for more details.'
        subject = request.POST.get('subject', 'Message from Ailaysa Test' )
        headers = {'X-Proz-API-Key': os.getenv("PROZ-KEY"),}
        url = os.getenv("PROZ_URL")+"messages"
        payload = {'recipient_uuids': uuids,
                    'sender_email': user.email ,
                    'body': message,
                    'subject': subject,
                    'sender_name': user.fullname}
    return Response({'msg':'email sent'})


#### -------------------- Adaptive Translation ---------------------------- ####
@task(queue='high-priority')
def adaptive_segment_translation(segments_data, source_lang, target_lang, gloss_terms):
    # from ai_workspace_okapi.models import Segment

    # try:
    #     translator = AdaptiveSegmentTranslator(source_lang, target_lang, os.getenv('ANTHROPIC_API_KEY') ,os.getenv('ANTHROPIC_MODEL_NAME'), gloss_terms)
    #     translated_segments = translator.process_batch(segments_data) 

    #     for segment in translated_segments:
    #         segment_obj = Segment.objects.get(id=segment["segment_id"])
    #         segment_obj.temp_target = segment["final_translation"]
    #         segment_obj.save()

    #     # Update batch status
    #     batch_status = TrackSegmentsBatchStatus.objects.get(celery_task_id=adaptive_segment_translation.request.id)
    #     batch_status.status = BatchStatus.COMPLETED
    #     batch_status.save()

    #     logger.info("Adaptive segment translation was completed and saved to DB")

    #     # Mark overall task as completed if all batches are done
    #     task = Task.objects.get(document=batch_status.document)
    #     if not TrackSegmentsBatchStatus.objects.filter(document=batch_status.document).exclude(status=BatchStatus.COMPLETED).exists():
    #         task.adaptive_file_translate_status = AdaptiveFileTranslateStatus.COMPLETED
    #         task.save()
    #         logger.info("All batches completed. Task marked as COMPLETED")

    # except Exception as e:
    #     logger.error(f"Batch task failed: {e}")
    #     batch_status = TrackSegmentsBatchStatus.objects.filter(celery_task_id=adaptive_segment_translation.request.id).first()
    #     if batch_status:
    #         batch_status.status = BatchStatus.FAILED
    #         batch_status.save()
    if gloss_terms:
        print(gloss_terms, "Gloss terms")
        print(len(gloss_terms), "Length of gloss_terms")
    import time
    time.sleep(10)


@task(queue='high-priority')
def segment_batch_translation(segments_data, batch_size, min_threshold, source_lang, target_lang, task_id, project_id, total_segments):
    from ai_workspace_okapi.serializers import AdaptiveSegmentSerializer
    from ai_workspace_okapi.models import Segment

    task = Task.objects.get(id=task_id)
    project = Project.objects.get(id=project_id)
    start_idx = 0

    print("Total segment count : {}".format(total_segments))
    print("Total segment count : {}".format(len(segments_data)))

    get_terms_for_task = get_glossary_for_task(project, task)

    while start_idx < total_segments:
        end_idx = min(start_idx + batch_size, total_segments)

        if (total_segments - end_idx) <= min_threshold:
            end_idx = total_segments

        batch_segments_data = segments_data[start_idx:end_idx]

        translation_task = adaptive_segment_translation.apply_async(
            (batch_segments_data, source_lang, target_lang, get_terms_for_task),
            queue='high-priority'
        )

        seg_start_id = batch_segments_data[0]["segment_id"]
        seg_end_id = batch_segments_data[-1]["segment_id"]

        TrackSegmentsBatchStatus.objects.create(
            celery_task_id=translation_task.id,
            status=BatchStatus.ONGOING,
            document=task.document,
            seg_start_id=seg_start_id,  
            seg_end_id=seg_end_id,  
            project=project
        )
        print("Batch Created", start_idx, "to", end_idx)
        start_idx = end_idx


@task(queue='high-priority')
def create_doc_and_write_seg_to_db(task_id):
    from ai_workspace_okapi.api_views import DocumentViewByTask
    from ai_workspace_okapi.models import TextUnit, Segment
    from ai_workspace_okapi.serializers import AdaptiveSegmentSerializer

    try:
        task = Task.objects.get(id=task_id)
        project = task.job.project
        document = DocumentViewByTask.create_document_for_task_if_not_exists(task)
        task = Task.objects.select_related('job__source_language', 'job__target_language').get(id=task.id)
        source_lang = task.job.source_language.language
        target_lang = task.job.target_language.language
        segments = Segment.objects.filter(text_unit__document__id=document.id).order_by('id')
        serializer = AdaptiveSegmentSerializer(segments, many=True)
        total_segments = len(serializer.data)
        task.adaptive_file_translate_status = AdaptiveFileTranslateStatus.ONGOING
        task.save()
        segment_batch_translation.apply_async((serializer.data, 15, 7, source_lang, target_lang, task_id, project.id, total_segments,), queue='high-priority')

    except Exception as e:
        logger.error(f'Error in batch task: {e}')


def get_glossary_for_task(project, task):
    from ai_glex.api_views import job_lang_pair_check
    from ai_glex.models import GlossarySelected, TermsModel

    job_ins = Task.objects.get(id=task.id).job
    src_lang, tar_lan = job_ins.source_language, job_ins.target_language

    try:
        gloss_job_ins = [] 
        if getattr(project, 'individual_gloss_project', None):
            gloss_proj = project.individual_gloss_project.project
            gloss_job_list = gloss_proj.project_jobs_set.all()
            individual_result = job_lang_pair_check(gloss_job_list, src_lang.id, tar_lan.id)
            if individual_result:
                gloss_job_ins.append(individual_result)

        gloss_selected = GlossarySelected.objects.filter(project=project)
        gloss_projects = [gloss.glossary.project for gloss in gloss_selected] if gloss_selected else []
        
        if gloss_projects:
            multiple_results = []
            for gp in gloss_projects:
                is_pair = job_lang_pair_check(gp.project_jobs_set.all(), src_lang.id, tar_lan.id)
                if is_pair:
                    multiple_results.append(is_pair)
            gloss_job_ins.extend(multiple_results)

        if gloss_job_ins:
            latest_terms = (
                TermsModel.objects
                .filter(job__in=gloss_job_ins)
                .annotate(sl_term_lower=Lower('sl_term'))
                .order_by('sl_term_lower', '-modified_date')
                .distinct('sl_term_lower')
            )
            term_map = {term.sl_term.lower(): term.tl_term for term in latest_terms if term.tl_term}
            return term_map
        
        return None

    except Exception as e:
        logger.info(f'Error in getting glossary for task: {e}')