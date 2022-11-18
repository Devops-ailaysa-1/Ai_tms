from rest_framework.response import Response
from rest_framework.views import APIView
import re,json
from .models import TmxFileNew
from .serializers import TmxFileSerializer,UserDefinedRateSerializer
from ai_workspace.serializers import TaskSerializer
from ai_workspace.models import Project, File, Task
from ai_tm import match
from translate.storage.tmx import tmxfile
from collections import Counter
from rest_framework import viewsets,status
from rest_framework.decorators import api_view
from django.db.models import Q
from .models import WordCountGeneral,WordCountTmxDetail,UserDefinedRate


def get_json_file_path(task):
    source_file_path = TaskSerializer(task).data["source_file_path"]
    path_list = re.split("source/", source_file_path)
    return path_list[0] + "doc_json/" + path_list[1] + ".json"


TAG_RE = re.compile(r'<[^>]+>')

def remove_tags(text):
    return TAG_RE.sub('', text)


class UserDefinedRateView(viewsets.ViewSet):

    def list(self, request):
        #user = request.user
        user = request.user.team.owner if request.user.team else request.user
        rates = UserDefinedRate.objects.filter(user=user).last()
        serializer = UserDefinedRateSerializer(rates)
        return Response(serializer.data)

    def create(self, request):
        user = request.user.team.owner if request.user.team else request.user
        serializer = UserDefinedRateSerializer(data={**request.POST.dict(),"user":user.id})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, pk):
        user = request.user.team.owner if request.user.team else request.user
        queryset = UserDefinedRate.objects.get(Q(id=pk) & Q(user_id = user.id))
        serializer =UserDefinedRateSerializer(queryset,data={**request.POST.dict()},partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        user = request.user.team.owner if request.user.team else request.user
        obj = UserDefinedRate.objects.get(Q(id=pk) & Q(user_id = user.id))
        obj.delete()
        return Response(status=204)


class TmxUploadView(viewsets.ViewSet):

    def list(self, request):
        project_id = request.GET.get('project')
        if not project_id:
            return Response({'msg':'project_id required'},status=400)
        files = TmxFileNew.objects.filter(project_id=project_id).all()
        serializer = TmxFileSerializer(files, many=True)
        return Response(serializer.data)

    def create(self, request):

        data = {**request.POST.dict(), "tmx_file": request.FILES.getlist('tmx_file')}
        ser_data = TmxFileSerializer.prepare_data(data)
        serializer = TmxFileSerializer(data=ser_data,many=True)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
        return Response(serializer.data, status=201)

    def update(self, request, pk):
        tmx_file_ins = TmxFileNew.objects.get(id=pk)
        job_id = request.POST.get("job_id", None)
        serializer = TmxFileSerializer(tmx_file_ins, data={"job" : job_id}, partial=True)
        print("SER VALIDITY-->", serializer.is_valid())
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=200)
        return Response(serializer.errors)

    def delete(self, request, pk):
        instance = TmxFileNew.objects.get(id=pk)
        instance.delete()
        return Response(status=204)


# def check(uploaded_files,job):
#     for file in uploaded_files:
#         tree = ET.parse(file.tmx_file.path)
#         root=tree.getroot()
#         for j in root.iter('tu'):
#             for i in j.iter('tuv'):
#                 lang = i.get('{http://www.w3.org/XML/1998/namespace}lang')
#                 print(lang.split('-')[0])
#         break





