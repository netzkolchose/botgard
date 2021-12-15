from threading import local

_thread_locals = local()


def get_current_request():
    return getattr(_thread_locals, "request", None)


def get_current_user():
    """ returns the current user, if exists, otherwise returns None """
    request = get_current_request()
    if request:
        return getattr(request, "user", None)


class GlobalRequestMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _thread_locals.request = request
        response = self.get_response(request)
        del _thread_locals.request
        return response
