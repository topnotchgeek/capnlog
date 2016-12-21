from django.conf.urls import url, include
from rest_framework import routers
from .viewsets import *

router = routers.DefaultRouter()

router.register('users', UserViewSet)
router.register('groups', GroupViewSet)
router.register('entries', EntryViewSet)
router.register('temps', TempHumViewSet)
router.register('webcams', WebcamViewSet)
router.register('images', SnapshotViewSet)

urlpatterns = [
    url(r'^', include(router.urls)),
]
