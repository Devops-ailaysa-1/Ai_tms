from ai_glex import models as glex_model
from tablib import Dataset
import pandas as pd

def duplicate_check(instance):
    term=['Source language term','Target language term']
    term_inst=list(glex_model.TermsModel.objects.filter(job__id=instance.job_id).values('sl_term','tl_term'))
    df1=pd.DataFrame(term_inst)
    with open(instance.file.path,'rb') as fp:
        df2=pd.read_excel(fp.read())[term]
        
    if not df1.empty:
        df1.rename(columns={'sl_term':term[0],'tl_term':term[1]},inplace=True)
        df_all=df2.merge(df1, on=term,how='left',indicator=True)
        df_look_up=df_all[df_all['_merge']=='left_only'][term]
        # df_look_up.insert(0, 'sno', range(1, len(df_look_up) + 1))
        return df_look_up
    else:
        # df2.insert(0, 'sno', range(1, len(df2) + 1))
        return df2


def update_words_from_template(sender, instance, *args, **kwargs):
    print("Ins--->",instance)
    glossary_obj = instance.project.glossary_project#glex_model.Glossary.objects.get(project_id = instance.project_id)
    uncommon_data_term=duplicate_check(instance)
    if not uncommon_data_term.empty:
        imported_data=Dataset()
        imported_data.headers=uncommon_data_term.columns.tolist()
        for row in uncommon_data_term.itertuples(index=False):
            imported_data.append(row)
        # instance.source_only = True
    else:
        dataset=Dataset()
        imported_data=dataset.load(instance.file.read(), format='xlsx')
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
                            data[3].strip() if data[3] else data[3], )
                value.glossary_id = glossary_obj.id
                value.file_id = instance.id
                value.job_id = instance.job_id
                value.save()
                #print("ID----------->",value.id)
    else:
        for data in imported_data:
            print("Data in else------->",data)
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
            #print("ID----------->",value.id)
    
    print("Terms Uploaded")

def delete_words_from_term_model(sender, instance, *args, **kwargs):
    try:
        terms =glex_model.Terms.objects.filter(file_id=instance.id)
        terms.delete()
    except:
        pass
    print("Terms Deleted")
