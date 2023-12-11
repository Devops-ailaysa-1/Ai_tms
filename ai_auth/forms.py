from os import path

from allauth.account.forms import (
    EmailAwarePasswordResetTokenGenerator,
    ResetPasswordForm,
)
from allauth.account.utils import user_pk_to_url_str
from django.conf import settings
#from django.contrib.auth import forms as admin_forms
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _
# from .tasks import email_send_task
from django.contrib.sites.shortcuts import get_current_site
from datetime import date

from ai_auth import models as auth_models
from django.core.mail import EmailMessage
from django.utils.translation import ugettext_lazy as _
import logging
logger = logging.getLogger('django')
import os


class SendInviteForm(ResetPasswordForm):
    """
    used to send an invitation to onboard the platform and reset the password
    """

    default_token_generator = EmailAwarePasswordResetTokenGenerator()

    def send_email_invite(self, email, uri, uid, token,current_site,user):
        context = {
            "uri": uri,
            "uid": uid,
            "token": token,
            "user":user,
            "current_site": current_site,
        }
        msg_plain = render_to_string("account/email/password_reset_email.txt", context)
        msg_html = render_to_string("account/email/password_reset_email.html", context)
        send_mail(
            "Password Reset",
            msg_plain,
           settings.DEFAULT_FROM_EMAIL,
            [email],
            html_message=msg_html,
        )


    def save(self, request, **kwargs):
        email = self.cleaned_data["email"]
        token_generator = kwargs.get("token_generator", self.default_token_generator)
        for user in self.users:
            temp_key = token_generator.make_token(user)
            uri = path.join(settings.CLIENT_BASE_URL, settings.PASSWORD_RESET_URL)
            current_site = get_current_site(request)
            self.send_email_invite(email, uri, user_pk_to_url_str(user), temp_key,current_site,user)

        return self.cleaned_data["email"]



# class AiPasswordResetForm(ResetPasswordForm):
#     def clean_email(self):
#         """
#         Invalid email should not raise error, as this would leak users
#         for unit test: test_password_reset_with_invalid_email
#         """
#         email = self.cleaned_data["email"]
#         email = get_adapter().clean_email(email)
#         self.users = filter_users_by_email(email, is_active=True)
#         return self.cleaned_data["email"]

#     def save(self, request, **kwargs):
#         if 'allauth' not in settings.INSTALLED_APPS:
#             return super().save(request, **kwargs)
#         # for allauth
#         current_site = get_current_site(request)
#         email = self.cleaned_data['email']
#         token_generator = kwargs.get('token_generator', default_token_generator)

#         for user in self.users:

#             temp_key = token_generator.make_token(user)

#             # save it to the password reset model
#             # password_reset = PasswordReset(user=user, temp_key=temp_key)
#             # password_reset.save()

#             # send the password reset email
#             path = reverse(
#                 'password_reset_confirm',
#                 args=[user_pk_to_url_str(user), temp_key],
#             )
#             url = build_absolute_uri(request, path)

#             context = {
#                 'current_site': current_site,
#                 'user': user,
#                 'password_reset_url': url,
#                 'request': request,
#             }
#             if app_settings.AUTHENTICATION_METHOD != app_settings.AuthenticationMethod.EMAIL:
#                 context['username'] = user_username(user)
#             get_adapter(request).send_mail(
#                 'account/email/password_reset_key', email, context
#             )
#         return self.cleaned_data['email']


def send_welcome_mail(current_site,user):
    context = {
        "user":user,
        "current_site": current_site,
    }
    email =user.email
    msg_plain = render_to_string("account/email/welcome.txt", context)#ai_staff/templates/account
    msg_html = render_to_string("account/email/welcome.html", context)
    sent=send_mail(
        "Welcome to Ailaysa!",
        msg_plain,
        settings.CEO_EMAIL,
        [email],
        html_message=msg_html,
    )
    if sent ==1:
        send_admin_new_user_notify(user)
    else:
        logger.error(f"welcome mail sending failed for {email}")

def send_admin_new_user_notify(user):
    if os.environ.get("ENV_NAME") != 'Production':
        return False
    context = {
    "user":user
    }
    email =user.email
    msg_html = render_to_string("new_user_notify.html", context)
    sent=send_mail(
        "New User Added",
        None,
       settings.DEFAULT_FROM_EMAIL,
        ["admin@ailaysa.com"],
        html_message=msg_html,
    )

    return True


def send_password_change_mail(current_site,user):
    today = date.today()
    d1 = today.strftime("%d/%m/%Y")
    context = {
        "user":user,
        "current_site": current_site,
        "date" : d1,
    }
    email =user.email
    msg_plain = render_to_string("account/email/password_change.txt", context)
    msg_html = render_to_string("account/email/password_change.html", context)
    send_mail(
        "Password change",
        msg_plain,
        settings.DEFAULT_FROM_EMAIL,
        [email],
        html_message=msg_html,
    )


def user_trial_end(user,sub):
    date1 = sub.trial_start.strftime("%B %d, %Y")
    date2 = sub.trial_end.strftime("%B %d, %Y")
    time1= sub.trial_start.strftime("%I:%M:%S %p")
    time2= sub.trial_end.strftime("%I:%M:%S %p")
    context = {
        "user":user,
        "start_date" : date1,
        "start_time": time1,
        "end_date" : date2,
        "end_time":time2
        }
    print("inside trial form")
    email =user.email
   # msg_plain = render_to_string("account/email/password_change.txt", context)
    msg_html = render_to_string("account/email/trial_ending.html", context)
    try:
        from .block_list import ven_blocklist
        block_list=ven_blocklist
    except Exception as e:
        block_list=[]
    if user.email not in block_list:
        ms =send_mail(
            " Your Trial Ends Soon",None,
            settings.DEFAULT_FROM_EMAIL,
            [email],
            html_message=msg_html,
        )
        print("mailsent>>",ms)
    else:
        print("user in block list")



def vendor_status_mail(email,status):
    context = {
        "user":email,
        "status": status,
    }
    if status == "Accepted":
        msg_html = render_to_string("account/email/vendor_status.html", context)
    else:
        msg_html = render_to_string("account/email/vendor_status_fail.html", context)
    send_mail(
        "Ailaysa Vendor profile application status",None,
        # msg_plain,
        settings.DEFAULT_FROM_EMAIL,
        [email],
        html_message=msg_html,
    )
    print("mailsent>>")


def vendor_request_admin_mail(instance):
    today = date.today()
    context = {'email': instance.email,'name':instance.name,'date':today,'message':instance.message}
    msg_html = render_to_string("vendor_onboarding_email.html", context)
    send_mail(
        "Regarding Vendor Onboarding",None,
        settings.DEFAULT_FROM_EMAIL,
        ['support@ailaysa.com'],
        html_message=msg_html,
    )
    print("mailsent>>")

def vendor_accepted_freelancer_mail(user):
    # print("User----<>",user)
    today = date.today()
    context = {'email': user.email,'name':user.fullname,'date':today}
    msg_html = render_to_string("vendor_accepted_freelancer_mail.html", context)
    send_mail(
        "Regarding Vendor Joining Freelancers Marketplace",None,
        settings.DEFAULT_FROM_EMAIL,
        ['support@ailaysa.com'],
        html_message=msg_html,
    )
    print("mailsent>>")

def vendor_renewal_mail(link,email):
    context = {'link':link}
    msg_html = render_to_string("vendor_renewal.html",context)
    send_mail(
        "Ailaysa has become a translators marketplace. Please update your account",None,
        settings.DEFAULT_FROM_EMAIL,
        [email],
        html_message=msg_html,
    )
    print("mailsent>>")


def internal_user_credential_mail(context):
    context = context
    email = context.get('email')
    team = context.get('team')
    msg_html = render_to_string("Internal_member_credential_email.html",context)
    send_mail(
        f"You have been added to {team}'s team in Ailaysa",None,
        settings.DEFAULT_FROM_EMAIL,
        [email],
        html_message=msg_html,
    )
    print("mailsent>>")

def vendor_notify_post_jobs(detail):
    #pass
    for i in detail:
        context = detail.get(i)
        email = context.get('user_email')
        msg_html = render_to_string("job_alert_email.html",context)
        tt = send_mail(
            'You have got a job opportunity with Ailaysa Marketplace!',None,
            settings.DEFAULT_FROM_EMAIL,
            #['thenmozhivijay20@gmail.com'],
            [email],
            html_message=msg_html,
        )
        print("available job alert mail sent>>")


# def vendor_notify_post_jobs(detail):
#     #pass
#     for i in detail:
#         context = detail.get(i)
#         email = context.get('user_email')
#         msg_html = render_to_string("job_alert_email.html",context)
#         send_mail(
#             'Available jobs alert from ailaysa',None,
#             settings.DEFAULT_FROM_EMAIL,
#             [email],
#             html_message=msg_html,
#         )
#         print("available job alert mail sent>>")



def external_member_invite_mail(context,email):
    context = context
    msg_html = render_to_string("External_member_invite_email.html",context)
    send_mail(
        'Ailaysa MarketPlace Invite',None,
        settings.DEFAULT_FROM_EMAIL,
        [email],
        html_message=msg_html,
    )
    print("mailsent>>")


def unread_notification_mail(email_list):
    for i in email_list:
        context = {'data':i.get('details')}
        email = i.get('email')
        msg_html = render_to_string("notification_email.html",context)
        send_mail(
            'Notification from Ailaysa',None,
            settings.DEFAULT_FROM_EMAIL,
            [email],
            html_message=msg_html,
        )
    print("notification mailsent>>")



