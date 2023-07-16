from django.db import models

# Create your models here.
from ai_auth.models import AiUser

class BiUser(models.Model):
    # TECHNICAL=1
    # FINANCE=2
    # ADMIN=3
    ROLE_CHOICES = (
        ("TECHNICAL", 'TECHNICAL'),
        ("FINANCE", 'FINANCE'),
        ("ADMIN","ADMIN"),
    )
    bi_user=models.OneToOneField(AiUser,related_name="bi_user", on_delete=models.CASCADE)
    bi_role = models.CharField(max_length=250, choices=ROLE_CHOICES)