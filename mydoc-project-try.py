class MyDocFilter(django_filters.FilterSet):
    proj_name = django_filters.CharFilter(lookup_expr='icontains')
    doc_name = django_filters.CharFilter(field_name='related_docs__doc_name',lookup_expr='icontains')
    class Meta:
        model = WriterProject
        fields = ['proj_name','doc_name']


class MyDocumentsView(viewsets.ModelViewSet):

    serializer_class = WriterProjectSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend,SearchFilter,CaseInsensitiveOrderingFilter]
    ordering_fields = ['proj_name','related_docs__doc_name','id']
    filterset_class = MyDocFilter
    paginator = PageNumberPagination()
    ordering = ('-id')
    paginator.page_size = 20
    # https://www.django-rest-framework.org/api-guide/filtering/

    def get_queryset(self):
        user = self.request.user
        ai_user = user.team.owner if user.team and user in user.team.get_project_manager else user 
        return WriterProject.objects.filter(ai_user=user)#.order_by('-id')
        

    def list(self, request, *args, **kwargs):
        paginate = request.GET.get('pagination',True)
        queryset = self.filter_queryset(self.get_queryset())
        if paginate == 'False':
            serializer = WriterProjectSerializer(queryset, many=True)
            return Response(serializer.data)
        pagin_tc = self.paginator.paginate_queryset(queryset, request , view=self)
        serializer = WriterProjectSerializer(pagin_tc, many=True)
        response = self.get_paginated_response(serializer.data)
        return  response

    def retrieve(self, request, pk):
        queryset = self.get_queryset()
        ins = get_object_or_404(queryset, pk=pk)
        serializer = MyDocumentSerializer(ins)
        return Response(serializer.data)

    def create(self, request):
        file = request.FILES.get('file',None)
        ai_user = request.user.team.owner if request.user.team else request.user
        writer_proj = request.POST.get('project',None)
        if not writer_proj:
            writer_obj = WriterProject.objects.create(ai_user_id = ai_user.id)
            writer_proj = writer_obj.id
        ser = MyDocumentSerializer(data={**request.POST.dict(),'project':writer_proj,'file':file,'ai_user':ai_user.id,'created_by':request.user.id})
        if ser.is_valid(raise_exception=True):
            ser.save()
            return Response(ser.data, status=201)
        return Response(ser.errors)
        
    def update(self, request, pk, format=None):
        ins = MyDocuments.objects.get(id=pk)
        file = request.FILES.get('file')
        if file:
            ser = MyDocumentSerializer(ins,data={**request.POST.dict(),'file':file},partial=True)
        else:
             ser = MyDocumentSerializer(ins,data={**request.POST.dict()},partial=True)
        if ser.is_valid(raise_exception=True):
            ser.save()
            return Response(ser.data, status=200)
        return Response(ser.errors)

    def destroy(self, request, pk):
        ins = MyDocuments.objects.get(id=pk)
        if ins.file:
            os.remove(ins.file.path)
        ins.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
