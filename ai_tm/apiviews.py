from rest_framework.response import Response
from rest_framework.views import APIView

from .models import TmxFileNew
from .serializers import TmxFileSerializer

from ai_workspace.models import Project, File, Task


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


class ProjectAnalysis(APIView):

    def get(self, request, project_id):

        # new_words = models.IntegerField(null=True, blank=True)
        # repetition = models.IntegerField(null=True, blank=True)
        # cross_file_rep = models.IntegerField(null=True, blank=True)
        # tm_100 = models.IntegerField(null=True, blank=True)
        # tm_95_99 = models.IntegerField(null=True, blank=True)
        # tm_85_94 = models.IntegerField(null=True, blank=True)
        # tm_75_84 = models.IntegerField(null=True, blank=True)
        # tm_50_74 = models.IntegerField(null=True, blank=True)
        # tm_102 = models.IntegerField(null=True, blank=True)
        # tm_101 = models.IntegerField(null=True, blank=True)
        # raw_total = models.IntegerField(null=True, blank=True)

        tmx_files = TmxFileNew.objects.filter(project_id=project_id).all()

        project_files = File.objects.filter(project=project_id)

        proj = Project.objects.filter(id=project_id).first()

        tm_jobs = TmxFile.objects.filter(project_id=project_id)

        proj_jobs = Job.objects.filter(project=project_id)

        # for tm_job in tm_jobs:
