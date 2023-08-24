from rest_framework.response import Response
from rest_framework.views import APIView
import re,json, xlsxwriter, os,requests
from .models import TmxFileNew, WordCountGeneral, CharCountGeneral
from .serializers import TmxFileSerializer,UserDefinedRateSerializer,CharCountGeneralSerializer, WordCountGeneralSerializer
from ai_workspace.serializers import TaskSerializer
from ai_workspace.models import Project, File, Task,Job
from ai_tm import match
#from translate.storage.tmx import tmxfile
from collections import Counter
from rest_framework import viewsets,status
from rest_framework.decorators import api_view
from django.db.models import Q
from django_celery_results.models import TaskResult
from .models import WordCountGeneral,WordCountTmxDetail,UserDefinedRate
from ai_workspace_okapi.utils import download_file
from ai_tm.utils import write_project_header, write_commons, write_data, tmx_read
from ai_workspace.serializers import TaskSerializer
from ai_workspace.api_views import ProjectAnalysisProperty
from django.conf import settings
from ai_auth.tasks import analysis,count_update
from ai_workspace.models import MTonlytaskCeleryStatus
import rapidfuzz
from rapidfuzz import process
import xml.etree.ElementTree as ET
from notifications.signals import notify
from django_oso.auth import authorize
from django.shortcuts import get_object_or_404
spring_host = os.environ.get("SPRING_HOST")

def get_json_file_path(task):
    source_file_path = TaskSerializer(task).data.get("source_file_path")
    path_list = re.split("source/", source_file_path)
    path = path_list[0] + "doc_json/" + path_list[1] + ".json"
    print("Exists")
    if not os.path.exists(path):
        print("Not Exists")
        write_json_data(task)
    return path


def write_json_data(task):
    ser = TaskSerializer(task)
    data = ser.data
    ProjectAnalysisProperty.correct_fields(data)
    # DocumentViewByTask.correct_fields(data)
    params_data = {**data, "output_type": None}
    res_paths = {"srx_file_path":"okapi_resources/okapi_default_icu4j.srx",
             "fprm_file_path": None,
             "use_spaces" : settings.USE_SPACES
             }
    doc = requests.post(url=f"http://{spring_host}:8080/getDocument/", data={
        "doc_req_params":json.dumps(params_data),
        "doc_req_res_params": json.dumps(res_paths)
    })

    if doc.status_code == 200 :
        doc_data = doc.json()
        task_write_data = json.dumps(doc_data, default=str)
        from ai_workspace_okapi.api_views import DocumentViewByTask
        DocumentViewByTask.correct_fields(data)
        params_data = {**data, "output_type": None}

        source_file_path = params_data["source_file_path"]
        path_list = re.split("source/", source_file_path)
        if not os.path.exists(os.path.join(path_list[0], "doc_json")):
            os.mkdir(os.path.join(path_list[0], "doc_json"))
        doc_json_path = path_list[0] + "doc_json/" + path_list[1] + ".json"

        with open(doc_json_path, "w") as outfile:
            json.dump(doc_data, outfile)
        return doc_json_path

    else:
        return None

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


# def update(job):
#     task_obj = Task.objects.filter(job=job)
#     for obj in task_obj:
#     for assigns in obj.task_info.filter(task_assign_info__isnull = False):
#         if assigns.account_raw_count == False:
#             if assigns.status == 1:
#                 word_count = get_weighted_word_count(obj)
#                 char_count = get_weighted_char_count(obj)
#                 assigns.task_assign_info.billable_word_count = word_count
#                 assigns.task_assign_info.billable_char_count = char_count
#                 assigns.task_assign_info.save()


from ai_auth.utils import authorize_list
from django.shortcuts import get_object_or_404, get_list_or_404

