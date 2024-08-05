from ai_glex import models as glex_model
from tablib import Dataset
import pandas as pd
from celery.decorators import task
#from ai_auth.tasks import update_words_from_template_task


def count_entries(file_path):
    df = pd.read_excel(file_path) 
    num_entries = len(df) 
    return num_entries



@task(queue='high-priority')
def update_words_from_template(instance_id): #update_words_from_template(sender, instance, *args, **kwargs)
    from ai_glex.models import GlossaryFiles
    instance = GlossaryFiles.objects.get(id=instance_id)
    glossary_obj = instance.project.glossary_project
    dataset = Dataset()
    imported_data = dataset.load(instance.file.read(), format='xlsx')
    if instance.source_only == False and instance.job.source_language != instance.job.target_language:
        

        for data in imported_data:
            if data[2]:
                try:
                    print("glossary---> advance file")
                    value = glex_model.TermsModel(
                            # data[0],          #Blank column
                            data[1],            #Autoincremented in the model
                            data[2].strip(),    #SL term column
                            data[3].strip() if data[3] else data[3],    #TL term column
                            data[4], data[5], data[6], data[7], data[8], data[9],
                            data[10], data[11], data[12], data[13], data[14], data[15]
                    )
                except:
                    print("glossary---> bulk create file")
                    value = glex_model.TermsModel(
                                data[1] if len(data) > 1 else None,  # Autoincremented in the model
                                data[2].strip() if len(data) > 2 and data[2] else None,  # SL term column
                                data[3].strip() if len(data) > 3 and data[3] else None,
                                data[4].strip() if len(data) > 4 and data[4] else None)  # For word choice
                                               
                value.glossary_id = glossary_obj.id
                value.file_id = instance.id
                value.job_id = instance.job_id
                value.save()
                instance.status  = "PENDING"
                instance.save()
        instance.status = "FINISHED"
        instance.is_extract = True
        instance.done_extraction = True
        instance.save()
    else:
        for data in imported_data:
            if data[2]:
                    instance.status  = "PENDING"
                    instance.save()
                    value = glex_model.TermsModel(
                            # data[0],          #Blank column
                            data[1],            #Autoincremented in the model
                            data[2].strip())
            value.glossary_id = glossary_obj.id
            value.file_id = instance.id
            value.job_id = instance.job_id
            value.save()
        instance.status  = "FINISHED"
        instance.save()
        

def delete_words_from_term_model(sender, instance, *args, **kwargs):
    try:
        terms =glex_model.Terms.objects.filter(file_id=instance.id)
        terms.delete()
    except:
        pass


def update_proj_settings(sender, instance, *args, **kwargs):
    if instance.glossary.project.project_type_id == 10 and instance.project.get_mt_by_page == True:
        instance.project.get_mt_by_page = False
        instance.project.save()
    else: 
        print("Nothing to change on  update_proj_settings function")