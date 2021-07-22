from .serializers import DocumentSerializer
from .models import Document, File
from rest_framework import viewsets
from rest_framework import views
from django.shortcuts import get_object_or_404

class IsUserCompletedInitialSetup(permissions.BasePermission):

    def has_permission(self, request, view):
        # user = (get_object_or_404(AiUser, pk=request.user.id))
        if request.user.user_permissions.filter(codename="user-attribute-exist").first():
            return True


class DocumentView(viewsets.ModelViewSet):
    permission_classes = [IsUserCompletedInitialSetup]
    serializer_class = DocumentSerializer

    def get_queryset(self, request):
        if request.user.user_attribute.user_type==1:
            Document.objects.filter()

    # protected String processor_name;
    # protected String source_language;
    # protected String target_language;
    # protected String output_type;
    # protected String source_file_path;
    # protected String extension;

class GetDocumentFromFile(views.APIView):

    def get(self, request, file_id):
        file_set = File.objects.extra(
          select={
            'source_file_path': 'source_file_path'
          }
        ).values(
          'renamed_value'
        ).all()
        file = get_object_or_404(file_set, pk=file_id)
        # File.objects
        return
