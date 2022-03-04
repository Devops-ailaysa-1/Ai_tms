from ai_glex import models as glex_model
from tablib import Dataset

def update_words_from_template(sender, instance, *args, **kwargs):
    glossary_obj = glex_model.Glossary.objects.get(project_id = instance.project_id)
    dataset = Dataset()
    imported_data = dataset.load(instance.file.read(), format='xlsx')
    for data in imported_data:
        value = glex_model.TermsModel(
                # data[0],          #Blank column
                data[1],            #Autoincremented in the model
                data[2].strip(),    #SL term column
                data[3].strip(),    #TL term column
                data[4], data[5], data[6], data[7], data[8], data[9],
                data[10], data[11], data[12], data[13], data[14], data[15]
        )
        value.glossary_id = glossary_obj.id
        value.file_id = instance.id
        value.job_id = instance.job_id
        value.save()
    print("Terms Uploaded")
