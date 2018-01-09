from __future__ import unicode_literals

import json
import logging
import os

import markdown
from django.db import models
from django.db.models import CharField, TextField, DecimalField, ForeignKey, DateTimeField
from django.utils import timezone
from django.utils.text import slugify
from datetime import datetime

from conf import settings

logger = logging.getLogger(__name__)


# Create your models here.
class Permalinkable(models.Model):

    slug = models.SlugField()

    class Meta:
        abstract = True

    def get_url_kwargs(self, **kwargs):
        kwargs.update(getattr(self, 'url_kwargs', {}))
        return kwargs

    @models.permalink
    def get_absolute_url(self):
        url_kwargs = self.get_url_kwargs(slug=self.slug)
        return (self.url_name, (), url_kwargs)

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if not self.slug:
            s = slugify(self.slug_source)
            if len(s) > 50:
                s = s[:50]
            self.slug = s
        super(Permalinkable, self).save(force_insert=force_insert, force_update=force_update, using=using, update_fields=update_fields)


class Authorable(models.Model):

    class Meta:
        abstract = True

    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='author+')


class Syncable(models.Model):

    class Meta:
        abstract = True

    status = models.SmallIntegerField(default=0, blank=True, null=True)
    flag = models.SmallIntegerField(default=0, blank=True, null=True)


class Htmlable(object):

    def as_html(self):
        src = self.html_source
        if src is None:
            return ''
        md = markdown.Markdown(safe_mode=False)
        return md.convert(src)


class Auditable(models.Model):

    class Meta:
        abstract = True

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='created_by+')
    modified_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='modified_by+')


class Timestampable(models.Model):

    class Meta:
        abstract = True

    create_time = models.DateTimeField(auto_now_add=True)
    modify_time = models.DateTimeField(auto_now=True)

    # def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
    #     self.modify_time = timezone.localtime(datetime.now(), timezone.get_current_timezone())
    #     super(Timestampable, self).save(force_insert=force_insert, force_update=force_update, using=using, update_fields=update_fields)


class BlogEntry(Htmlable, Syncable, Timestampable, Permalinkable, Authorable, models.Model):

    title = models.CharField(max_length=100, blank=False, null=False)
    entry_text = models.TextField(blank=True, null=True)

    def __unicode__(self):
        return u'%s' % self.title

    @property
    def html_source(self):
        return self.entry_text

    @property
    def slug_source(self):
        return self.title

    @property
    def url_name(self):
        return 'blog-detail'


