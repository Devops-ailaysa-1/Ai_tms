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
    LLM_ERROR = "LLM_ERROR", "LLM_ERROR"
    OTHER = "OTHER", "OTHER"

class PibTranslateStatusChoices(models.TextChoices):
    yet_to_start = "YET_TO_START", "yet_to_start"
    in_progress = "In_Progress", "in_progress"
    completed = "COMPLETED", "completed"
    failed = "FAILED", "failed"

class PibStoryCreationType(models.TextChoices):
    TEXT_INPUT = "text_input", "Text Input"
    FILE_UPLOAD = "file_upload", "File Upload"
