from django.http import HttpRequest, HttpResponse


class LogRequestMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest):
        try:
            body = request.body.decode()
            print(f"REQUEST {request.method} {request.path} {body}")
        except UnicodeDecodeError:
            print("REQUEST", request.method, request.path, request.body)
        return self.get_response(request)
