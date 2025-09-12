from django.db import transaction


def atomic_request_middleware(get_response):

    @transaction.atomic
    def middleware(request):
        return get_response(request)

    return middleware
