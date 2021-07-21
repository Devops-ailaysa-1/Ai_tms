from .serializers import DocumentSerializer
from .models import Document
from rest_framework import viewsets

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