class TmxUploadView(viewsets.ViewSet):

    def list(self, request):
        project_id = request.GET.get('project')
        if not project_id:
            return Response({'msg':'project_id required'},status=400)
        # project = get_object_or_404(Project.objects.all(), id=project_id)
        # authorize(request, resource=project, actor=request.user, action="read") #
        files = TmxFileNew.objects.filter(project_id=project_id).all()
        serializer = TmxFileSerializer(files, many=True)
        return Response(serializer.data)

    def create(self, request):
        job = request.POST.get('job_id')
        data = {**request.POST.dict(), "tmx_file": request.FILES.getlist('tmx_file')}
        ser_data = TmxFileSerializer.prepare_data(data)
        serializer = TmxFileSerializer(data=ser_data,many=True)
        # job_obj = get_object_or_404(Job, id=job).proj_obj
        # authorize(request, resource=job_obj, actor=request.user, action="create") #
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            count_update.apply_async((job,),queue='medium-priority')
            task_obj = Task.objects.filter(job_id=job).last()
            ins = MTonlytaskCeleryStatus.objects.filter(Q(task_id=task_obj.id) & Q(task_name = 'analysis')).last()
            if ins:
                MTonlytaskCeleryStatus.objects.filter(Q(task_id=task_obj.id) & Q(task_name = 'analysis')).update(status=1)
        return Response(serializer.data, status=201)

    def update(self, request, pk):
        tmx_file_ins = TmxFileNew.objects.get(id=pk)
        job_id = request.POST.get("job_id", None)
        # authorize(request, resource=tmx_file_ins , actor=request.user, action="update") #
        serializer = TmxFileSerializer(tmx_file_ins, data={"job" : job_id}, partial=True)
        task_obj = Task.objects.filter(job_id=job_id).last()
        if serializer.is_valid():
            serializer.save()
            count_update.apply_async((job_id,), queue='medium-priority')
            ins = MTonlytaskCeleryStatus.objects.filter(Q(task_id=task_obj.id) & Q(task_name = 'analysis')).last()
            if ins:
                MTonlytaskCeleryStatus.objects.filter(Q(task_id=task_obj.id) & Q(task_name = 'analysis')).update(status=1)
            return Response(serializer.data, status=200)
        return Response(serializer.errors)

    def delete(self, request, pk):
        instance = TmxFileNew.objects.get(id=pk)
        # authorize(request, resource=instance , actor=request.user, action="delete") #
        task_obj = Task.objects.filter(job_id=instance.job.id)
        ins = MTonlytaskCeleryStatus.objects.filter(Q(task_id__in=task_obj) & Q(task_name = 'analysis'))
        if ins:
            MTonlytaskCeleryStatus.objects.filter(Q(task_id__in=task_obj) & Q(task_name = 'analysis')).update(status=1)
        os.remove(instance.tmx_file.path)
        count_update.apply_async((instance.job.id,),queue='medium-priority')
        instance.delete()
        return Response(status=204)



def check(uploaded_file,job):
    #for file in uploaded_files:
    tree = ET.parse(uploaded_file.tmx_file.path)
    root=tree.getroot()
    targets=[]
    for i in root.iter('header'):
        source = i.get('srclang').split('-')[0]
    for tag in root.iter('tu'):
        for node in tag.iter('tuv'):
            lang = node.get('{http://www.w3.org/XML/1998/namespace}lang')
            if lang != source:
                target = lang.split('-')[0]
                targets.append(target)
        break
    if job.source_language_code == source and job.target_language_code in targets:
        return True
    else:return False

def get_tm_analysis(doc_data,job):
        #[list(result) for key, result  in groupby(tasks, key=lambda item: item.job)]
        #print("DocData-------------->",doc_data)
        #doc_data = json.loads(doc_data)
        text_data = doc_data.get("text")
        #print("Doc data in Analysis---------------->",doc_data)
        sources = []
        sources_ = []
        tm_lists = []
        final = []
        files_list=[]
        sl = job.source_language_code
        tl = job.target_language_code

        for para in text_data.values():
            for segment in para:
                count = segment.get('seg_word_count') if segment.get('seg_word_count') else len(segment['source'].split())
                sources.append({'source':segment["source"].strip(),'count':count})##RapidFuzz does not consider leading and trailing space so we used strip()
                sources_.append(segment["source"].strip())
        c = Counter(sources_)
        files=[]
        files_ = TmxFileNew.objects.filter(job_id=job.id).all()
        for file in files_:
            print(check(file,job))
            if check(file,job):
                files.append(file)
        unrepeated = [i for n, i in enumerate(sources) if i not in sources[:n]]
        if files:
            tm_lists = tmx_read(files,job)
            files_list = [i.id for i in files]
            for i,j in enumerate(unrepeated):
                repeat = c[j.get('source')]-1 if c[j.get('source')]>1 else 0
                tt = process.extractOne(j.get('source'), tm_lists, scorer=rapidfuzz.distance.Levenshtein.normalized_similarity)
                final.append({'sent':j.get('source'),'ratio':tt[1],'index':i,'word_count':j.get('count'),'repeat':repeat})
            return final,files_list
        else:
            if len(sources_) == len(set(sources_)):
                return None,files_list
            else:
                for i,j in enumerate(unrepeated):
                    repeat = c[j.get('source')]-1 if c[j.get('source')]>1 else 0
                    final.append({'sent':j.get('source'),'ratio':0,'index':i,'word_count':j.get('count'),'repeat':repeat})
                return final,files_list