class Webcam(models.Model):
    name = CharField(max_length=100, unique=True)
    description = TextField(blank=True, null=True)
    latitude = DecimalField(max_digits=12, decimal_places=9, default=-999.99)
    longitude = DecimalField(max_digits=12, decimal_places=9, default=-999.99)
    schedule = TextField(blank=True, null=True)
    slug = CharField(max_length=100, unique=True)

    url_name = 'webcam'

    def __unicode__(self):
        return '%s' % self.name

    def get_absolute_url(self):
        return ''

    def get_schedule(self):
        if self.schedule is None or len(self.schedule) == 0:
            return None
        return json.loads(self.schedule)

    def is_scheduled(self):
        sch = self.get_schedule()
        if sch is None:
            return settings.NO_SCHEDULE_MEANS_ON
        now = datetime.now()
        dsch = sch.get('all', None)
        if dsch is None:
            dow = now.strftime('%a').lower()
            dsch = sch.get(dow, None)
        if dsch is None:
            return settings.NO_SCHEDULE_MEANS_ON
        o = dsch.get('off', None)
        if o:
            for tms in o:
                if self.time_in_range(now, tms):
                    return False
        o = dsch.get('on', None)
        if o is None:
            return settings.NO_SCHEDULE_MEANS_ON
        for tms in o:
            if self.time_in_range(now, tms):
                return True
        return False

    def time_in_range(self, now, tms):
        tmfmt = "%H:%M:%S"
        st = datetime.strptime(tms['start'], tmfmt)
        et = datetime.strptime(tms['stop'], tmfmt)
        sd = datetime(now.year, now.month, now.day, st.hour, st.minute, st.second)
        ed = datetime(now.year, now.month, now.day, et.hour, et.minute, et.second)
        return (now >= sd) and (now <= ed)

    def months_with_snaps(self, yr=None):
        if yr is None:
            return self.snapshot_set.all().datetimes('ts_create', 'month')
        tz = timezone.get_current_timezone()
        now = timezone.make_aware(datetime.now(),tz)
        sd = timezone.make_aware(datetime(now.year, now.month, now.day),tz)
        ed = timezone.make_aware(datetime(now.year, now.month, now.day),tz)
        return self.snapshot_set.filter(ts_create__range=(sd,ed)).datetimes('ts_create', 'month')

    def years_with_snaps(self):
        return self.snapshot_set.all().datetimes('ts_create', 'year')

    def snaps_for_day(self, dt):
        tz = timezone.get_current_timezone()
        sd = timezone.make_aware(datetime(dt.year, dt.month, dt.day, 0, 0, 0),tz)
        ed = timezone.make_aware(datetime(dt.year, dt.month, dt.day, 23, 59, 59),tz)
        return self.snapshot_set.filter(ts_create__range=(sd,ed))

    def snaps_for_hour(self, y, m, d, hr):
        tz = timezone.get_current_timezone()
        dfrom = timezone.make_aware(datetime(y, m, d, hr, 0),tz)
        dto = timezone.make_aware(datetime(y, m, d, hr, 59, 59),tz)
        return self.snapshot_set.filter(ts_create__range=(dfrom, dto)).order_by('ts_create')

    def snaps_for_fname(self, fnm):
        return self.snapshot_set.filter(img_name__contains=fnm)

    def get_url_kwargs(self, **kwargs):
        kwargs.update(getattr(self, 'url_kwargs', {}))
        return kwargs

    @models.permalink
    def get_absolute_url(self):
        url_kwargs = self.get_url_kwargs(slug=self.slug)
        return (self.url_name, (), url_kwargs)

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if not self.slug:
            s = slugify(self.slug_source)
            if len(s) > 50:
                s = s[:50]
            self.slug = s
        super(Webcam, self).save(force_insert=force_insert, force_update=force_update, using=using, update_fields=update_fields)

    def create_snap(self, d):
        fnm = d.get('fname', None)
        img = d.get('imgdata', None)
        opts = d.get('img_opts', None)
        if fnm is None or img is None:
            logger.debug('create_snap: bad data')
            return None
        tz = timezone.get_current_timezone()
        n = datetime.now(tz)
        dir = os.path.join(settings.WEBCAM_IMAGE_PATH, '%04d' % n.year, '%02d' % n.month, '%02d' % n.day)
        if not os.path.exists(dir):
            os.makedirs(dir)
        path = os.path.join(dir, fnm)
        # logger.debug('save_image: %s' % path)
        fout = open(path, "wb")
        fout.write(img.decode("base64"))
        fout.close()
        ss = Snapshot()
        ss.webcam = self
        ss.img_name = fnm
        ss.img_path = dir[len(settings.WEBCAM_IMAGE_PATH)+1:]
        if opts:
            ss.img_opts = json.dumps(opts)
        ss.save()
        return ss


class Snapshot(models.Model):
    webcam = ForeignKey(Webcam)
    ts_create = DateTimeField(auto_created=True, auto_now_add=True)
    img_name = CharField(max_length=255, blank=True, null=True)
    img_path = CharField(max_length=1024, blank=True, null=True)
    img_opts = CharField(max_length=1024, blank=True, null=True, default=None)

    def __unicode__(self):
        return '%s from %s' % (self.img_name, self.webcam.name)

    def get_absolute_url(self):
        return ''

    def delete(self, using=None, keep_parents=False):
        fnm = self.img_name if len(self.img_path) == 0 else os.path.join(self.img_path, self.img_name)
        if not fnm.startswith(settings.WEBCAM_IMAGE_PATH):
            fnm = os.path.join(settings.WEBCAM_IMAGE_PATH, fnm)
        if os.path.exists(fnm):
            logger.debug('deleting %s' % fnm)
            os.remove(fnm)
        super(Snapshot, self).delete(using, keep_parents)

    def image_effect(self):
        if self.img_opts:
            j = json.loads(self.img_opts)
            if j.has_key('image_effect'):
                return j['image_effect']
        return ''

    @property
    def image_url(self):
        img = self.img_name if len(self.img_path) == 0 else '%s/%s' % (self.img_path, self.img_name)
        return '%simg/webcam/%s' % (settings.STATIC_URL, img)


