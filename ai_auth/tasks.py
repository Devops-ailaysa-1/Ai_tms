from django.core.mail import send_mail
import smtplib
from celery.utils.log import get_task_logger
import celery
import djstripe
logger = get_task_logger(__name__)
from celery.decorators import task
from datetime import date
from django.utils import timezone
from django.db.models import Q
from .models import AiUser,UserAttribute,HiredEditors
import datetime
from djstripe.models import Subscription
from ai_auth.Aiwebhooks import renew_user_credits_yearly
from notifications.models import Notification
from ai_auth import forms as auth_forms
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

from datetime import datetime, timedelta
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
def renewal_list():
    cycle_date = timezone.now()
    subs =Subscription.objects.filter(billing_cycle_anchor__year=cycle_date.year,
                        billing_cycle_anchor__month=cycle_date.month,billing_cycle_anchor__day=cycle_date.day,status='active')
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
               recent_message = j.description
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