def get_word_count(tm_analysis,project,task):
    tm_100,tm_95_99,tm_85_94,tm_75_84,tm_50_74,tm_101,tm_102,new,repetition,raw_total =0,0,0,0,0,0,0,0,0,0
    char_tm_100,char_tm_95_99,char_tm_85_94,char_tm_75_84,char_tm_50_74,char_tm_101,char_tm_102,char_new,char_repetition,char_raw_total =0,0,0,0,0,0,0,0,0,0
    for i,j in enumerate(tm_analysis):
        #print("J-------------->",j)
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
                char_tm_102+=len(j.get('sent'))
            elif ratio_ == pre_ratio  or ratio_ == next_ratio:########need to check incontext logic
                tm_101+=j.get('word_count')
                char_tm_101+=len(j.get('sent'))
            else:
                tm_100+=j.get('word_count')
                char_tm_101+=len(j.get('sent'))
        elif 95 <= ratio_ <= 99:
            tm_95_99 += j.get('word_count')
            char_tm_95_99 +=len(j.get('sent'))
        elif 85 <= ratio_ <= 94:
            tm_85_94 += j.get('word_count')
            char_tm_85_94 +=len(j.get('sent'))
        elif 75 <= ratio_ <= 84:
            tm_75_84 += j.get('word_count')
            char_tm_75_84 += len(j.get('sent'))
        elif 74 <= ratio_ <= 50:
            tm_50_74 += j.get('word_count')
            char_tm_50_74 += len(j.get('sent'))
        else:
            new+=j.get('word_count')
            char_new+=len(j.get('sent'))
        if j.get('repeat'):
            repetition+=j.get('word_count')*j.get('repeat')
            char_repetition+=len(j.get('sent'))*j.get('repeat')
            #print("Repetition-------------->",repetition)
        raw_total+=j.get('word_count')
        char_raw_total+=len(j.get('sent'))
    raw_total_final = raw_total + repetition
    char_raw_total_final = char_raw_total + char_repetition
    wc = WordCountGeneral.objects.filter(Q(project_id=project.id) & Q(tasks_id=task.id)).last()
    cc = CharCountGeneral.objects.filter(Q(project_id=project.id) & Q(tasks_id=task.id)).last()
    #print("CCCCC-------------------------->",cc)
    if cc:
        obj1 = CharCountGeneral.objects.filter(Q(project_id=project.id) & Q(tasks_id=task.id))
        obj1.update(tm_100 = char_tm_100,tm_95_99 = char_tm_95_99,tm_85_94 = char_tm_85_94,tm_75_84 = char_tm_75_84,\
        tm_50_74 = char_tm_50_74,tm_101 = char_tm_101,tm_102 = char_tm_102,new_words = char_new,\
        repetition=char_repetition,raw_total=char_raw_total_final)
    else:
        cc = CharCountGeneral.objects.create(project_id=project.id,tasks_id=task.id,\
            tm_100 = char_tm_100,tm_95_99 = char_tm_95_99,tm_85_94 = char_tm_85_94,tm_75_84 = char_tm_75_84,\
            tm_50_74 = char_tm_50_74,tm_101 = char_tm_101,tm_102 = char_tm_102,new_words = char_new,\
            repetition=char_repetition,raw_total=char_raw_total_final)
    if wc:
        obj = WordCountGeneral.objects.filter(Q(project_id=project.id) & Q(tasks_id=task.id))
        obj.update(tm_100 = tm_100,tm_95_99 = tm_95_99,tm_85_94 = tm_85_94,tm_75_84 = tm_75_84,\
        tm_50_74 = tm_50_74,tm_101 = tm_101,tm_102 = tm_102,new_words = new,\
        repetition=repetition,raw_total=raw_total_final)
    else:
        wc = WordCountGeneral.objects.create(project_id=project.id,tasks_id=task.id,\
            tm_100 = tm_100,tm_95_99 = tm_95_99,tm_85_94 = tm_85_94,tm_75_84 = tm_75_84,\
            tm_50_74 = tm_50_74,tm_101 = tm_101,tm_102 = tm_102,new_words = new,\
            repetition=repetition,raw_total=raw_total_final)
    return wc




def get_tasks_for_analysis(user,instance):
    if instance.ai_user == user:
        tasks = instance.get_mtpe_tasks
    elif instance.team:
        if ((instance.team.owner == user)|(user in instance.team.get_project_manager)):
            tasks = instance.get_mtpe_tasks
        else:
            tasks = [task for job in instance.project_jobs_set.filter(~Q(target_language = None)) for task \
                in job.job_tasks_set.all() for task_assign in task.task_info.filter(assign_to_id = user)]

    else:
        tasks = [task for job in instance.project_jobs_set.filter(~Q(target_language = None)) for task \
            in job.job_tasks_set.all() for task_assign in task.task_info.filter(assign_to_id = user)]

    return tasks


