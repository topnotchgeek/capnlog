from conf import settings


def all_pages(request):
    return {
        'STATIC_URL': settings.STATIC_URL,
        'BOOTSTRAP_VERSION': settings.BOOTSTRAP_VERSION,
        'JQUERY_VERSION': settings.JQUERY_VERSION
    }
