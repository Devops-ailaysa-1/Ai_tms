
from rest_framework.pagination import PageNumberPagination ,LimitOffsetPagination

class TemplateGlobalPagination(PageNumberPagination):
    page_size = 20
    page_query_param = 'page'
    page_size_query_param = 'page_size'
     

class MyTemplateDesignPagination(PageNumberPagination):
    page_size = 20
    page_query_param = 'page'
    page_size_query_param = 'page_size'
    max_page_size = 100


class CanvasDesignListViewsetPagination(PageNumberPagination):
    page_size = 20
    page_query_param = 'page'
    page_size_query_param = 'page_size'