class SnapshotDailyStat(models.Model):
    webcam = ForeignKey(Webcam)
    for_date = models.DateField(auto_created=False, auto_now=False, auto_now_add=False)
    am_start = models.DateTimeField(auto_created=False, auto_now=False, auto_now_add=False, blank=True, null=True)
    am_end = models.DateTimeField(auto_created=False, auto_now=False, auto_now_add=False, blank=True, null=True)
    am_count = models.IntegerField(default=0)
    pm_start = models.DateTimeField(auto_created=False, auto_now=False, auto_now_add=False, blank=True, null=True)
    pm_end = models.DateTimeField(auto_created=False, auto_now=False, auto_now_add=False, blank=True, null=True)
    pm_count = models.IntegerField(default=0)

    def __unicode__(self):
        return '%s, %s: %d' % (self.webcam.name, self.for_date, self.total_count)

    @property
    def total_count(self):
        return self.am_count + self.pm_count

    @classmethod
    def lookup(cls, webcam, for_date=None):
        if for_date is None:
            for_date = datetime.now()
        set = SnapshotDailyStat.objects.filter(webcam=webcam).filter(for_date=for_date)
        if set.count() == 1:
            return set.all()[0]
        return None


class WuAstronomy(models.Model):
    status = models.SmallIntegerField(default=0, blank=True, null=True)
    flag = models.SmallIntegerField(default=0, blank=True, null=True)
    reading_time = models.DateTimeField(auto_created=False, auto_now=False, auto_now_add=False)
    date_key = models.CharField(max_length=20, unique=True)

    moon_pct = models.SmallIntegerField(default=-1)
    moon_age = models.SmallIntegerField(default=-1)
    moon_phase = models.CharField(max_length=50, blank=True, null=True)
    moon_hemi = models.CharField(max_length=32, blank=True, null=True)
    moon_rise = models.TimeField(auto_created=False, auto_now=False, auto_now_add=False, blank=True)
    moon_set = models.TimeField(auto_created=False, auto_now=False, auto_now_add=False, blank=True)
    sun_rise = models.TimeField(auto_created=False, auto_now=False, auto_now_add=False, blank=True)
    sun_set = models.TimeField(auto_created=False, auto_now=False, auto_now_add=False, blank=True)

    def _fmt_time(self, val):
        return val.strftime('%H:%M')

    def __unicode__(self):
        return 'sun: %s - %s, moon: %s (%d)' % (self._fmt_time(self.sun_rise), self._fmt_time(self.sun_set), self.moon_phase, self.moon_pct)

    def get_daylength(self):
        if self.sun_rise is None or self.sun_set is None:
            return None
        ssr = '2015-01-01 %02d:%02d' % (self.sun_rise.hour, self.sun_rise.minute)
        sss = '2015-01-01 %02d:%02d' % (self.sun_set.hour, self.sun_set.minute)
        sr = datetime.strptime(ssr, '%Y-%m-%d %H:%M')
        ss = datetime.strptime(sss, '%Y-%m-%d %H:%M')
        dlt = ss - sr
        m = dlt.seconds / 60
        h = m / 60
        m = m % 60
        return '%d hour%s, %d minute%s' % (h, '' if h == 1 else 's', m, '' if m ==1 else 's')

    def compare(self, other):
        if other is None:
            return 0
        ssr = '2015-01-01 %02d:%02d' % (self.sun_rise.hour, self.sun_rise.minute)
        sss = '2015-01-01 %02d:%02d' % (self.sun_set.hour, self.sun_set.minute)
        sr = datetime.strptime(ssr, '%Y-%m-%d %H:%M')
        ss = datetime.strptime(sss, '%Y-%m-%d %H:%M')
        sdlt = ss - sr

        osr = '2015-01-01 %02d:%02d' % (other.sun_rise.hour, other.sun_rise.minute)
        oss = '2015-01-01 %02d:%02d' % (other.sun_set.hour, other.sun_set.minute)
        sr = datetime.strptime(ssr, '%Y-%m-%d %H:%M')
        ss = datetime.strptime(sss, '%Y-%m-%d %H:%M')
        odlt = ss - sr
        return sdlt.seconds - odlt.seconds


