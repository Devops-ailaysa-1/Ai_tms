from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import TmxFileSerializer


class TmxUploadView(APIView):

    def get(self, request, project_id):
        files = TmxFile.objects.filter(project_id=project_id).all()
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


# class ProjectAnalysis(APIView):
#
#     def get(self, request):
#         pass

