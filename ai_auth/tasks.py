from django.core.mail import send_mail
import smtplib
from celery.utils.log import get_task_logger
import celery,re,pickle, copy
import djstripe
logger = get_task_logger(__name__)
from celery.decorators import task
from datetime import date
from django.utils import timezone
from .models import AiUser,UserAttribute,HiredEditors,ExistingVendorOnboardingCheck
import datetime,os,json, collections
from djstripe.models import Subscription,Invoice
from ai_auth.Aiwebhooks import renew_user_credits_yearly
from notifications.models import Notification
from ai_auth import forms as auth_forms
from ai_marketplace.models import ProjectboardDetails
import requests
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
@task
def sync_invoices_and_charges(days):
    queryset = Invoice.objects.annotate(
            diff=ExpressionWrapper(timezone.now() - F('djstripe_updated'), output_field=DurationField())
            ).filter(diff__gt=timedelta(days))
    resync_instances(queryset)

@task
def renewal_list():
    cycle_date = timezone.now()
    subs =Subscription.objects.filter(billing_cycle_anchor__year=cycle_date.year,
                        billing_cycle_anchor__month=cycle_date.month,billing_cycle_anchor__day=cycle_date.day,status='active').filter(~Q(billing_cycle_anchor__year=F('current_period_start__year'),
                        billing_cycle_anchor__month=F('current_period_start__month'),billing_cycle_anchor__day=F('current_period_start__day')))
    print(subs)
    for sub in subs:
        renew_user_credits.apply_async((sub.djstripe_id,),eta=sub.billing_cycle_anchor)

@task
def renew_user_credits(sub_id):
    sub =Subscription.objects.get(djstripe_id=sub_id)
    renew_user_credits_yearly(subscription=sub)

@task
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

# @task
# def find_renewals():
@task
def delete_hired_editors():
    HiredEditors.objects.filter(Q(status = 1)&Q(date_of_expiry__lte = timezone.now())).delete()
    print("deleted")
    logger.info("Delete Hired Editor")


@task
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



@task
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



@task
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




@task
def shortlisted_vendor_list_send_email_new(projectpost_id):
    from ai_vendor.models import VendorLanguagePair
    from ai_auth import forms as auth_forms
    instance = ProjectboardDetails.objects.get(id=projectpost_id)
    lang_pair = VendorLanguagePair.objects.none()
    jobs = instance.get_postedjobs
    for obj in jobs:
        if obj.src_lang_id == obj.tar_lang_id:
            query = VendorLanguagePair.objects.filter(Q(source_lang_id=obj.src_lang_id) | Q(target_lang_id=obj.tar_lang_id) & Q(deleted_at=None)).distinct('user')
        else:
            query = VendorLanguagePair.objects.filter(Q(source_lang_id=obj.src_lang_id) & Q(target_lang_id=obj.tar_lang_id) & Q(deleted_at=None)).distinct('user')
        lang_pair = lang_pair.union(query)
    res={}
    for object in lang_pair:
        tt = object.source_lang.language if object.source_lang_id == object.target_lang_id else object.target_lang.language
        print(object.user.fullname)
        if object.user_id in res:
            res[object.user_id].get('lang').append({'source':object.source_lang.language,'target':tt})
        else:
            res[object.user_id]={'name':object.user.fullname,'user_email':object.user.email,'lang':[{'source':object.source_lang.language,'target':tt}],'project_deadline':instance.proj_deadline,'bid_deadline':instance.bid_deadline}
    auth_forms.vendor_notify_post_jobs(res)
    print("mailsent")


@task
def check_dict(dict):
    print("dct------->",dict)
    dict1 = json.loads(dict)
    logger.info("RRRR",dict)