@api_view(['GET',])
def get_project_analysis(request,project_id):
        

        from ai_workspace.models import MTonlytaskCeleryStatus

        tasks= []

        proj_wwc,proj_wcc = 0,0

        proj_raw_total,proj_tm_100,proj_tm_95_99,proj_tm_85_94,proj_tm_75_84,proj_tm_50_74,proj_tm_101,proj_tm_102,proj_new,proj_repetition = 0,0,0,0,0,0,0,0,0,0

        proj_char_raw_total,proj_char_tm_100,proj_char_tm_95_99,proj_char_tm_85_94,proj_char_tm_75_84,proj_char_tm_50_74,proj_char_tm_101,proj_char_tm_102,proj_char_new,proj_char_repetition = 0,0,0,0,0,0,0,0,0,0

        proj = Project.objects.filter(id=project_id).first()
        # authorize(request,resource=proj,actor=request.user,action="read") #
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
            task_ids = [i.id for i in tasks]
            for i in tasks:
                ins = MTonlytaskCeleryStatus.objects.filter(Q(task_id=i.id) & Q(task_name = 'analysis')).last()
                print("Ins-------------->",ins)
                state = analysis.AsyncResult(ins.celery_task_id).state if ins and ins.celery_task_id else None
                #print("STate------------->",state)
                if state == 'PENDING' or state == 'STARTED':
                    try:
                        cel = TaskResult.objects.get(task_id=ins.celery_task_id)
                        return Response({'msg':'Analysis is in progress. please wait','celery_id':ins.celery_task_id},status=401)
                    except TaskResult.DoesNotExist:
                        cel_task = analysis.apply_async((task_ids,proj.id,), queue='medium-priority')
                        return Response({'msg':'Analysis is in progress. please wait','celery_id':cel_task.id},status=401)
                    #print("stst",ins.status)
                elif (not ins) or state == 'FAILURE' or state == 'REVOKED':
                    cel_task = analysis.apply_async((task_ids,proj.id,), queue='medium-priority')
                    return Response({'msg':'Analysis is in progress. please wait','celery_id':cel_task.id},status=401)
                elif state == 'SUCCESS':
                    print("Ins Status---------->",ins.status)
                    if ins.status == 1:
                        cel_task = analysis.apply_async((task_ids,proj.id,),queue='medium-priority' )
                        return Response({'msg':'Analysis is in progress. please wait','celery_id':cel_task.id},status=401)
                    else:
                        pass
        #else:
        #print("Outside If")
        res=[]
        user = request.user.team.owner if request.user.team and request.user.team.owner.is_agency else request.user  #####For LSP
        analysis_tasks = get_tasks_for_analysis(user,proj)

        for task in  analysis_tasks:
            word_count = task.task_wc_general.last()
            char_count = task.task_cc_general.last()
            #print("Word_count_obj---------->",word_count)

            WWC = (word_count.new_words * 100 + word_count.tm_100 * rates.tm_100_percentage + \
                  word_count.tm_95_99 * rates.tm_95_99_percentage + word_count.tm_85_94 * rates.tm_85_94_percentage +\
                  word_count.tm_75_84 * rates.tm_75_84_percentage + word_count.tm_50_74 * rates.tm_50_74_percentage +\
                  word_count.tm_101 * rates.tm_101_percentage + word_count.tm_102 * rates.tm_102_percentage+\
                  word_count.repetition * rates.tm_repetition_percentage)/100

            #print("WWC---------------->",WWC)
            if char_count:
                WCC = (char_count.new_words * 100 + char_count.tm_100 * rates.tm_100_percentage + \
                      char_count.tm_95_99 * rates.tm_95_99_percentage + char_count.tm_85_94 * rates.tm_85_94_percentage +\
                      char_count.tm_75_84 * rates.tm_75_84_percentage + char_count.tm_50_74 * rates.tm_50_74_percentage +\
                      char_count.tm_101 * rates.tm_101_percentage + char_count.tm_102 * rates.tm_102_percentage+\
                      char_count.repetition * rates.tm_repetition_percentage)/100
            else:
                WCC = 0

            proj_wwc += round(WWC)
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

            if char_count:

                proj_wcc += round(WCC)
                proj_char_tm_100 += char_count.tm_100
                proj_char_tm_101 += char_count.tm_101
                proj_char_tm_102 += char_count.tm_102
                proj_char_tm_95_99 += char_count.tm_95_99
                proj_char_tm_85_94 += char_count.tm_85_94
                proj_char_tm_75_84 += char_count.tm_75_84
                proj_char_tm_50_74 += char_count.tm_50_74
                proj_char_new += char_count.new_words
                proj_char_repetition += char_count.repetition
                proj_char_raw_total += char_count.raw_total

            ser = WordCountGeneralSerializer(word_count,context={'weighted':round(WWC),'char_weighted':round(WCC)})
            print("WccC----------->",ser.data)

            res.append(ser.data)
        print("project wwc------------>",proj_wwc)
        proj_detail =[{'project_id':proj.id,'project_name':proj.project_name,'weighted':proj_wwc,'new':proj_new,'repetition':proj_repetition,\
                    'tm_50_74':proj_tm_50_74,'tm_75_84':proj_tm_75_84,'tm_85_94':proj_tm_85_94,'tm_95_99':proj_tm_95_99,\
                    'tm_100':proj_tm_100,'tm_101':proj_tm_101,'tm_102':proj_tm_102,'raw_total':proj_raw_total,\
                    'weighted_char':proj_wcc,'char_new':proj_char_new,'char_repetition':proj_char_repetition,\
                    'char_tm_50_74':proj_char_tm_50_74,'char_tm_75_84':proj_char_tm_75_84,'char_tm_85_94':proj_char_tm_85_94,'char_tm_95_99':proj_char_tm_95_99,\
                    'char_tm_100':proj_char_tm_100,'char_tm_101':proj_char_tm_101,'char_tm_102':proj_char_tm_102,'char_raw_total':proj_char_raw_total}]
        ser = UserDefinedRateSerializer(rates)
        return Response({'payable_rate':ser.data,'project_wwc':proj_detail,'task_wwc':res})



