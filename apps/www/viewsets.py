import json
import os
import logging

from django.contrib.auth.models import User, Group
from django.http.response import JsonResponse, HttpResponseBadRequest, HttpResponse, HttpResponseNotFound
from rest_framework import viewsets
from rest_framework.decorators import detail_route

from .serializers import UserSerializer, GroupSerializer, EntrySerializer, TempHumSerializer, SnapshotSerializer, \
    WebcamSerializer, StationSerializer
from .models import BlogEntry, TempHumidity, Webcam, Snapshot, Station

logger = logging.getLogger(__name__)

class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer


class GroupViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """
    queryset = Group.objects.all()
    serializer_class = GroupSerializer


class EntryViewSet(viewsets.ModelViewSet):
    queryset = BlogEntry.objects.all().order_by('-create_time')
    serializer_class = EntrySerializer


class StationViewSet(viewsets.ModelViewSet):
    lookup_field = 'name'
    queryset = Station.objects.all()
    serializer_class = StationSerializer

    @detail_route(methods=['post'])
    def reading(self, request, name=None):
        stn = self.get_object()
        try:
            rht = stn.create_reading(json.loads(request.body))
            if rht:
                return JsonResponse({"result": "success", "station_id": stn.id, "rht_id": rht.id }, status=201)
        except ValueError:
            pass
        return HttpResponseBadRequest()


class TempHumViewSet(viewsets.ModelViewSet):
    queryset = TempHumidity.objects.order_by('-reading_time')[:24]
    serializer_class = TempHumSerializer


class WebcamViewSet(viewsets.ModelViewSet):
    lookup_field = 'slug'
    serializer_class = WebcamSerializer
    queryset = Webcam.objects.all()

    @detail_route(methods=['post'])
    def snapshot(self, request, slug=None):
        wc = self.get_object()
        try:
            ss = wc.create_snap(json.loads(request.body))
            if ss:
                return JsonResponse({"result": "success", "webcam_id": wc.slug, "img_id": ss.id}, status=201)
        except ValueError:
            pass
        return HttpResponseBadRequest()

    @detail_route(methods=['get'])
    def scheduled(self, request, slug=None):
        wc = self.get_object()
        return HttpResponse(status=200 if wc and wc.is_scheduled() else 404)


class SnapshotViewSet(viewsets.ModelViewSet):
    serializer_class = SnapshotSerializer
    queryset = Snapshot.objects.all()

    def get_queryset(self):
        return super(SnapshotViewSet, self).get_queryset()
