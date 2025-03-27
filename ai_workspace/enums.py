from django.db import models

class AdaptiveFileTranslateStatus(models.TextChoices):
    NOT_INITIATED = "NOT_INITIATED", "Translate Not Initiated"
    ONGOING = "ONGOING", "Translation Ongoing"
    COMPLETED = "COMPLETED", "Translation Completed"
    FAILED = "FAILED", "Translation Failed"

    