def get_weighted_word_count(task):
    if task.task_wc_general.last() == None:
        analysis([task.id],task.job.project.id)
    else:
        temp1 = [i.id for i in task.job.tmx_file_job.all()]
        temp2 = [i.tmx_file_obj_id for i in task.task_wc_general.last().wc_general.all()]
        temp3 = set(temp1) ^ set(temp2)
        if temp3:
            task.task_wc_general.last().wc_general.all().delete()
            analysis([task.id],task.job.project.id)

    rates = UserDefinedRate.objects.filter(user = task.job.project.ai_user).last()
    if not rates:
        rates = UserDefinedRate.objects.filter(is_default = True).first()

    ins = MTonlytaskCeleryStatus.objects.filter(Q(task_id=task.id) & Q(task_name = 'analysis')).last()
    print("status------------------>",ins)
    if not ins or ins.status == 1:
        analysis([task.id],task.job.project.id)

    word_count = task.task_wc_general.last()
    WWC = (word_count.new_words * 100 + word_count.tm_100 * rates.tm_100_percentage + \
          word_count.tm_95_99 * rates.tm_95_99_percentage + word_count.tm_85_94 * rates.tm_85_94_percentage +\
          word_count.tm_75_84 * rates.tm_75_84_percentage + word_count.tm_50_74 * rates.tm_50_74_percentage +\
          word_count.tm_101 * rates.tm_101_percentage + word_count.tm_102 * rates.tm_102_percentage+\
          word_count.repetition * rates.tm_repetition_percentage)/100
    print("WWC-------------->",WWC)
    return round(WWC)

def get_weighted_char_count(task):
    rates = UserDefinedRate.objects.filter(user = task.job.project.ai_user).last()
    if not rates:
        rates = UserDefinedRate.objects.filter(is_default = True).first()

    if task.task_cc_general.last() == None:
        analysis([task.id],task.job.project.id)
    else:
        temp1 = [i.id for i in task.job.tmx_file_job.all()]
        temp2 = [i.tmx_file_obj_id for i in task.task_wc_general.last().wc_general.all()]
        temp3 = set(temp1) ^ set(temp2)
        if temp3:
            task.task_wc_general.last().wc_general.all().delete()
            analysis([task.id],task.job.project.id)

    ins = MTonlytaskCeleryStatus.objects.filter(Q(task_id=task.id) & Q(task_name = 'analysis')).last()
    print("status------------------>",ins.status)
    if not ins or ins.status == 1:
        analysis([task.id],task.job.project.id)

    char_count = task.task_cc_general.last()
    WCC = (char_count.new_words * 100 + char_count.tm_100 * rates.tm_100_percentage + \
          char_count.tm_95_99 * rates.tm_95_99_percentage + char_count.tm_85_94 * rates.tm_85_94_percentage +\
          char_count.tm_75_84 * rates.tm_75_84_percentage + char_count.tm_50_74 * rates.tm_50_74_percentage +\
          char_count.tm_101 * rates.tm_101_percentage + char_count.tm_102 * rates.tm_102_percentage+\
          char_count.repetition * rates.tm_repetition_percentage)/100

    return round(WCC)


