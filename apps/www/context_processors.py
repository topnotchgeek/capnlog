from .models import TempHumidity
from conf import settings


def all_pages(request):
    rht = None
    try:
        rht = TempHumidity.objects.latest('reading_time')
    except:
        rht = None
    return {
        'STATIC_URL': settings.STATIC_URL,
        'BOOTSTRAP_VERSION': settings.BOOTSTRAP_VERSION,
        'JQUERY_VERSION': settings.JQUERY_VERSION,
        'rht':  rht

    }
