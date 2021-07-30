from django.shortcuts import render, redirect, reverse, get_object_or_404
from django import views
from .forms import DocumentListForm, SegmentListForm
from .serializers import DocumentSerializerV2
from django.http import JsonResponse
from .models import  Segment
from .serializers import SegmentSerializer
# Create your views here.

class DocumentListView(views.View):
    def get(self, request):
       form = DocumentListForm()
       form.fields["documents"].queryset = (
           form.fields["documents"].queryset.filter(
                task__file__project__ai_user = self.request.user
           )
       )
       return render(
           request, "document-list.html", context={"form": form}
       )

    def post(self, request):
        form = DocumentListForm(request.POST or None)
        if form.is_valid():
            document = form.cleaned_data.get("documents")
            ser_data = DocumentSerializerV2(document).data
            return redirect(
                reverse("ws_okapi:segments-list", kwargs={"document_id": ser_data.get("document_id")})
            )

class SegmentListView(views.View):
    def get(self, request, document_id):
        form = SegmentListForm()
        form.fields["segment"].queryset = (
            form.fields["segment"].queryset.filter(
                text_unit__document_id = document_id
            )
        )
        return render(
            request, "segment-list.html", context={"form": form}
        )

    def post(self, request, document):
        form = SegmentListForm(request.POST or None)
        if form.is_valid():
            pass

class SegmentDetailView(views.View):
    def get(self, request, segment_id):
        qs = Segment.objects.all()
        segment = get_object_or_404(qs, id=segment_id)
        form_data = SegmentSerializer(segment).data