# @api_view(['GET',])
# def get_project_analysis(request,project_id):
#
#         tasks= []
#
#         proj_wwc = 0
#
#         proj_raw_total,proj_tm_100,proj_tm_95_99,proj_tm_85_94,proj_tm_75_84,proj_tm_50_74,proj_tm_101,proj_tm_102,proj_new,proj_repetition = 0,0,0,0,0,0,0,0,0,0
#
#         proj = Project.objects.filter(id=project_id).first()
#
#         user = proj.ai_user
#
#         rates = UserDefinedRate.objects.filter(user = user).last()
#         if not rates:
#             rates = UserDefinedRate.objects.filter(is_default = True).first()
#
#         for _task in proj.get_mtpe_tasks:
#             if _task.task_wc_general.last() == None:
#                 tasks.append(_task)
#             else:
#                 temp1 = [i.id for i in _task.job.tmx_file_job.all()]
#                 temp2 = [i.tmx_file_obj_id for i in _task.task_wc_general.last().wc_general.all()]
#                 temp3 = set(temp1) ^ set(temp2)
#                 if temp3:
#                     tasks.append(_task)
#                     _task.task_wc_general.last().wc_general.all().delete()
#
#         if tasks:
#
#             for task in tasks:
#
#                 file_path = get_json_file_path(task)
#
#                 doc_data = json.load(open(file_path))
#
#                 if type(doc_data) == str:
#
#                     doc_data = json.loads(doc_data)
#
#                 raw_total = doc_data.get('total_word_count')
#
#                 tm_analysis,files_list = get_tm_analysis(doc_data,task.job)
#                 print("Tm Analysis----------->",tm_analysis)
#
#                 if tm_analysis:
#                     word_count = get_word_count(tm_analysis,proj,task,raw_total)
#                 else:
#                     word_count = WordCountGeneral.objects.create(project_id =project_id,tasks_id=task.id,\
#                                 new_words=doc_data.get('total_word_count'),raw_total=raw_total)
#                 [WordCountTmxDetail.objects.create(word_count=word_count,tmx_file_id=i,tmx_file_obj_id=i) for i in files_list]
#
#         res=[]
#         for task in  proj.get_mtpe_tasks:
#             word_count = task.task_wc_general.last()
#
#             WWC = (word_count.new_words * 100 + word_count.tm_100 * rates.tm_100_percentage + \
#                   word_count.tm_95_99 * rates.tm_95_99_percentage + word_count.tm_85_94 * rates.tm_85_94_percentage +\
#                   word_count.tm_75_84 * rates.tm_75_84_percentage + word_count.tm_50_74 * rates.tm_50_74_percentage +\
#                   word_count.tm_101 * rates.tm_101_percentage + word_count.tm_102 * rates.tm_102_percentage)/100
#
#             proj_wwc += WWC
#             proj_tm_100 += word_count.tm_100
#             proj_tm_101 += word_count.tm_101
#             proj_tm_102 += word_count.tm_102
#             proj_tm_95_99 += word_count.tm_95_99
#             proj_tm_85_94 += word_count.tm_85_94
#             proj_tm_75_84 += word_count.tm_75_84
#             proj_tm_50_74 += word_count.tm_50_74
#             proj_new += word_count.new_words
#             proj_repetition += word_count.repetition
#             proj_raw_total += word_count.raw_total
#
#             res.append({'task_id':task.id,'task_file':task.file.filename,'task_lang_pair':task.job.source_target_pair_names,'weighted':round(WWC),'new':word_count.new_words,'repetition':word_count.repetition,\
#             'tm_50_74':word_count.tm_50_74,'tm_75_84':word_count.tm_75_84,'tm_85_94':word_count.tm_85_94,'tm_95_99':word_count.tm_95_99,\
#             'tm_100':word_count.tm_100,'tm_101':word_count.tm_101,'tm_102':word_count.tm_102,'raw_total':word_count.raw_total})
#
#         proj_detail =[{'project_id':proj.id,'project_name':proj.project_name,'weighted':round(proj_wwc),'new':proj_new,'repetition':proj_repetition,\
#                     'tm_50_74':proj_tm_50_74,'tm_75_84':proj_tm_75_84,'tm_85_94':proj_tm_85_94,'tm_95_99':proj_tm_95_99,\
#                     'tm_100':proj_tm_100,'tm_101':proj_tm_101,'tm_102':proj_tm_102,'raw_total':proj_raw_total}]
#         ser = UserDefinedRateSerializer(rates)
#         return Response({'payable_rate':ser.data,'project_wwc':proj_detail,'task_wwc':res})


