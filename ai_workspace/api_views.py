from ai_auth.authentication import IsCustomer
from rest_framework import viewsets
from rest_framework.response import Response
from .serializers import ProjectSerializer
from rest_framework.permissions import AllowAny, IsAuthenticated
from .models import Project

class ProjectView(viewsets.ModelViewSet):
	#permission_classes = [IsCustomer]
	serializer_class = ProjectSerializer
	queryset = Project.objects.all()

	def create(self, request):
		data = request.data 
		serializer = ProjectSerializer(data = data)
		if serializer.is_valid(raise_exception=True):
			serializer.save()
			return Response(serializer.data)