def get_tm_analysis(doc_data,job):
        #doc_data = json.loads(doc_data)
        text_data = doc_data.get("text")
        sources = []
        sources_ = []
        tm_lists = []
        final = []
        files_list=[]
        sl = job.source_language_code
        tl = job.target_language_code

        for para in text_data.values():
            for segment in para:
                sources.append(segment["source"])
                sources_.append(segment["source"].strip())
        #print("Source--------------->",sources)
        c = Counter(sources_)
        files = TmxFileNew.objects.filter(job_id=job.id).all()
        #files = check(uploaded_files,job)
        print("Files---------->",files)
        if files:
            files_list = [i.id for i in files]
            for file in files:
                with open(file.tmx_file.path, 'rb') as fin:
                    tm_file = tmxfile(fin, sl, tl)

                for node in tm_file.unit_iter():
                    tm_lists.append(remove_tags(node.source))
            #print("Tm_Lists--------->",tm_lists)
            unrepeated = [i for n, i in enumerate(sources) if i not in sources[:n]]
            for i,j in enumerate(unrepeated):
                repeat = c[j]-1 if c[j]>1 else 0
                tt = match.extractOne(j,tm_lists,match_type='levenshtein')
                final.append({'sent':j,'ratio':tt[1],'index':i,'word_count':len(j.split()),'repeat':repeat})
            #print("Final------------->",final)
            return final,files_list
        else:
            return None,files_list

def get_word_count(tm_analysis,project,task,raw_total):
    tm_100,tm_95_99,tm_85_94,tm_75_84,tm_50_74,tm_101,tm_102,new,repetition =0,0,0,0,0,0,0,0,0
    for i,j in enumerate(tm_analysis):
        if i>0:
            previous = tm_analysis[i-1]
            pre_ratio = previous.get('ratio')*100
        else:pre_ratio = None
        if i<len(tm_analysis)-1:
            next_ = tm_analysis[i+1]
            next_ratio = next_.get('ratio')*100
        else:next_ratio = None
        ratio_ = round(j.get('ratio')*100)
        if ratio_ == 100:
            if ratio_ == pre_ratio and ratio_ == next_ratio:
                tm_102+=j.get('word_count')
            elif ratio_ == pre_ratio  or ratio_ == next_ratio:########need to check incontext logic
                tm_101+=j.get('word_count')
            else:
                tm_100+=j.get('word_count')
        elif 95 <= ratio_ <= 99:
            tm_95_99 += j.get('word_count')
        elif 85 <= ratio_ <= 94:
            tm_85_94 += j.get('word_count')
        elif 75 <= ratio_ <= 84:
            tm_75_84 += j.get('word_count')
        elif 74 <= ratio_ <= 50:
            tm_50_74 += j.get('word_count')
        else:
            new+=j.get('word_count')
        if j.get('repeat'):
            repetition+=j.get('word_count')*j.get('repeat')
    print("95-99------>",tm_95_99)
    print("100--------->",tm_100,tm_101,tm_102)
    wc = WordCountGeneral.objects.filter(Q(project_id=project.id) & Q(tasks_id=task.id)).last()
    if wc:
        obj = WordCountGeneral.objects.filter(Q(project_id=project.id) & Q(tasks_id=task.id))
        obj.update(tm_100 = tm_100,tm_95_99 = tm_95_99,tm_85_94 = tm_85_94,tm_75_84 = tm_75_84,\
        tm_50_74 = tm_50_74,tm_101 = tm_101,tm_102 = tm_102,new_words = new,\
        repetition=repetition,raw_total=raw_total)
    else:
        wc = WordCountGeneral.objects.create(project_id=project.id,tasks_id=task.id,\
            tm_100 = tm_100,tm_95_99 = tm_95_99,tm_85_94 = tm_85_94,tm_75_84 = tm_75_84,\
            tm_50_74 = tm_50_74,tm_101 = tm_101,tm_102 = tm_102,new_words = new,\
            repetition=repetition,raw_total=raw_total)
    return wc



