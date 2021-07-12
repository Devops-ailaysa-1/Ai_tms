from django.core.mail.backends.smtp import EmailBackend
from .tasks import send_dj_core_emails
from django.core.mail.message import sanitize_address
from django.conf import settings

class AiEmailBackend(EmailBackend):
    def _send(self, email_message):
        """A helper method that does the actual sending."""
        if not email_message.recipients():
            return False
        encoding = email_message.encoding or settings.DEFAULT_CHARSET
        from_email = sanitize_address(email_message.from_email, encoding)
        recipients = [sanitize_address(addr, encoding) for addr in email_message.recipients()]
        message = email_message.message()
        return send_dj_core_emails.delay(self.connection, from_email, recipients, message,self.fail_silently)

