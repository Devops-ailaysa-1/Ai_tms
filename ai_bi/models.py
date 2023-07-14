from django.db import models

# Create your models here.
from ai_auth.models import AiUser

class BiUser(models.Model):
    TECHNICAL=1
    FINANCE=2
    ADMIN=3
    ROLE_CHOICES = (
        (TECHNICAL, 'technical'),
        (FINANCE, 'finance'),
        (ADMIN,"admin"),
    )
    bi_user=models.OneToOneField(AiUser,related_name="bi_user", on_delete=models.CASCADE)
    bi_role = models.IntegerField( choices=ROLE_CHOICES)