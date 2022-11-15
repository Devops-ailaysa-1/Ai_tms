from rest_framework.response import Response
from rest_framework.views import APIView
import re
from .models import TmxFileNew
from .serializers import TmxFileSerializer
from ai_workspace.serializers import TaskSerializer
from ai_workspace.models import Project, File, Task
from ai_tm import match


def get_json_file_path(task):
    source_file_path = TaskSerializer(task).data["source_file_path"]
    path_list = re.split("source/", source_file_path)
    return path_list[0] + "doc_json/" + path_list[1] + ".json"

def remove_tags(string):
    return re.sub(rf'</?\d+>', "", string)


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
        sl = job.source_language_code
        tl = job.target_language_code

        for para in text_data.values():
            for segment in para:
                sources.append(segment["source"].strip())

        files = TmxFileNew.objects.filter(job_id=job.id).all()

        for file in files:
            with open(file, 'rb') as fin:
                tm_file = tmxfile(fin, sl, tl)

            for node in tm_file.unit_iter():
                tm_lists.append(remove_tags(node.source))
            for i,j in enumerate(sources):
                tt = match.extractOne(j,tm_list)
                final.append({'sent':j,'ratio':tt[1],'index':i,'word_count':j.split().count()})
        return final




class ProjectAnalysis(APIView):

    def get(self, request, project_id):

        temp = ProjectAnalysisTemplate.objects.filter(user=job.project.ai_user).first()
        if not temp:
            temp = ProjectAnalysisTemplate.objects.filter(is_default=True).first()

        proj = Project.objects.filter(id=project_id).first()

        proj_tasks = proj.get_tasks

        for task in proj_tasks:
            file_path = get_json_file_path(task)
            doc_data = json.load(open(file_path))
            tm_analysis = get_tm_analysis(doc_data,task.job)
            print("Tm-------------->",tm_analysis)
            for i in tm_analysis:
                ratio_ = i.get('ratio')*100
                range = DefinedRange.objects.filter(temp=temp).filter(Q(start__lte=ratio_)) | Q(end__gt=ratio_).first()
                WordCount.objects.create(project=proj,task=task,range=range,words=i.get('word_count'))

        #tm_jobs = TmxFile.objects.filter(project_id=project_id)

        #proj_jobs = Job.objects.filter(project=project_id)

        # for tm_job in tm_jobs:
