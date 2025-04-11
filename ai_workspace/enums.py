from django.db import models

class AdaptiveFileTranslateStatus(models.TextChoices):
    NOT_INITIATED = "NOT_INITIATED", "Translate Not Initiated"
    ONGOING = "ONGOING", "Translation Ongoing"
    COMPLETED = "COMPLETED", "Translation Completed"
    FAILED = "FAILED", "Translation Failed"


class BatchStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"  
    ONGOING = "ONGOING", "Ongoing"
    COMPLETED = "COMPLETED", "Completed"
    FAILED = "FAILED", "Failed"

class ErrorStatus(models.TextChoices):
    INSUFFICIENT_CREDIT = "INSUFFICIENT_CREDIT", "INSUFFICIENT_CREDIT"
    OTHER = "OTHER", "OTHER"