# class ReportDownloadView(APIView):
#
#     @staticmethod
#     def download_excel(path, new, rep, c100, \
#                        c95_99, c85_94, c75_84, c50_74, c101, c102, raw, proj=None, task=None):
#
#         if proj != None:
#
#             wwc = round(new + (0.3 * rep) + c50_74 + (0.6 * c75_84) + (0.6 * c85_94) + (0.6 * c95_99) + \
#                   (0.3 * c100) + (0.3 * c101) + (0.3 * c102))
#
#             workbook = xlsxwriter.Workbook(path)
#
#             if task == None:
#                 worksheet = workbook.add_worksheet(proj.project_name)
#                 worksheet.write('A1', 'Project name')
#                 worksheet.write('B1', proj.project_name)
#             else:
#                 worksheet = workbook.add_worksheet(proj.project_name)
#                 worksheet.write('A1', 'Task')
#                 worksheet.write('B1', os.path.splitext(task.file.filename[0]) + "(" + task.job.source_language.language + "-" \
#                                        + task.job.source_language.language + ")")
#
#             # Row 2
#             worksheet.write('B2', 'Total')
#             worksheet.write('C2', 'Weighted')
#             worksheet.write('D2', 'New')
#             worksheet.write('E2', 'Repetition')
#             worksheet.write('F2', '50-74%')
#             worksheet.write('G2', '75-84%')
#             worksheet.write('H2', '85-94%')
#             worksheet.write('I2', '95-99%')
#             worksheet.write('J2', '100%')
#             worksheet.write('K2', '101%')
#             worksheet.write('L2', '102%')
#
#             # Row 3
#             worksheet.write('A3', 'Payable rate')
#             worksheet.write('D3', '100%')
#             worksheet.write('E3', '30%')
#             worksheet.write('F3', '100%')
#             worksheet.write('G3', '60%')
#             worksheet.write('H3', '60%')
#             worksheet.write('I3', '60%')
#             worksheet.write('J3', '30%')
#             worksheet.write('K3', '30%')
#             worksheet.write('L3', '30%')
#
#             # Row 4
#             worksheet.write('B4', raw)
#             worksheet.write('C4', wwc)
#             worksheet.write('D4', new)
#             worksheet.write('E4', rep)
#             worksheet.write('F4', c50_74)
#             worksheet.write('G4', c75_84)
#             worksheet.write('H4', c85_94)
#             worksheet.write('I4', c95_99)
#             worksheet.write('J4', c100)
#             worksheet.write('K4', c101)
#             worksheet.write('L4', c102)
#
#             workbook.close()
#             return download_file(path)
#
#     def get(self, request):
#         task_id = request.GET.get("task_id", None)
#         project_id = request.GET.get("project_id", None)
#         download_type = request.GET.get("download_type")
#
#         # # Checking for required fields
#         if not (project_id or task_id):
#             return Response({"error": "Required fields missings!"}, status=400)
#
#         if project_id:
#
#             # Setting the file location for the report
#             proj = Project.objects.get(id=project_id)
#
#             if not os.path.exists(os.path.join(proj.project_dir_path, "analysis_reports")):
#                 os.mkdir(os.path.join(proj.project_dir_path, "analysis_reports"))
#
#             report_path = os.path.join(proj.project_dir_path, "analysis_reports", proj.project_name + ".xlsx")
#
#
#             # Initializing word count values
#             pnew, prep, p100, p95_99, p85_94, p75_84, p50_74, p101, p102, praw = \
#             0, 0, 0, 0, 0, 0, 0, 0, 0, 0
#
#             # Adding word count from each task
#             task_wcs = WordCountGeneral.objects.filter(project_id=project_id)
#             for tk_wc in task_wcs:
#                 pnew += tk_wc.new_words
#                 prep += tk_wc.repetition
#                 p100 += tk_wc.tm_100
#                 p95_99 += tk_wc.tm_95_99
#                 p85_94 += tk_wc.tm_85_94
#                 p75_84 += tk_wc.tm_75_84
#                 p50_74 += tk_wc.tm_50_74
#                 p101 += tk_wc.tm_101
#                 p102 += tk_wc.tm_102
#                 praw += tk_wc.raw_total
#
#             return ReportDownloadView.download_excel(report_path, pnew, prep, p100, p95_99, p85_94, \
#                                                      p75_84, p50_74, p101, p102, praw, proj=proj, task=None)
#
#         else:
#
#             # Setting the file location for the report
#             proj = Task.objects.get(id=task_id).job.project
#             task = Task.objects.get(id=task_id)
#             report_path = os.path.join(proj.project_dir_path, "analysis_reports",
#                     os.path.splitext(task.file.filename[0]) + "(" + task.job.source_language.language + "_" \
#                                        + task.job.source_language.language + ")" + ".xlsx")
#
#             twc = WordCountGeneral.objects.filter(tasks_id=task_id).first()
#
#             return ReportDownloadView.download_excel(report_path, twc.new_words, twc.repetition, twc.tm_100, twc.tm_95_99, twc.tm_85_94, \
#                                                      twc.tm_75_84, twc.tm_50_74, twc.tm_101, twc.tm_102, praw, proj=proj, task=task)