# class ProjectAnalysis(APIView):
#
#     def get(self, request, project_id):
@api_view(['GET',])
def get_project_analysis(request,project_id):

        tasks= []

        proj_wwc = 0

        proj_raw_total,proj_tm_100,proj_tm_95_99,proj_tm_85_94,proj_tm_75_84,proj_tm_50_74,proj_tm_101,proj_tm_102,proj_new,proj_repetition = 0,0,0,0,0,0,0,0,0,0

        proj = Project.objects.filter(id=project_id).first()

        user = proj.ai_user

        rates = UserDefinedRate.objects.filter(user = user).last()
        if not rates:
            rates = UserDefinedRate.objects.filter(is_default = True).first()

        for _task in proj.get_mtpe_tasks:
            if _task.task_wc_general.last() == None:
                tasks.append(_task)
            else:
                temp1 = [i.id for i in _task.job.tmx_file_job.all()]
                temp2 = [i.tmx_file_obj_id for i in _task.task_wc_general.last().wc_general.all()]
                temp3 = set(temp1) ^ set(temp2)
                if temp3:
                    tasks.append(_task)
                    _task.task_wc_general.last().wc_general.all().delete()

        if tasks:

            for task in tasks:

                file_path = get_json_file_path(task)

                doc_data = json.load(open(file_path))

                print("DocData------->",doc_data)
                doc_data = json.loads(doc_data)

                raw_total = doc_data.get('total_word_count')

                tm_analysis,files_list = get_tm_analysis(doc_data,task.job)

                print("Tm-------------->",tm_analysis)

                if tm_analysis:
                    word_count = get_word_count(tm_analysis,proj,task,raw_total)
                else:
                    word_count = WordCountGeneral.objects.create(project_id =project_id,tasks_id=task.id,\
                                new_words=doc_data.get('total_word_count'),raw_total=raw_total)
                [WordCountTmxDetail.objects.create(word_count=word_count,tmx_file_id=i,tmx_file_obj_id=i) for i in files_list]

        res=[]
        for task in  proj.get_mtpe_tasks:
            word_count = task.task_wc_general.last()

            WWC = (word_count.new_words * 100 + word_count.tm_100 * rates.tm_100_percentage + \
                  word_count.tm_95_99 * rates.tm_95_99_percentage + word_count.tm_85_94 * rates.tm_85_94_percentage +\
                  word_count.tm_75_84 * rates.tm_75_84_percentage + word_count.tm_50_74 * rates.tm_50_74_percentage +\
                  word_count.tm_101 * rates.tm_101_percentage + word_count.tm_102 * rates.tm_102_percentage)/100

            proj_wwc += WWC
            proj_tm_100 += word_count.tm_100
            proj_tm_101 += word_count.tm_101
            proj_tm_102 += word_count.tm_102
            proj_tm_95_99 += word_count.tm_95_99
            proj_tm_85_94 += word_count.tm_85_94
            proj_tm_75_84 += word_count.tm_75_84
            proj_tm_50_74 += word_count.tm_50_74
            proj_new += word_count.new_words
            proj_repetition += word_count.repetition
            proj_raw_total += word_count.raw_total

            res.append({'task_id':task.id,'task_file':task.file.filename,'task_lang_pair':task.job.source_target_pair_names,'weighted':round(WWC),'new':word_count.new_words,'repetition':word_count.repetition,\
            'tm_50_74':word_count.tm_50_74,'tm_75_84':word_count.tm_75_84,'tm_85_94':word_count.tm_85_94,'tm_95_99':word_count.tm_95_99,\
            'tm_101':word_count.tm_101,'tm_102':word_count.tm_102,'raw_total':word_count.raw_total})

        proj_detail =[{'project_id':proj.id,'project_name':proj.project_name,'weighted':round(proj_wwc),'new':proj_new,'repetition':proj_repetition,\
                    'tm_50_74':proj_tm_50_74,'tm_75_84':proj_tm_75_84,'tm_85_94':proj_tm_85_94,'tm_95_99':proj_tm_95_99,\
                    'tm_101':proj_tm_101,'tm_102':proj_tm_102,'raw_total':proj_raw_total}]
        ser = UserDefinedRateSerializer(rates)
        return Response({'payable_rate':ser.data,'project_wwc':proj_detail,'task_wwc':res})
