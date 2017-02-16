import json
import os
import logging
from datetime import datetime
from shutil import copyfile

from django.contrib.auth.models import User, Group
from django.http.response import JsonResponse, HttpResponseBadRequest, HttpResponse
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import detail_route

from conf import settings
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
        except ValueError, e:
            return HttpResponseBadRequest(reason=e.message)


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
                self.make_latest(ss)
                return JsonResponse(SnapshotSerializer(instance=ss, context={'request': request}).data, status=201)    #{"result": "success", "webcam_id": wc.slug, "img_id": ss.id}
        except ValueError:
            pass
        return HttpResponseBadRequest()

    @detail_route(methods=['get'])
    def scheduled(self, request, slug=None):
        wc = self.get_object()
        return HttpResponse(status=200 if wc and wc.is_scheduled() else 404)

    @detail_route(methods=['get'])
    def snaps(self, request, slug=None):
        wc = self.get_object()
        tz = timezone.get_current_timezone()
        ct = timezone.make_aware(datetime.now(), tz)
        cnt = False
        try:
            y = int(request.query_params.get('y', ct.year))
            m = int(request.query_params.get('m', ct.month))
            d = int(request.query_params.get('d', ct.day))
            h = int(request.query_params.get('h', -1))
            cnt = len(request.query_params.get('count', '')) > 0

            if h >= 0:
                sd = timezone.make_aware(datetime(y, m, d, h, 0, 0),tz)
                ed = timezone.make_aware(datetime(y, m, d, h, 59, 59),tz)
            else:
                sd = timezone.make_aware(datetime(y, m, d, 0, 0, 0),tz)
                ed = timezone.make_aware(datetime(y, m, d, 23, 59, 59),tz)
            if cnt:
                return JsonResponse(data={'count': wc.snapshot_set.filter(ts_create__range=(sd,ed)).count()})
            return JsonResponse(data=SnapshotSerializer(wc.snapshot_set.filter(ts_create__range=(sd,ed)), many=True, context={'request': request}).data, safe=False)
        except ValueError, e:
            return HttpResponseBadRequest(reason=e.message)

    def make_latest(self, ss):
        ss = Snapshot()
        sfnm = ss.img_name
        sdir = os.path.join(settings.WEBCAM_IMAGE_PATH, ss.img_path)
        src = os.path.join(sdir, sfnm)
        dfnm = 'latest.jpg'
        ddir = settings.WEBCAM_IMAGE_PATH
        dst = os.path.join(ddir, dfnm)
        copyfile(src, dst)
        logger.debug('make_latest: copied %s to %s' % (src, dst))


class SnapshotViewSet(viewsets.ModelViewSet):
    serializer_class = SnapshotSerializer
    queryset = Snapshot.objects.all()

    def get_queryset(self):
        return super(SnapshotViewSet, self).get_queryset()
