from django.db import models

class DownloadBase(models.Model):
    class Meta:
        abstract = True

    def download(self):
        raise NotImplementedError("You should derive "
            "the function in child class")