class Station(models.Model):
    status = models.SmallIntegerField(default=0, blank=True, null=True)
    flag = models.SmallIntegerField(default=0, blank=True, null=True)
    name = models.CharField(max_length=255, blank=False, null=False, unique=True)

    def __unicode__(self):
        return '%s' % self.name

    def create_reading(self, d):
        if d is None:
            return None
        tm = d.get('time', None)
        t = d.get('temp', -999.99)
        h = d.get('humidity', -1.0)
        if tm is None or t == -999.99 or h == -1.0:
            return None
        rtm = datetime.strptime(tm, '%Y-%m-%d %H:%M:%S')
        tk = TempHumidity.make_time_key(rtm)
        rht = None
        try:
            rht = TempHumidity.objects.get(time_key=tk)
        except TempHumidity.DoesNotExist:
            rht = None
        if rht is not None:
            return None
        rht = TempHumidity()
        rht.station = self
        rht.time_key = tk
        rht.temperature = t
        rht.humidity = h
        rht.reading_time = timezone.make_aware(rtm, timezone.get_current_timezone())
        rht.save()
        return rht


class TempHumidity(models.Model):
    TIME_KEY_FMT = '%Y%m%d_%H%M'

    status = models.SmallIntegerField(default=0, blank=True, null=True)
    flag = models.SmallIntegerField(default=0, blank=True, null=True)
    reading_time = models.DateTimeField(auto_created=False, auto_now=False, auto_now_add=False)
    time_key = models.CharField(max_length=20, unique=True)

    temperature = models.DecimalField(decimal_places=1, max_digits=5, default=0.0, blank=True, null=True)
    humidity = models.DecimalField(decimal_places=1, max_digits=5, default=0.0, blank=True, null=True)
    station = models.ForeignKey(Station)

    # class Meta:
    #     unique_together = ('time_key', 'station')

    def __unicode__(self):
        return '%s - %s %5.1f %5.1f' % ('station-01', self.time_key, self.temperature, self.humidity)

    @classmethod
    def make_time_key(cls, dte):
        return dte.strftime(cls.TIME_KEY_FMT)


class Presence(models.Model):
    status = models.SmallIntegerField(default=0, blank=True, null=True)
    flag = models.SmallIntegerField(default=0, blank=True, null=True)
    reading_time = models.DateTimeField(auto_created=False, auto_now=False, auto_now_add=False)

    user_id = models.CharField(max_length=255)
    device_id = models.CharField(max_length=512)
    latitude = DecimalField(max_digits=12, decimal_places=9, default=-999.99)
    longitude = DecimalField(max_digits=12, decimal_places=9, default=-999.99)

    def __unicode__(self):
        return '%s - %s %12.9f %12.9f' % (self.user_id, self.device_id, self.latitude, self.longitude)


class Sensor(models.Model):
    status = models.SmallIntegerField(default=0, blank=True, null=True)
    flag = models.SmallIntegerField(default=0, blank=True, null=True)
    reading_time = models.DateTimeField(auto_created=False, auto_now=False, auto_now_add=False)
    entity_id = models.CharField(max_length=255, blank=True, null=True)
    value = models.CharField(max_length=255, blank=True, null=True)

    def __unicode__(self):
        return '%s - %s' % (self.entity_id, self.value)