class ReportDownloadView(APIView):

    @staticmethod
    def download_excel(path, proj):

        workbook = xlsxwriter.Workbook(path)
        worksheet = workbook.add_worksheet(proj.project_name)

        write_project_header(workbook, worksheet, proj)

        write_commons(workbook, worksheet, proj)

        write_data(workbook, worksheet, proj)

        workbook.close()
        return download_file(path)

    def get(self, request):
        task_id = request.GET.get("task_id", None)
        project_id = request.GET.get("project_id", None)
        download_type = request.GET.get("download_type")

        # Checking for required fields
        if not (project_id or task_id):
            return Response({"error": "Required fields missings!"}, status=400)

        if project_id:

            # Setting the file location for the report
            proj = Project.objects.get(id=project_id)
            if not os.path.exists(os.path.join(proj.project_dir_path, "analysis_reports")):
                os.mkdir(os.path.join(proj.project_dir_path, "analysis_reports"))
            report_path = os.path.join(proj.project_dir_path, "analysis_reports", proj.project_name + ".xlsx")

            return ReportDownloadView.download_excel(report_path, proj)



@api_view(['GET',])
def download_tmx_file(request,file_id):
    try:
        instance = TmxFileNew.objects.get(id=file_id).tmx_file
        return download_file(instance.path)
    except:
        return Response({'msg':'No file Exists'})



def notify_word_count(task_assign,word_count,char_count):
    from ai_marketplace.serializers import ThreadSerializer
    from ai_marketplace.models import ChatMessage
    print("$$$$$$$$$$$")
    receiver = task_assign.assign_to
    receivers = []
    receivers =  receiver.team.get_project_manager if (receiver.team and receiver.team.owner.is_agency) or receiver.is_agency else []
    receivers.append(receiver)
    print("Rece",receivers)
    sender =  task_assign.task_assign_info.assigned_by
    print("send",sender)
    unit = task_assign.task_assign_info.mtpe_count_unit.id
    obj = task_assign.task
    proj = obj.job.project.project_name
    for i in receivers:
        thread_ser = ThreadSerializer(data={'first_person':sender.id,'second_person':i.id})
        if thread_ser.is_valid():
            thread_ser.save()
            thread_id = thread_ser.data.get('id')
        else:
            thread_id = thread_ser.errors.get('thread_id')
        message = '''For your kind information,

            TMX file(s) for the project ({proj}) have been updated.
            Weighted word count for the task ({Filename}(Languagepair), {task_id}) will be affected.
            Payments will be updated accordingly.

            For further assistance or information, please contact the Project Owner.'''.format(proj=proj,Filename=obj.file.filename,Languagepair=obj.job.source_target_pair_names,task_id=obj.ai_taskid)

        # if unit == 1:
        #     '''For your kind information,
        #
        #     TMX file(s) for the project ({{proj}}) have been updated.
        #     Weighted word count for the task ({{Filename + Language pair}}, task_id) will be affected.
        #     Payments will be updated accordingly.
        #
        #     For further assistance or information, please contact the Project Owner.'''
        #     message = "Weighted Word Count in Task with task_id "+ obj.ai_taskid +" has changed because of tmx file update.your payment will be changed.New Weighted word count: "+ str(word_count)+"."
        # if unit == 2:
        #     message = "Weighted Char Count in Task with task_id "+ obj.ai_taskid +" has changed because of tmx file update.your payment will be changed.New Weighted Char count: "+ str(char_count)+"."
        print("MSG---------->",message)
        if thread_id:
            msg = ChatMessage.objects.create(message=message,user=sender,thread_id=thread_id)
            print("Chat--------->",msg)
            notify.send(sender, recipient=i, verb='Message', description=message,thread_id=int(thread_id))