def user_trial_extend_mail(user):
    context = {'user':user.fullname}
    email = user.email
    msg_html = render_to_string("user_trial_extend.html",context)
    send_mail(
        'Trial-Extension',None,
        settings.DEFAULT_FROM_EMAIL,
        [email],
        html_message=msg_html,
    )
    print("trial_exten_mail_sent-->>>")



def existing_vendor_onboarding_mail(user,gen_password):
    context = {'user':user.fullname,'email':user.email,'gen_password':gen_password}
    email = user.email
    msg_html = render_to_string("existing_vendor_onboarding.html",context)
    # sent =send_mail(
    #     'Become a member of Ailaysa freelancer marketplace',None,
    #     'Ailaysa Vendor Manager <vendormanager@ailaysa.com>',
    #     [email],
    #     html_message=msg_html,
    # )

    msg = EmailMessage(
        'Become a member of Ailaysa freelancer marketplace',
         msg_html,
        'Ailaysa Vendor Manager <vendormanager@ailaysa.com>',
        [email],
        bcc=['vendormanager@ailaysa.com'],
        reply_to=['vendormanager@ailaysa.com'],
    )

    msg.content_subtype = "html"

    sent=msg.send()
    print("existing_vendor_onboarding_mail-->>>")
    if sent==0:
        return False
    else:
        return True

def send_campaign_welcome_mail(user):
    context = {'user':user,}
    email = user.email
    msg_html = render_to_string("account/email/welcome_campaign.html", context)
    # sent =send_mail(
    #     'Become a member of Ailaysa freelancer marketplace',None,
    #     'Ailaysa Vendor Manager <vendormanager@ailaysa.com>',
    #     [email],
    #     html_message=msg_html,
    # )

    msg = EmailMessage(
        "Translate your book free",
         msg_html,
        settings.DEFAULT_FROM_EMAIL,
        [email]
    )
    file = open('mediafiles/email/Translate your book free.pdf', 'rb')
    msg.attach('Translate your book free.pdf',file.read(),'application/pdf')
    msg.content_subtype = "html"
    sent=msg.send()
    file.close()
    if sent ==1:
        logger.info(f"Campaign welcome mail sent for {user.uid}")
    else:
        logger.error(f"Campaign welocome mail sending failed for {user.uid}")

def campaign_user_invite_email(user,gen_password):
    context = {'user':user.fullname,'email':user.email,'gen_password':gen_password}
    email = user.email
    msg_html = render_to_string("campaign_user_registration.html",context)
    # sent =send_mail(
    #     'Become a member of Ailaysa freelancer marketplace',None,
    #     'Ailaysa Vendor Manager <vendormanager@ailaysa.com>',
    #     [email],
    #     html_message=msg_html,
    # )

    msg = EmailMessage(
        'Welcome to Ailaysa!',
         msg_html,
        'Ailaysa <noreply@ailaysa.com>',
        [email],
        bcc=['support@ailaysa.com'],
        reply_to=['support@ailaysa.com'],
    )

    msg.content_subtype = "html"

    sent=msg.send()
    print("campaign_user_onboarding_mail-->>>")
    if sent==0:
        return False
    else:
        return True
    
# BOOTCAMP_MARKETING_DEFAULT_MAIL=os.getenv("BOOTCAMP_MARKETING_DEFAULT_MAIL")
def bootcamp_marketing_ack_mail(user_name,user_email,file_path):
    plain_msg = "Name: "+user_name+" Email: "+user_email
    Subject = "New Registration for Free BootCamp Marketing"

    file_ext = {"doc":"application/msword",
                "docx":"application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "pdf":"application/pdf"}
    email =  os.getenv("BOOTCAMP_MARKETING_DEFAULT_MAIL")
    # print("email",email)
    # email = "hemanthmurugan21@gmail.com"

    email_message = EmailMessage(Subject, plain_msg, settings.DEFAULT_FROM_EMAIL, [email])
    
    if file_path:
        file_name = file_path.split("/")[-1]
        file = open(file_path,'rb')
        email_message.attach(file_name,file.read(),file_ext[file_name.split(".")[-1]])

    sent = email_message.send()
    if sent:
        return True
    else:
        return False



def bootcamp_marketing_response_mail(user_name,user_email):
    Subject = "Ailaysa Pre-job bootcamp - Thank you for registering"
    Body = """Dear {},\n\n
Thank you registering for the one week pre-job bootcamp for
"AI Jobs in Sales and Digital Marketing" with Ailaysa.
We will let you know about further updates soon.\n

    Regards,
    Team Ailaysa""".format(user_name)
    
    sent = send_mail(Subject, Body, settings.DEFAULT_FROM_EMAIL, [user_email])
    if sent:
        return True
    else:
        return False