@task
def write_segments_to_db(validated_str_data, document_id): #validated_data

    decoder = json.JSONDecoder(object_pairs_hook=collections.OrderedDict)
    validated_data = decoder.decode(validated_str_data)


    text_unit_ser_data = validated_data.pop("text_unit_ser", [])
    text_unit_ser_data2 = copy.deepcopy(text_unit_ser_data)

    from ai_workspace_okapi.models import Document
    from ai_workspace.api_views import UpdateTaskCreditStatus
    from ai_workspace_okapi.api_views import MT_RawAndTM_View
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
                target = ""
                seg['temp_target'] = ""
                status_id = None
            else:
                initial_credit = user.credit_balance.get("total_left")
                consumable_credits = MT_RawAndTM_View.get_consumable_credits(document,None,seg['source'])
                if initial_credit > consumable_credits:
                    mt = get_translation(mt_engine,str(seg["source"]),document.source_language_code,document.target_language_code)
                    seg['temp_target'] = mt
                    seg['target'] = mt
                    status_id = TranslationStatus.objects.get(status_id=104).id
                    debit_status, status_code = UpdateTaskCreditStatus.update_credits(user, consumable_credits)
                else:
                    target=""
                    seg['temp_target']=""
                    status_id=None
            seg_params.extend([str(seg["source"]), target, seg['temp_target'], str(seg["coded_source"]), str(tagged_source), \
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
        segments = Segment.objects.filter(text_unit__document=document)
        for i in segments:
            if i.target != "":
                count += 1
                mt_params.extend([i.target,mt_engine,None,"ai_workspace_okapi.segment",i.id])
        print("MT-------------->",mt_params)
        mt_raw_sql = "INSERT INTO ai_workspace_okapi_mt_rawtranslation (mt_raw, mt_engine_id, task_mt_engine_id, reverse_string_for_segment,segment_id)\
        VALUES {}".format(','.join(['(%s, %s, %s, %s, %s)'] * count))
        if mt_params:
            with closing(connection.cursor()) as cursor:
                cursor.execute(mt_raw_sql, mt_params)
    logger.info("mt_raw wrriting completed")


@task
def mt_only(project_id,token):
    from ai_workspace.models import Project,Task
    from ai_workspace_okapi.api_views import DocumentViewByTask
    from ai_workspace_okapi.serializers import DocumentSerializerV2
    pr = Project.objects.get(id=project_id)
    print("celerytask-------->",mt_only.request.id)
    print("PRE TRANSLATE-------------->",pr.pre_translate)
    if pr.pre_translate == True:
        tasks = pr.get_mtpe_tasks
        print("TASKS Inside CELERY----->",tasks)
        [MTonlytaskCeleryStatus.objects.create(task_id = i.id,status=1,celery_task_id=mt_only.request.id) for i in pr.get_mtpe_tasks]
        for i in pr.get_mtpe_tasks:
            document = DocumentViewByTask.create_document_for_task_if_not_exists(i)
            doc = DocumentSerializerV2(document).data
            print(doc)
            MTonlytaskCeleryStatus.objects.create(task_id = i.id,status=2,celery_task_id=mt_only.request.id)

@task
def write_doc_json_file(doc_data, task_id):

    from ai_workspace.serializers import TaskSerializer
    task = Task.objects.get(id=task_id)
    data = TaskSerializer(task).data
    from ai_workspace_okapi.api_views import DocumentViewByTask
    DocumentViewByTask.correct_fields(data)
    params_data = {**data, "output_type": None}

    source_file_path = params_data["source_file_path"]
    path_list = re.split("source/", source_file_path)
    os.mkdir(os.path.join(path_list[0], "doc_json"))
    doc_json_path = path_list[0] + "doc_json/" + path_list[1] + ".json"

    with open(doc_json_path, "w") as outfile:
        json.dump(doc_data, outfile)
    logger.info("Document json data written as a file")


@task
def text_to_speech_long_celery(consumable_credits,user_id,file_path,task_id,language,voice_gender,voice_name):
    from ai_workspace.api_views import text_to_speech_task,long_text_source_process
    obj = Task.objects.get(id=task_id)
    user = AiUser.objects.get(id=user_id)
    MTonlytaskCeleryStatus.objects.create(task_id = obj.id,status=1,celery_task_id=text_to_speech_long_celery.request.id,task_name = "text_to_speech_long_celery")
    #tt = text_to_speech_task(obj,language,gender,user,voice_name)
    tt = long_text_source_process(consumable_credits,user,file_path,obj,language,voice_gender,voice_name)
    #MTonlytaskCeleryStatus.objects.create(task_id = obj.id,status=2,celery_task_id=text_to_speech_celery.request.id,task_name = "text_to_speech_celery")
    print("TT-------------------->",tt)
    logger.info("Text to speech called")
    # if tt.status_code == 400:
    #     return tt.status_code



@task
def google_long_text_file_process_cel(consumable_credits,document_user_id,file_path,task_id,target_language,voice_gender,voice_name):
    from ai_workspace_okapi.api_views import long_text_process
    document_user = AiUser.objects.get(id = document_user_id)
    obj = Task.objects.get(id=task_id)
    MTonlytaskCeleryStatus.objects.create(task_id=obj.id,status=1,task_name='google_long_text_file_process_cel',celery_task_id=google_long_text_file_process_cel.request.id)
    tr = long_text_process(consumable_credits,document_user,file_path,obj,target_language,voice_gender,voice_name)
    #MTonlytaskCeleryStatus.objects.create(task_id=task.id,status=2,task_name='google_long_text_file_process_cel',celery_task_id=google_long_text_file_process_cel.request.id)
    logger.info("Text to speech document called")



    # host = os.environ.get("HOST")
    # #Base_Url = "http://127.0.0.1:8089/"
    # #DocumentViewByTask.as_view()(self.request)

        # headers = {'Authorization':'Bearer '+token}
        # print(headers)
#task = DocumentViewByTask.get_object(task_id=i)
            # print("Begin-------------->",i.id)
            # url = f"http://localhost:8089/workspace_okapi/document/{i.id}"
            # res = requests.request("GET", url, headers=headers)
            # print("doc--->",res.text)
@task
def transcribe_long_file_cel(speech_file,source_code,filename,task_id,length,user_id,hertz):
    from ai_workspace.api_views import transcribe_long_file
    obj = Task.objects.get(id = task_id)
    user = AiUser.objects.get(id = user_id)
    MTonlytaskCeleryStatus.objects.create(task_id=obj.id,status=1,task_name='transcribe_long_file_cel',celery_task_id=transcribe_long_file_cel.request.id)
    transcribe_long_file(speech_file,source_code,filename,obj,length,user,hertz)
    logger.info("Transcribe called")




@task
def pre_translate_update(task_id):
    from ai_workspace.models import Task, TaskAssign
    from ai_workspace_okapi.models import Document,Segment,TranslationStatus,MT_RawTranslation
    from ai_workspace.api_views import UpdateTaskCreditStatus
    from ai_workspace_okapi.api_views import MT_RawAndTM_View

    task = Task.objects.get(id=task_id)
    MTonlytaskCeleryStatus.objects.create(task_id = task_id,status=1,celery_task_id=pre_translate_update.request.id)
    user = task.job.project.ai_user
    mt_engine = task.job.project.mt_engine_id
    task_mt_engine_id = TaskAssign.objects.get(Q(task=task) & Q(step_id=1)).mt_engine.id
    segments = Segment.objects.filter(text_unit__document=task.document)
    update_list = []
    mt_segments = []

    for seg in segments:###############Need to revise####################
        i = seg.get_active_object()
        if i.target == '':
            initial_credit = user.credit_balance.get("total_left")
            consumable_credits = MT_RawAndTM_View.get_consumable_credits(task.document, i.id, i)
            if initial_credit > consumable_credits:
                i.target = get_translation(mt_engine, i.source, task.document.source_language_code, task.document.target_language_code)
                i.temp_target = i.target
                i.status_id = TranslationStatus.objects.get(status_id=104).id
                debit_status, status_code = UpdateTaskCreditStatus.update_credits(user, consumable_credits)
                mt_segments.append(i)
            else:
                MTonlytaskCeleryStatus.objects.create(task_id = task_id,status=1,celery_task_id=pre_translate_update.request.id,error_type="Insufficient Credits")
                break
    #             i.target= ""
    #             i.temp_target = ''
    #             i.status_id = None
            update_list.append(i)
    #
    Segment.objects.bulk_update(update_list,['target','temp_target','status_id'])


    instances = [
            MT_RawTranslation(
                mt_raw= i.target,
                mt_engine_id = mt_engine,
                task_mt_engine_id = task_mt_engine_id,
                segment_id= i.id,
            )
            for i in mt_segments
        ]

    MT_RawTranslation.objects.bulk_create(instances)
    #MTonlytaskCeleryStatus.objects.create(task_id = task_id,status=2,celery_task_id=pre_translate_update.request.id)
    logger.info("pre_translate_update")
