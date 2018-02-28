import glob
import os
import random
from datetime import datetime, timedelta

import logging
from django.utils import timezone

from .models import WuAstronomy, Webcam, TempHumidity, SnapshotDailyStat
from .weather_underground import *
from conf import settings

logger = logging.getLogger(__name__)


class ImageManager(object):

    _image_names = None

    def __init__(self):
        self._image_names = []

    def add_image(self, nm):
        self._image_names.append(nm)

    def get_random_image(self):
        if self._image_names is None or len(self._image_names) == 0:
            return None
        n = len(self._image_names)
        i = random.randint(0, 50000) % n
        return self._image_names[i]

    @property
    def image_count(self):
        if self._image_names is None:
            return 0
        return len(self._image_names)


class FileBasedImageManager(ImageManager):

    def __init__(self, src_path, mask):
        super(FileBasedImageManager, self).__init__()
        self.load_from(src_path, mask)

    def load_from(self, src_path, mask):
        s = os.path.join(src_path, mask)
        lst = glob.glob(s)
        for f in lst:
            self.add_image(os.path.basename(f))


DEF_QUERY = '91916'     #'KSAN'
DATE_KEY_FORMAT = '%Y%m%d'


def do_daily(query=None):
    if query is None:
        query = DEF_QUERY
    tz = timezone.get_current_timezone()
    cur_tm = timezone.make_aware(datetime.now(), tz)
    key = cur_tm.strftime(DATE_KEY_FORMAT)
    try:
        pa = WuAstronomy.objects.get(date_key=key)
    except WuAstronomy.DoesNotExist:
        pa = None
    if pa is None:
        wu = WeatherUnderground(settings.WU_API_KEY)
        a = wu.get_astronomy(query)
        try:
            moon = a.get(WUKEY_MOON, None)
            sun = a.get(WUKEY_SUN, None)
            pa = WuAstronomy()
            pa.reading_time = cur_tm
            pa.date_key = key
            pa.moon_age = moon[WUKEY_MOON_AGE] or 0
            pa.moon_phase = moon[WUKEY_MOON_PHASE] or ''
            pa.moon_hemi = moon[WUKEY_MOON_HEMI] or ''
            pa.moon_pct = moon[WUKEY_MOON_PCT] or 0
            t = wu.parse_time(moon[WUKEY_SUNRISE])
            if t is not None:
                pa.moon_rise = t
            t = wu.parse_time(moon[WUKEY_SUNSET])
            if t is not None:
                pa.moon_set = t
            t = wu.parse_time(sun[WUKEY_SUNRISE])
            if t is not None:
                pa.sun_rise = t
            t = wu.parse_time(sun[WUKEY_SUNSET])
            if t is not None:
                pa.sun_set = t
            pa.save()
        except KeyError:
            pass
    return pa


def update_schedule():
    pa = do_daily()
    if pa is None:
        return
    tz = timezone.get_current_timezone()
    cur_tm = timezone.make_aware(datetime.now(), tz)
    try:
        wc = Webcam.objects.get(pk=1)
    except:
        return
    on = []
    pad = timedelta(seconds=1800)
    pad2 = timedelta(seconds=2700)
    sr = pa.sun_rise
    FMT = "%H:%M:%S"
    st = timezone.make_aware(datetime(cur_tm.year, cur_tm.month, cur_tm.day, sr.hour, sr.minute, sr.second, 0),tz) - pad
    et = timezone.make_aware(datetime(cur_tm.year, cur_tm.month, cur_tm.day, sr.hour, sr.minute, sr.second, 0), tz) + pad2
    on.append({'start': '%s' % st.strftime(FMT), 'stop': '%s' % et.strftime(FMT)})
    ss = pa.sun_set
    st = timezone.make_aware(datetime(cur_tm.year, cur_tm.month, cur_tm.day, ss.hour, ss.minute, ss.second, 0),tz) - pad2
    et = timezone.make_aware(datetime(cur_tm.year, cur_tm.month, cur_tm.day, ss.hour, ss.minute, ss.second, 0), tz) + pad
    on.append({'start': '%s' % st.strftime(FMT), 'stop': '%s' % et.strftime(FMT)})
    sch = {
        'all': {
            'on': on
        }
    }
    wc.schedule = json.dumps(sch)
    wc.save()
    return '%s: %s' % (wc, wc.schedule)


def first_day_before(dt, dow):
    tz = timezone.get_current_timezone()
    rv = timezone.make_aware(datetime(dt.year, dt.month, dt.day), tz)
    dlt = timedelta(days=1)
    while rv.weekday() != dow:
        rv = rv - dlt
    return rv


def last_day_after(dt, dow):
    tz = timezone.get_current_timezone()
    rv = timezone.make_aware(datetime(dt.year, dt.month, dt.day), tz)
    dlt = timedelta(days=1)
    while rv.weekday() != dow:
        rv = rv + dlt
    return rv


def last_day_of_month(dt):
    tz = timezone.get_current_timezone()
    rv = timezone.make_aware(datetime(dt.year, dt.month, 28), tz)
    dlt = timedelta(days=1)
    while dt.month == rv.month:
        rv = timezone.make_aware(datetime(dt.year, dt.month, dt.day), tz)
        dt = dt + dlt
    return rv


def update_stats():
    dates = TempHumidity.objects.datetimes('reading_time', 'day')
    for dte in dates:
        pass


def update_daily_stats(wc_id=1, dte=None):
    try:
        wc = Webcam.objects.get(pk=wc_id)
    except Webcam.DoesNotExist:
        logger.warning('no webcam found for: %d' % wc_id)
        return None
    if dte is None:
        dte = datetime.now()
    tz = timezone.get_current_timezone()
    for_date = timezone.make_aware(datetime(year=dte.year, month=dte.month, day=dte.day), tz)
    logger.debug('lookup snapshot: %s %s' % (wc, for_date))
    ds = SnapshotDailyStat.lookup(webcam=wc, for_date=for_date)
    if ds is None:
        ds = SnapshotDailyStat.objects.create(webcam=wc, for_date=for_date)
    logger.debug('updating snapshot: %s' % ds)
    snaps = wc.snaps_for_day(for_date)
    cnt = snaps.count() if snaps else 0
    am = None
    pm = None
    chg = False
    noon = timezone.make_aware(datetime(for_date.year, for_date.month, for_date.day, 12, 0, 0), tz)
    if cnt > 0:
        am = snaps.filter(ts_create__lt=noon)
        pm = snaps.filter(ts_create__gt=noon)
    if am and am.count() > 0:
        chg = True
        ds.am_count = am.count()
        ds.am_start = am.earliest('ts_create').ts_create
        ds.am_end = am.latest('ts_create').ts_create
    if pm and pm.count() > 0:
        chg = True
        ds.pm_count = pm.count()
        ds.pm_start = pm.earliest('ts_create').ts_create
        ds.pm_end = pm.latest('ts_create').ts_create
    if chg:
        ds.save()
    logger.debug('snapshot update complete: %s' % ds)
    return ds
