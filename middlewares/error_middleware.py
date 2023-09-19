from django.http import HttpResponse
import json
from pymongo import MongoClient
from django.utils.deprecation import MiddlewareMixin
# Previous imports and timing middleware should remain unchanged
import requests

from rest_framework.response import Response
from django.http import JsonResponse
from rest_framework.response import Response

def error_middleware(get_response):
    def middleware(request):
        # This method does nothing, all we want is exception processing
        return get_response(request)

    def process_exception(request, exception):
        client = MongoClient("localhost", 27017)
        db = client["log"]
        coll = db["error_log"]
        coll.insert_one({"url": request.get_raw_uri(),
            "data": request.POST.dict(), "user": request.user.username,
            "url_params": request.GET.dict()})

        client.close()
        return JsonResponse({"error": str(exception)}, status=400)

    middleware.process_exception = process_exception

    return middleware

class StackOverflowMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        if response.status_code == 401:
            client = MongoClient("localhost", 27017)
            db = client["log"]
            coll = db["error_log"]
            result = coll.insert_one({"url": request.get_raw_uri(),
             "data": request.POST.dict(), "user": request.user.username,
             "url_params": request.GET.dict()})

            print("inserted id---->", str(result.inserted_id))

            client.close()

        return response


