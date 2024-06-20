from django.middleware.gzip import GZipMiddleware
from django.utils.decorators import decorator_from_middleware_with_args

class CustomGZipMiddleware(GZipMiddleware):
    def process_response(self, request, response):
        # Check if response is a streaming response
        if getattr(response, 'streaming', False):
            return response
        return super().process_response(request, response)

# Decorator for using in views if needed
gzip_page = decorator_from_middleware_with_args(CustomGZipMiddleware)
