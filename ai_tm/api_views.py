from rest_framework.response import Response
from rest_framework.views import APIView
import re
from .models import TmxFileNew
from .serializers import TmxFileSerializer
from ai_workspace.serializers import TaskSerializer
from ai_workspace.models import Project, File, Task
from ai_tm import match
from translate.storage.tmx import tmxfile
from collections import Counter

def get_json_file_path(task):
    source_file_path = TaskSerializer(task).data["source_file_path"]
    path_list = re.split("source/", source_file_path)
    return path_list[0] + "doc_json/" + path_list[1] + ".json"


TAG_RE = re.compile(r'<[^>]+>')

def remove_tags(text):
    return TAG_RE.sub('', text)


class TmxUploadView(APIView):

    def get(self, request, project_id):
        files = TmxFileNew.objects.filter(project_id=project_id).all()
        serializer = TmxFileSerializer(files, many=True)
        return Response(serializer.data)

    def post(self, request, project_id):
        data = {**request.POST.dict(), "tmx_file": request.FILES.get('tmx_file')}
        data.update({'project_id': project_id})
        ser_data = TmxFileSerializer.prepare_data(data)
        serializer = TmxFileSerializer(data=ser_data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
        return Response(serializer.data, status=201)


def get_tm_analysis(doc_data,job):
        text_data = doc_data.get("text")
        sources = []
        tm_lists = []
        final = []
        files_list=[]
        sl = job.source_language_code
        tl = job.target_language_code

        for para in text_data.values():
            for segment in para:
                sources.append(segment["source"].strip())
        #c = Counter(sources)
        files = TmxFileNew.objects.filter(job_id=job.id).all()
        print("Files---------->",files)
        if files:
            files_list = [i.id for i in files]
            for file in files:
                with open(file.tmx_file.path, 'rb') as fin:
                    tm_file = tmxfile(fin, sl, tl)

                for node in tm_file.unit_iter():
                    tm_lists.append(remove_tags(node.source))
            print("Tm_Lists--------->",tm_lists)
            for i,j in enumerate(sources):
                #repeat = True if c[j]>1 else False
                tt = match.extractOne(j,tm_lists)
                final.append({'sent':j,'ratio':tt[1],'index':i,'word_count':len(j.split())})#,'repeat':repeat})
            print(final)
            return final,files_list
        else:
            return None,files_list

def get_word_count(tm_analysis):
    tm_100,tm_95_99,tm_85_94,tm_75_84,tm_50_74,tm_101,tm_102,new,repeatation =0,0,0,0,0,0,0,0,0
    for i,j in enumerate(tm_analysis):
        if i>0:
            previous = tm_analysis[i-1]
        if i<len(tm_analysis)-1:
            next_ = tm_analysis[i+1]
        ratio_ = j.get('ratio')*100
        if ratio_ == 100:
            if ratio_ == previous.get('ratio') or ratio_ == next_.get('ratio'):
                tm_101+=j.get('word_count')
            elif ratio_ == previous.get('ratio') and ratio_ == next_.get('ratio'):
                tm_102+=j.get('word_count')
            else:
                tm_100+=j.get('word_count')
        elif ratio_<=95 and ratio_>=99:
            tm_95_99+=j.get('word_count')
        elif ratio_<=85 and ratio_>=94:
            tm_85_94+=j.get('word_count')
        elif ratio_<=75 and ratio_>=84:
            tm_75_84+=j.get('word_count')
        elif ratio_<=74 and ratio_>=50:
            tm_50_74+=j.get('word_count')
        else:
            new+=j.get('word_count')
    wc = WordCountGeneral.objects.create(project=project,tasks=task,\
        tm_100 = tm_100,tm_95_99 = tm_95_99,tm_85_94 = tm_85_94,tm_75_84 = tm_75_84,\
        tm_50_74 = tm_50_74,tm_101 = tm_101,tm_102 = tm_102,new_words = new)
    return wc
    # return {'tm_100':tm_100,'tm_95_99':tm_95_99,'tm_85_94':tm_85_94,\
    #         'tm_75_84':tm_75_84,'tm_50_74':tm_50_74,'tm_101':tm_101,\
    #         'tm_102':tm_102,'new':new}


# class ProjectAnalysis(APIView):
#
#     def get(self, request, project_id):

def get_project_analysis(project_id):

        proj = Project.objects.filter(id=project_id).first()

        user = proj.ai_user

        proj_tasks = proj.get_tasks

        for task in proj_tasks:

            file_path = get_json_file_path(task)

            doc_data = json.load(open(file_path))

            tm_analysis,files_list = get_tm_analysis(doc_data,task.job)

            print("Tm-------------->",tm_analysis)

            if tm_analysis:
                word_count = get_word_count(tm_analysis,project,task)
            else:
                word_count = WordCountGeneral.objects.create(project=project,tasks=task,new_words=doc_data.get('total_word_count'))
            [WordCountTmxDetail.objects.create(word_count=word_count,tmx_file=i) for i in files_list]

            rates = UserDefinedRate.objects.filter(user = user).first()
            if not rates:
                rates = UserDefinedRate.objects.filter(is_default = True).first()
            

            #     for i,j in enumerate(tm_analysis):
            #         if i>0:
            #             previous = tm_analysis[i-1]
            #         if i<len(tm_analysis)-1:
            #             next_ = tm_analysis[i+1]
            #         ratio_ = i.get('ratio')
            #         if ratio_ == 1:
            #             if ratio_ == previous.get('ratio') or ratio_ == next.get('ratio'):
            #                 tm_101+=j.get('word_count')
            #             elif ratio == previous.get('ratio') and ratio_ == next.get('ratio'):
            #                 tm_102+=j.get('word_count')
            #             else:
            #                 tm_100+=j.get('word_count')
            #         elif ratio
            #
            #
            #         # range = DefinedRange.objects.filter(temp=temp).filter(Q(start__lte=ratio_ ,end__gt=ratio_)).first()
            #         # WordCount.objects.create(project=proj,task=task,range=range,words=i.get('word_count'))
            # else:
            #     WordCountGeneral.objects.create(project=proj,task=task,new_words=doc_data.get('total_word_count'))

        #tm_jobs = TmxFile.objects.filter(project_id=project_id)

        #proj_jobs = Job.objects.filter(project=project_id)

        # for tm_job in tm_jobs:
