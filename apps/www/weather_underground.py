import json
import urllib2
import time
from datetime import datetime
from django.utils import timezone

WUKEY_CURRENT_OBS = 'current_observation'
WUKEY_STATION_ID = 'station_id'
WUKEY_WEATHER = 'weather'
WUKEY_TEMP = 'temp_f'
WUKEY_REL_HUMID = 'relative_humidity'
WUKEY_WIND_DIR = 'wind_degrees'
WUKEY_WIND_MPH = 'wind_mph'
WUKEY_GUST_MPH = 'wind_gust_mph'
WUKEY_BAROM = 'pressure_in'
WUKEY_BAROM_TREND = 'pressure_trend'
WUKEY_DEWPOINT = 'dewpoint_f'
WUKEY_PRECIP_1H = 'precip_1hr_in'
WUKEY_PRECIP_1D = 'precip_today_in'
WUKEY_OBS_TIME = 'observation_time_rfc822'
WUKEY_LOCAL_TZ = 'local_tz_short'

WUKEY_OBS_EPOCH = 'observation_epoch'
WUKEY_LOCAL_EPOCH = 'local_epoch'

WUKEY_MOON = 'moon_phase'
WUKEY_SUN = 'sun_phase'
WUKEY_MOON_AGE = 'ageOfMoon'
WUKEY_MOON_PHASE = 'phaseofMoon'
WUKEY_MOON_HEMI = 'hemisphere'
WUKEY_MOON_PCT = 'percentIlluminated'
WUKEY_SUNRISE = 'sunrise'
WUKEY_SUNSET = 'sunset'
WUKEY_MINUTE = 'minute'
WUKEY_HOUR = 'hour'

WU_OBS_TIME_PATTERN = '%a, %d %b %Y %H:%M:%S'

class WeatherUnderground(object):
    _BASE_URL = 'http://api.wunderground.com/api'

    def __init__(self, api_key):
        self._api_key = api_key

    def _get_feature(self, feature, query):
        if self._api_key is None:
            raise RuntimeError('provide an api key')
        u = '%s/%s/%s/q/%s.json' % (self._BASE_URL, self._api_key, feature, query)
        f = urllib2.urlopen(u)
        js = f.read()
        rv = json.loads(js)
        f.close()
        return rv

    def get_astronomy(self, query):
        return self._get_feature('astronomy', query)

    def get_conditions(self, query):
        return self._get_feature('conditions', query)

    def get_forecast(self, query):
        return self._get_feature('forecast', query)

    def parse_time(self, jt):
        if WUKEY_MINUTE in jt and WUKEY_HOUR in jt:
            m = jt[WUKEY_MINUTE]
            h = jt[WUKEY_HOUR]
            return datetime.strptime('%s:%s' % (h, m), '%H:%M')
        return None

    def parse_datetime(self, tmstr, local_tz):
    #Tue, 31 Mar 2015 15:39:52 -0700
        # if len(tmstr) < 25:
        #     return None
        # s = '%s %s' % (tmstr[:25],  local_tz)
        s = tmstr[:25]
        return datetime.strptime(s, WU_OBS_TIME_PATTERN)

    def from_epoch(self, epoch):
        t = time.localtime(epoch)
        #tz = timezone.get_current_timezone()
        return datetime(t.tm_year, t.tm_mon, t.tm_mday, t.tm_hour, t.tm_min, t.tm_sec)