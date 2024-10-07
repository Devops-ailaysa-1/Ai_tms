from ai_qa import models as qa_model
from tablib import Dataset
import logging
logger = logging.getLogger("django")
def update_words_from_forbidden_file(sender, instance, created, *args, **kwargs):
    if created:
        s = open(instance.forbidden_file.path)
        text = s.readlines()
        for i in text:
            qa_model.ForbiddenWords.objects.create(words=i.strip(),job=instance.job,project=instance.project,file=instance)
        logging.info("ForbiddenWords Added")


def delete_words_from_ForbiddenWords(sender, instance, *args, **kwargs):
    try:
        forbidden_words = qa_model.ForbiddenWords.objects.filter(file_id = instance.id)
        forbidden_words.delete()
    except:
        pass
    logging.info("ForbiddenWords Deleted")

def update_words_from_untranslatable_file(sender, instance, created,*args, **kwargs):
    if created:
        s = open(instance.untranslatable_file.path)
        text = s.readlines()
        for i in text:
            qa_model.UntranslatableWords.objects.create(words=i.strip(),job=instance.job,project=instance.project,file=instance)
        logging.info("Untranslatables added")

def delete_words_from_Untranslatable(sender, instance, *args, **kwargs):
    try:
        untranslatable_words = qa_model.UntranslatableWords.objects.filter(file_id = instance.id)
        untranslatable_words.delete()
    except:
        pass
    logging.info("UntranslatableWords Deleted")
