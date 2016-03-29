from __future__ import unicode_literals

import json

import markdown
from django.db import models
from django.db.models import CharField, TextField, DecimalField, ForeignKey, DateTimeField
from django.utils import timezone
from django.utils.text import slugify
from datetime import datetime

from conf import settings

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

    # def can_consume(self):
    #     sch = self.get_schedule()
    #     if sch is None:
    #         return settings.NO_SCHEDULE_MEANS_ON
    #     tz = timezone.get_current_timezone()
    #     now = datetime.now(tz)
    #     st = timezone.make_aware(datetime(now.year, now.month, now.day, 0, 0, 0), tz)
    #     sp = timezone.make_aware(datetime(now.year, now.month, now.day, 23, 59, 59), tz)
    #     return (now >= st) and (now <= sp)

    def get_schedule(self):
        if self.schedule is None or len(self.schedule) == 0:
            return None
        return json.loads(self.schedule)

    def is_scheduled(self):
        sch = self.get_schedule()
        if sch is None:
            return settings.NO_SCHEDULE_MEANS_ON
        tz = timezone.get_current_timezone()
        now = datetime.now(tz)
        dsch = sch.get('all', None)
        if dsch is None:
            dow = now.strftime('%a').lower()
            dsch = sch.get(dow, None)
        if dsch is None:
            return settings.NO_SCHEDULE_MEANS_ON
        o = dsch.get('off', None)
        if o:
            for tms in o:
                st = datetime.strptime(tms['start'], "%H:%M:%S")
                et = datetime.strptime(tms['stop'], "%H:%M:%S")
                sd = datetime(now.year, now.month, now.day, st.hour, st.minute, st.second, tzinfo=tz)
                ed = datetime(now.year, now.month, now.day, et.hour, et.minute, et.second, tzinfo=tz)
                if (now >= sd) and (now <= ed):     # self.time_in_range(now, tz, st, et):
                    return False
        o = dsch.get('on', None)
        if o is None:
            return settings.NO_SCHEDULE_MEANS_ON
        for tms in o:
            st = datetime.strptime(tms['start'], "%H:%M:%S")
            et = datetime.strptime(tms['stop'], "%H:%M:%S")
            sd = datetime(now.year, now.month, now.day, st.hour, st.minute, st.second, tzinfo=tz)
            ed = datetime(now.year, now.month, now.day, et.hour, et.minute, et.second, tzinfo=tz)
            if (now >= sd) and (now <= ed):         # self.time_in_range(now, tz, st, et)
                return True
        return False

    def months(self, yr=None):
        if yr is None:
            return self.snapshot_set.all().datetimes('ts_create', 'month')
        tz = timezone.get_current_timezone()
        now = datetime.now(tz)
        sd = datetime(now.year, now.month, now.day, tzinfo=tz)
        ed = datetime(now.year, now.month, now.day, tzinfo=tz)
        return self.snapshot_set.filter(ts_create__range=(sd,ed)).datetimes('ts_create', 'month')

    def years(self):
        return self.snapshot_set.all().datetimes('ts_create', 'year')

    def snaps_for_day(self, dt):
        tz = timezone.get_current_timezone()
        sd = datetime(dt.year, dt.month, dt.day, 0, 0, 0, tzinfo=tz)
        ed = datetime(dt.year, dt.month, dt.day, 23, 59, 59, tzinfo=tz)
        return self.snapshot_set.filter(ts_create__range=(sd,ed))

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

    # def time_in_range(self, now, tz, st, et):
    #     sd = timezone.make_aware(datetime(now.year, now.month, now.day, st.hour, st.minute, st.second), tz)
    #     ed = timezone.make_aware(datetime(now.year, now.month, now.day, et.hour, et.minute, et.second), tz)
    #     return (now >= sd) and (now <= ed)


class Snapshot(models.Model):
    webcam = ForeignKey(Webcam)
    ts_create = DateTimeField(auto_created=True, auto_now_add=True)
    img_name = CharField(max_length=255, blank=True, null=True)
    img_path = CharField(max_length=1024, blank=True, null=True)

    def __unicode__(self):
        return '%s from %s' % (self.img_name, self.webcam.name)

    def get_absolute_url(self):
        return ''


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
