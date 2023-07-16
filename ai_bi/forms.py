
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from datetime import date

def bi_user_invite_mail(email, user,password):
    today = date.today()
    context = {'email': email,'name':user.fullname,'date':today,'password':password}
    msg_html = render_to_string("Bi_user_cred_email.html", context)
    send_mail(
        "Regarding BI Credential",None,
        settings.DEFAULT_FROM_EMAIL,
        [email],
        html_message=msg_html,
    )
    print("mailsent>>")