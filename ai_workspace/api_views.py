from rest_framework import viewsets
from rest_framework.response import Response
from .serializers import ProjectSerializer
from .models import Project

class ProjectView(viewsets.ModelViewSet):
	serializer_class = ProjectSerializer
	queryset = Project.objects.all()

	def create(self, request):

		data = request.data 
		serializer = ProjectSerializer(data = data)
		if serializer.is_valid(raise_exception=True):
			serializer.save()
			return Response(serializer.data)





