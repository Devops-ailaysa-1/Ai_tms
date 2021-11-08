from django.core.mail import send_mail
import smtplib
from celery.utils.log import get_task_logger
import celery
logger = get_task_logger(__name__)
from celery.decorators import task
from datetime import date
from .models import AiUser,UserAttribute
import datetime
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




@task
def delete_inactive_user_account():
    # AiUser.objects.filter(deactivation_date__date = date.today()).delete()
    users_list = AiUser.objects.filter(deactivation_date__date = date.today())
    for i in users_list:
        i.is_active=False
        i.save()
        # dir = UserAttribute.objects.get(user_id=i.id).allocated_dir
        # os.system("rm -r " +dir)
        # i.delete()
    logger.info("Delete Inactive User")
