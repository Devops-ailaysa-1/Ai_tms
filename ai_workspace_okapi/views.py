from django.shortcuts import render, redirect, reverse, get_object_or_404
from django import views
from .forms import DocumentListForm, SegmentListForm, SegmentForm
from .serializers import DocumentSerializerV2
from django.http import JsonResponse, HttpResponse
from .models import  Segment
from .serializers import SegmentSerializer, MT_RawSerializer
from .api_views import MT_RawAndTM_View, SegmentsUpdateView, DocumentToFile
import os
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

    def post(self, request, document_id):
        form = SegmentListForm(request.POST or None)
        if form.is_valid():
            segment_id = form.cleaned_data["segment"].id
            return redirect(
                        reverse("ws_okapi:segment-update-dj", kwargs={"segment_id": segment_id})
                    )
        return render(
                    request, "segment-list.html", context={"form": form}
                )

class SegmentUpdateView(views.View):
    def get_instance(self, segment_id):
        qs = Segment.objects.all()
        segment = get_object_or_404(qs, id=segment_id)
        return segment

    def get(self, request, segment_id):
        segment = self.get_instance(segment_id)
        mt_raw = MT_RawAndTM_View.get_data(request, segment_id)[0].data["mt_raw"]
        form = SegmentForm(instance=segment, initial={"mt_raw": mt_raw})
        return render(request, "segment-update.html", context={"form": form})

    def post(self, request, segment_id):
        segment = self.get_instance(segment_id)
        form = SegmentForm(request.POST)
        if form.is_valid():
            res_data = SegmentsUpdateView.get_update(segment, form.cleaned_data, request)
            return JsonResponse(
                res_data.data, safe=False
            )

class DownloadDocumentToFileView(views.View):
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
        form = DocumentListForm(request.POST)
        if form.is_valid():
            res = DocumentToFile.document_data_to_file(request, form.cleaned_data["documents"].id)
            if res.status_code in [200, 201]:
                file_path = res.text
                if os.path.isfile(res.text):
                    if os.path.exists(file_path):
                        with open(file_path, 'rb') as fh:
                            response = HttpResponse(fh.read(), content_type="application/vnd.ms-excel")
                            response['Content-Disposition'] = 'inline; filename=' + os.path.basename(file_path)
                            return response
            return JsonResponse({"msg": "something went to wrong in okapi file processing"}, safe=False)








from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .serializers import SelflearningAssetSerializer
from rest_framework.response import Response
from ai_workspace_okapi.models import SelflearningAsset,Document
from ai_staff.models import Languages
from rest_framework import status

#self learning segment
class SelflearningApi(viewsets.ViewSet):
    permission_classes = [IsAuthenticated,]
    # lang=get_object_or_404(Languages,id=17)

    def list(self,request):
        slf=SelflearningAsset.objects.filter(user=self.request.user).order_by('-id')
        slf_learning_serializer=SelflearningAssetSerializer(slf,many=True)
        return Response(slf_learning_serializer.data,status=status.HTTP_200_OK)
    
    def create(self,request,document_id): 
        doc=get_object_or_404(Document,id=document_id)
        lang=get_object_or_404(Languages,id=doc.target_language_id)
        user=self.request.user
        slf_lrn_list=SelflearningAsset.objects.filter(user=user,target_language=lang)
        # print(doc.target_language_id,'-----',doc.target_language)
        
        #input data
        in_word=request.POST.get('source',None)
        edited_word=request.POST.get('edited',None)

        slf_lrn_list=slf_lrn_list.filter(source_word=in_word)
        if slf_lrn_list.count() < 5:
            slf_lrn_create=SelflearningAsset.objects.create(user=user,target_language=lang,source_word=in_word,edited_word=edited_word)
            return Response(status=status.HTTP_201_CREATED)
                        
        else:
            first_out=slf_lrn_list.first().delete()
            slf_lrn_create=SelflearningAsset.objects.create(user=user,target_language=lang,source_word=in_word,edited_word=edited_word)
            return Response(status=status.HTTP_201_CREATED)