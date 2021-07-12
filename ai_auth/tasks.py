from celery import shared_task
from django.core.mail import send_mail
import smtplib

@shared_task
def test_task():
    print("this is task")

@shared_task
def email_send_task(sub, msg, from_email, to_mails_list):
    send_mail(
        sub, msg, from_email, to_mails_list
        # html_message=msg_html,
    )
    return True
    
@shared_task
def send_dj_core_emails(conn, from_email, recipients, message, fail_silently=True):  
    try:
        conn.sendmail(from_email, recipients, message.as_bytes(linesep='\r\n'))
    except smtplib.SMTPException:
        if not fail_silently:
            raise
        return False
    return True