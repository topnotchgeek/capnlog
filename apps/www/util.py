import glob
import os
import random
from datetime import datetime, timedelta
from django.utils import timezone

from .models import WuAstronomy, Webcam
from .weather_underground import *
from conf import settings


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


DEF_QUERY = 'KSAN'
DATE_KEY_FORMAT = '%Y%m%d'


def do_daily(query=None):
    if query is None:
        query = DEF_QUERY
    tz = timezone.get_current_timezone()
    cur_tm = datetime.now(tz)
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
            pa.reading_time = timezone.make_naive(cur_tm, tz)
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


def update_schedule():
    do_daily()
    tz = timezone.get_current_timezone()
    cur_tm = datetime.now(tz)
    key = cur_tm.strftime(DATE_KEY_FORMAT)
    try:
        pa = WuAstronomy.objects.get(date_key=key)
    except WuAstronomy.DoesNotExist:
        return
    try:
        wc = Webcam.objects.get(pk=1)
    except:
        return
    sr = pa.sun_rise
    ss = pa.sun_set
    dlt = timedelta(seconds=1800)
    st = datetime(cur_tm.year, cur_tm.month, cur_tm.day, sr.hour, sr.minute, sr.second, 0, tz) - dlt
    et = datetime(cur_tm.year, cur_tm.month, cur_tm.day, ss.hour, ss.minute, ss.second, 0, tz) + dlt
    wc.schedule = '{ "all": {"start" : "%s", "stop": "%s"}}' % (st.strftime("%H:%M:%S"), et.strftime("%H:%M:%S"))
    wc.save()
