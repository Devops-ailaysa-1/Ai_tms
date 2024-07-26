from ai_glex import models as glex_model
from tablib import Dataset
import pandas as pd
from ai_auth.tasks import update_words_from_template_task


def count_entries(file_path):
    df = pd.read_excel(file_path) 
    num_entries = len(df) 
    return num_entries


def update_words_from_template(sender, instance, *args, **kwargs):
    #glossary_obj = instance.project.glossary_project#glex_model.Glossary.objects.get(project_id = instance.project_id)
    #print("File--------->",instance.file)
    # entries = count_entries(instance.file)
    # print("Entries------------>",entries)
    # if entries > 50000:
    #     update_words_from_template_task.apply_async(([instance.id],))
    #     print("Celery Called")
    # else:
    glossary_obj = instance.project.glossary_project
    dataset = Dataset()
    imported_data = dataset.load(instance.file.read(), format='xlsx')
    if instance.source_only == False and instance.job.source_language != instance.job.target_language:
        for data in imported_data:
            if data[2]:
                try:
                    value = glex_model.TermsModel(
                            # data[0],          #Blank column
                            data[1],            #Autoincremented in the model
                            data[2].strip(),    #SL term column
                            data[3].strip() if data[3] else data[3],    #TL term column
                            data[4], data[5], data[6], data[7], data[8], data[9],
                            data[10], data[11], data[12], data[13], data[14], data[15]
                    )
                except:
                    value = glex_model.TermsModel(
                            # data[0],          #Blank column
                            data[1],            #Autoincremented in the model
                            data[2].strip(),    #SL term column
                            data[3].strip() if data[3] else data[3],
                            data[4].strip() if data[4] else data[4] ) #for word choice 
                value.glossary_id = glossary_obj.id
                value.file_id = instance.id
                value.job_id = instance.job_id
                value.save()
    else:
        for data in imported_data:
            if data[2]:
                    value = glex_model.TermsModel(
                            # data[0],          #Blank column
                            data[1],            #Autoincremented in the model
                            data[2].strip()
                            )
            value.glossary_id = glossary_obj.id
            value.file_id = instance.id
            value.job_id = instance.job_id
            value.save()

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
        print("Nothing to change")