
import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import login, logout
from django.core.urlresolvers import reverse
from django.http import JsonResponse, HttpResponse, HttpResponseBadRequest
from django.db.models import Avg, Min, Max

# Create your views here.
from vanilla import ListView, DetailView, UpdateView, CreateView
from vanilla.views import TemplateView

from .models import BlogEntry, TempHumidity, Station
from .forms import BlogEntryForm
from .util import *

logger = logging.getLogger(__name__)


def wrapped_login(request):
#    ctx = _build_context(request, 'Login')
    ctx = {}
    ctx['page_title'] = 'Login'
#    cart = get_cart(request, False)
    referer = request.META.get('HTTP_REFERER', None)
    if referer:
        if "/login" in referer or '/logout' in referer:
            pass
        else:
            ctx['next'] = referer
    new_cust=request.GET.get('new_cust', None)
    if new_cust:
        messages.info(request, 'Welcome %s, thanks for registering!' % (new_cust))
    resp = login(request, extra_context=ctx)
#    if request.method == 'POST' and hasattr(request, 'user') and request.user.is_authenticated():
#        u = request.user
#        if cart:
#            cart.user = u
#            cart.save()
#            request.session['cart_id'] = cart.id
#        cust = get_customer_from_user(u)
#        if cust:
#            request.session['cust_id'] = cust.id
#        site = get_site(request)
#        if site:
#            LoggedInUser.objects.filter(username=u.username, site=site).delete()
#        else:
#            LoggedInUser.objects.filter(username=u.username).delete()
#        lu = LoggedInUser()
#        lu.username = u.username
##        lu.login_time = datetime.datetime.now()
#        if site:
#            lu.site = site
#        lu.save()
    return resp


def wrapped_logout(request):
    ctx = {}
    ctx['page_title'] = 'Logged Out'
    resp = logout(request, extra_context=ctx)
    return resp

#    return logout(request, next_page=reverse('home'))

#        site = get_site(request)
#        if site:
#            LoggedInUser.objects.filter(username=request.user.username, site=site).delete()
#        else:
#            LoggedInUser.objects.filter(username=request.user.username).delete()


class LoginRequiredMixin(object):

    @classmethod
    def as_view(cls):
        return login_required(super(LoginRequiredMixin, cls).as_view())


class WebsiteView(TemplateView):

    def get_page_title(self):
        return 'untitled'

    def get_context_data(self, **kwargs):
        rv = super(WebsiteView, self).get_context_data(**kwargs)
        rv['page_title'] = self.get_page_title()
        return rv


class HomeView(WebsiteView):

    template_name = 'www/home.html'
    start_date = datetime.strptime('2016-01-15', '%Y-%m-%d')
    # on_date = datetime.strptime('2016-01-15', '%Y-%m-%d')
    def get_context_data(self, **kwargs):
        rv = super(HomeView, self).get_context_data(**kwargs)
        dlt = datetime.now() - self.start_date
        rv['start_date'] = self.start_date
        rv['onboard'] = dlt.days > 0
        rv['days_aboard'] = abs(dlt.days)

        return rv

    def get_page_title(self):
        return 'Captains Blog'


class BlogView(ListView):

    template_name = 'www/blog_list.html'
    context_object_name = 'blog_entries'
    start_date = datetime.strptime('2016-01-15', '%Y-%m-%d')

    def get_context_data(self, **kwargs):
        rv = super(BlogView, self).get_context_data(**kwargs)
        dlt = datetime.now() - self.start_date
        rv['start_date'] = self.start_date
        rv['onboard'] = dlt.days > 0
        rv['days_aboard'] = abs(dlt.days)
        rv['page_title'] = 'Captains Log'
        # rv['STATIC_URL'] = settings.STATIC_URL
        try:
            r = BlogEntry.objects.order_by('-create_time')[0]
        except IndexError:
            r = None
        rv['recent_entry'] = r
        return rv

    def get_queryset(self):
        return BlogEntry.objects.order_by('-create_time')


class BlogDetailView(DetailView):

    template_name = 'www/blog_detail.html'
    context_object_name = 'entry'
    model = BlogEntry
    lookup_field = 'slug'

    def get_context_data(self, **kwargs):
        rv = super(BlogDetailView, self).get_context_data(**kwargs)
        fbim = FileBasedImageManager(settings.IMAGE_DIR, '*.jpg')
        # now = datetime.now()
        rv['random_img'] = fbim.get_random_image()
        # rv['STATIC_URL'] = settings.STATIC_URL
        nxt = None
        prv = None
        if self.object:
            rv['page_title'] = self.object.title
            dte = self.object.create_time
            try:
                prv = BlogEntry.objects.filter(create_time__gt=dte).order_by('create_time')[0]
            except IndexError:
                prv = None
            try:
                nxt = BlogEntry.objects.filter(create_time__lt=dte).order_by('-create_time')[0]
            except IndexError:
                nxt = None
        rv['prev_entry'] = prv
        rv['next_entry'] = nxt
        return rv


class BlogEditView(LoginRequiredMixin, UpdateView):

    template_name = 'www/blog_edit.html'
    context_object_name = 'entry'
    model = BlogEntry
    form_class = BlogEntryForm
    lookup_field = 'slug'

    def get_context_data(self, **kwargs):
        rv = super(BlogEditView, self).get_context_data(**kwargs)
        if rv is None:
            rv = {}
        # imgs = []
        # for i in range(1, 11):
        #     imgs.append('new_boat_%s.jpg' % i)
        # now = datetime.now()
        # rv['random_img'] = imgs[now.second % 10]
        # nxt = None
        # prv = None
        # if self.object:
        #     rv['page_title'] = 'Edit: %s' % self.object.title
        #     dte = self.object.modify_time
        #     try:
        #         prv = BlogEntry.objects.filter(modify_time__gt=dte).order_by('modify_time')[0]
        #     except IndexError:
        #         prv = None
        #     try:
        #         nxt = BlogEntry.objects.filter(modify_time__lt=dte).order_by('-modify_time')[0]
        #     except IndexError:
        #         nxt = None
        # rv['prev_entry'] = prv
        # rv['next_entry'] = nxt
        return rv

    def get_success_url(self):
        return reverse('home')


class BlogCreateView(LoginRequiredMixin, CreateView):

    template_name = 'www/blog_edit.html'
    context_object_name = 'entry'
    model = BlogEntry
    form_class = BlogEntryForm
    lookup_field = 'slug'

    def get_context_data(self, **kwargs):
        rv = super(BlogCreateView, self).get_context_data(**kwargs)
        if rv is None:
            rv = {}
        rv['page_title'] = 'New Entry'
        return rv

    def get_success_url(self):
        return reverse('home')


class VisitorsView(WebsiteView):

    template_name = 'www/visitors.html'

    def get_page_title(self):
        return 'Visitors'


class PhotosView(WebsiteView):

    template_name = 'www/photos.html'

    def get_page_title(self):
        return 'Photos'


class WeatherView(WebsiteView):

    template_name = 'www/weather.html'
    stations = None

    def get_page_title(self):
        return 'San Diego Weather'

    def get_context_data(self, **kwargs):
        rv = super(WeatherView, self).get_context_data(**kwargs)
        if rv is None:
            rv = {}
        rv['stations'] = ['station-01']
        rv['auto_refresh'] = True
        rv['auto_refresh_secs'] = 300
        return rv


class BoatCamView(WebsiteView):

    template_name = 'www/boat_cam.html'

    def get_page_title(self):
        return 'Boat Cam!'

    def get_context_data(self, **kwargs):
        rv = super(BoatCamView, self).get_context_data(**kwargs)
        if rv is None:
            rv = {}
        try:
            wc = Webcam.objects.get(pk=1)
            rv['last_image'] = wc.snapshot_set.latest('ts_create')
        except Webcam.DoesNotExist:
            pass
        rv['auto_refresh'] = True
        rv['auto_refresh_secs'] = 60
        return rv


class WebcamView(DetailView):

    template_name = 'www/wc.html'
    context_object_name = 'webcam'
    lookup_field = 'slug'
    lookup_url_kwarg = 'slug'
    model = Webcam

    def get_context_data(self, **kwargs):
        rv = super(WebcamView, self).get_context_data(**kwargs)
        schOn = []
        schOff = []
        mths = None
        cnt = 0
        if self.object:
            mths = self.object.snapshot_set.datetimes('ts_create', 'month', order='DESC')
            cnt = self.object.snapshot_set.count()
            rv['page_title'] = self.object.name
            if len(self.object.schedule) > 0:
                try:
                    sch = json.loads(self.object.schedule)
                    if sch:
                        all = sch.get('all', None)
                        if all:
                            schOn = all.get('on', None)
                            schOff = all.get('off', None)
                except ValueError:
                    pass
        tz = timezone.get_current_timezone()
        ct = timezone.make_aware(datetime.now(), tz)
        rv['now'] = ct
        # rv['all_days'] = allD
        rv['scheduled_on'] = schOn
        rv['scheduled_off'] = schOff
        rv['months'] = mths
        rv['total_snaps'] = cnt
        return rv


class WcMonthView(DetailView):

    template_name = 'www/wc.html'
    context_object_name = 'webcam'
    lookup_field = 'slug'
    lookup_url_kwarg = 'slug'
    model = Webcam

    def get_context_data(self, **kwargs):
        rv = super(WcMonthView, self).get_context_data(**kwargs)
        y = int(self.kwargs['year'])
        m = int(self.kwargs['month'])
        tz = timezone.get_current_timezone()
        dom1 = timezone.make_aware(datetime(y, m, 1), tz)
        tday = timezone.make_aware(datetime.now(), tz)
        dlt = timedelta(days=1)
        firstD = first_day_before(dom1, 6)
        lastD = last_day_after(last_day_of_month(dom1), 5)
        curD = firstD
        allD = []
        schOn = []
        schOff = []
        fst = None
        lst = None
        ar_secs = 0
        if self.object:
            if y == tday.year and m == tday.month and self.object.is_scheduled():
                update_daily_stats(self.object.id, tday)
                ar_secs = 60
            rv['page_title'] = '%s - %s' % (self.object.name, dom1.strftime('%b %Y'))
            if len(self.object.schedule) > 0:
                sch = json.loads(self.object.schedule)
                if sch:
                    all = sch.get('all', None)
                    if all:
                        schOn = all.get('on', None)
                        schOff = all.get('off', None)
            ndx = 0
            while curD <= lastD:
                stats = SnapshotDailyStat.lookup(webcam=self.object, for_date=curD)
                # if stats is None:
                #     stats = update_daily_stats(self.object.id, curD)
                allD.append({'index': ndx, 'day': curD, 'count': 0 if stats is None else stats.total_count, 'stats': stats})
                curD += dlt
                ndx += 1
            if len(self.object.schedule) > 0:
                sch = json.loads(self.object.schedule)
                if sch:
                    all = sch.get('all', None)
                    if all:
                        schOn = all.get('on', None)
                        schOff = all.get('off', None)
            fst = self.object.snapshot_set.earliest('ts_create')
            lst = self.object.snapshot_set.latest('ts_create')

        pm = firstD - dlt
        if fst and pm >= fst:
            rv['prev_month'] = pm
        nm = last_day_of_month(dom1) + dlt
        if nm <= tday:
            rv['next_month'] = nm
        # rv['first_day'] = firstD
        # rv['last_day'] = lastD
        rv['cur_month'] = dom1
        rv['now'] = tday
        rv['all_days'] = allD
        rv['latest_snap'] = lst
        rv['first_day'] = None if fst is None else fst.ts_create
        rv['last_day'] = None if lst is None else lst.ts_create
        rv['scheduled_on'] = schOn
        rv['scheduled_off'] = schOff
        if ar_secs > 0:
            rv['auto_refresh'] = True
            rv['auto_refresh_secs'] = ar_secs
        return rv


class WcDayView(TemplateView):
    template_name = 'www/wc_day.html'

    def get_context_data(self, **kwargs):
        rv = super(WcDayView, self).get_context_data(**kwargs)
        try:
            wc = Webcam.objects.get(slug=self.kwargs['slug'])
        except Webcam.DoesNotExist:
            wc = None
        y = int(self.kwargs['year'])
        m = int(self.kwargs['month'])
        d = int(self.kwargs['day'])
        tz = timezone.get_current_timezone()
        curD = datetime(y, m, d)
        sfd = None
        if wc:
            sfd = wc.snaps_for_day(curD)
        cnt = sfd.count() if sfd else 0
        fst = None
        lst = None
        am = None
        pm = None
        amf = None
        aml = None
        pmf = None
        pml = None
        noon = datetime(curD.year, curD.month, curD.day, 12, 0, 0)
        if cnt > 0:
            fst = sfd.earliest('ts_create')
            lst = sfd.latest('ts_create')
            am = sfd.filter(ts_create__lt=noon)
            pm = sfd.filter(ts_create__gt=noon)
        if am and am.count() > 0:
            amf = am.earliest('ts_create')
            aml = am.latest('ts_create')
        if pm and pm.count() > 0:
            pmf = pm.earliest('ts_create')
            pml = pm.latest('ts_create')
        rv.update({'webcam': wc,
                    'day': curD,
                    'count': cnt,
                    'earliest': fst,
                    'latest': lst,
                    'am': am,
                    'pm': pm,
                    'aml': aml,
                    'amf': amf,
                    'pmf': pmf,
                    'pml': pml})
        return rv


class AdilHomeView(WebsiteView):

    template_name = 'www/adil_home.html'
    webcam = None

    def get_page_title(self):
        return 'A Day in Pictures'

    def get_context_data(self, **kwargs):
        rv = super(AdilHomeView, self).get_context_data(**kwargs)
        tz = timezone.get_current_timezone()
        ct = datetime.now(tz)
        dlt = timedelta(days=1)
        firstD = first_day_before(datetime(ct.year, ct.month, 1, tzinfo=tz), 6)
        lastD = last_day_after(last_day_of_month(ct), 5)
        curD = firstD
        allD = []
        self.webcam = None
        try:
            self.webcam = Webcam.objects.get(pk=1)
            while curD <= lastD:
                sfd = self.webcam.snaps_for_day(curD)
                cnt = sfd.count()
                fst = None
                lst = None
                if cnt > 0:
                    fst = sfd.earliest('ts_create')
                    lst = sfd.latest('ts_create')
                allD.append({'day': curD, 'count': cnt, 'earliest': fst, 'latest': lst })
                curD = curD + dlt
        except Webcam.DoesNotExist:
            pass
        rv['webcam'] = self.webcam
        rv['first_day'] = firstD
        rv['last_day'] = lastD
        rv['now'] = ct
        rv['all_days'] = allD
        return rv


class DayInTheLifeView(WebsiteView):

    template_name = 'www/adil.html'
    webcam = None

    def get_context_data(self, **kwargs):
        rv = super(DayInTheLifeView, self).get_context_data(**kwargs)
        tz = timezone.get_current_timezone()
        cslug = self.kwargs['slug']
        y = int(self.kwargs['year'])
        m = int(self.kwargs['month'])
        d = int(self.kwargs['day'])
        td = timezone.make_aware(datetime.now(), tz)
        wdate = timezone.make_aware(datetime(y, m, d),tz)
        dlt = timedelta(days=1)
        pdate = wdate - dlt
        ndate = wdate + dlt
        self.webcam = None
        try:
            self.webcam =  Webcam.objects.get(slug=cslug)
            rv['webcam'] = self.webcam
            rv['all_dates'] = None if self.webcam is None else self.webcam.snapshot_set.all().datetimes('ts_create', 'day')
            rv['which_date'] = wdate
            rv['prev_date'] = pdate
            if ndate < td:
                rv['next_date'] = ndate
            rv['snaps_by_hour'] = self._build_sbh(y, m, d)
            rv['page_title'] = '%s %s' % (self.webcam.name, wdate.strftime("%b %d, %Y"))
        except Webcam.DoesNotExist:
            pass
        return rv

    def _build_sbh(self, y, m, d):
        sbh = []
        for i in range(0,24):
            hr = datetime(y, m, d, i, 0)
            snaps = self.webcam.snaps_for_hour(y, m, d, i)
            sbh.append({"hour": hr, "snaps": snaps})
        return sbh


class AdilHourView(TemplateView):

    template_name = 'www/adil_hour.html'

    def get_context_data(self, **kwargs):
        rv = super(AdilHourView, self).get_context_data(**kwargs)
        cslug = self.kwargs['slug']
        y = int(self.kwargs['year'])
        m = int(self.kwargs['month'])
        d = int(self.kwargs['day'])
        h = int(self.kwargs['hour'])
        snaps = None
        try:
            wc = Webcam.objects.get(slug=cslug)
            snaps = wc.snaps_for_hour(y, m, d, h)
        except Webcam.DoesNotExist:
            pass
        # rv['STATIC_URL'] = settings.STATIC_URL
        rv['snaps'] = snaps
        return rv


DEF_HOURS = 24


class AjaxChartView(TemplateView):

    template_name = 'n/a'

    def __init__(self):
        super(AjaxChartView, self).__init__()
        self.station = 'station-01'
        # self.kind = None
        # self.names = {"KSAN": "San Diego", "KPHX": "Phoenix", "KOKC": "OKC", "KTEB": "Hackensack"}

    def get_context_data(self, **kwargs):
        rv = super(AjaxChartView, self).get_context_data(**kwargs)
        tz = timezone.get_current_timezone()
        cur_tm = datetime.now(tz)
        dlt = timedelta(hours=DEF_HOURS)
        st_tm = cur_tm - dlt
        try:
            stn = Station.objects.get(name=self.station)
        except Station.DoesNotExist:
            return {}
        rdngs = []
        list = TempHumidity.objects.filter(station=stn).filter(reading_time__gte=st_tm).order_by('reading_time')
        for c in list:
            rt = timezone.localtime(c.reading_time, tz)
            t = c.temperature
            if t:
                if t < -1000:
                    t = 0
                t = float('%.2f' % t)
            h = c.humidity
            if h:
                if h < -1000:
                    h = 0
                h = float('%.2f' % h)
            rdngs.append({'yy': rt.year, 'mm': rt.month-1, 'dd': rt.day, 'hh': rt.hour, 'mi': rt.minute, 'temp': t, 'hum': h})
        return {'name': stn.name, 'readings': rdngs}

    def get(self, request, *args, **kwargs):
        # s = request.GET.get('stations', 'KSAN,KPHX')
        # self.stations = s.split(',')
        self.kind = request.GET.get('kind', 't')
        return super(AjaxChartView, self).get(request, *args, **kwargs)

    def render_to_response(self, context):
        s = json.dumps(context)
        return HttpResponse(s, content_type='application/json')


class HiLoView(TemplateView):

    template_name = 'www/hilo.html'

    def __init__(self):
        super(HiLoView, self).__init__()
        # self.station = 'station-01'
        # self.kind = None
        # self.names = {"KSAN": "San Diego", "KPHX": "Phoenix", "KOKC": "OKC", "KTEB": "Hackensack"}

    def get_context_data(self, **kwargs):
        rv = super(HiLoView, self).get_context_data(**kwargs)
        tz = timezone.get_current_timezone()
        cur_tm = timezone.make_aware(datetime.now())
        sta_nm = self.kwargs['station']
        y = int(self.kwargs['year'])
        m = int(self.kwargs['month'])
        rv['page_title'] = 'Highs and Lows %02d/%d' % (m, y)

        d1 = timezone.make_aware(datetime(y, m, 1), tz)
        firstD = d1
        if d1.weekday() != 6:
            firstD = first_day_before(d1, 6)
        lastD = last_day_after(last_day_of_month(d1), 5)
        days = []
        dlt = lastD - firstD
        for i in range(dlt.days+1):
            dx = firstD + timedelta(days=i)
            days.append(dx)
        ld = last_day_of_month(d1)
        oneDay = timedelta(days=1)
        rv['prev_month'] = d1 - oneDay
        nm = ld + oneDay
        if nm < cur_tm:
            rv['next_month'] = nm
        hilo = []
        try:
            sta = Station.objects.get(name=sta_nm)
        except Station.DoesNotExist:
            sta = None
        if sta:
            rv['station'] = sta
            for d in days:
                # k = '%04d-%02d-%02d' % (y, m,  d)
                # dte = datetime.strptime(k, '%Y-%m-%d')
                st = timezone.make_aware(datetime(d.year, d.month, d.day, 00, 00, 00), tz)
                et = timezone.make_aware(datetime(d.year, d.month, d.day, 23, 59, 59), tz)
                d = {'date': st}
                th = sta.temphumidity_set.filter(reading_time__range=(st,et))
                if th.count() > 0:
                    d.update(th.aggregate(Min('temperature'), Max('temperature'), Avg('temperature')))
                hilo.append(d)
        rv['hilo'] = hilo
        return rv


class CrlsView(TemplateView):
    template_name = 'n/a'

    def get_context_data(self, **kwargs):
        rv = super(CrlsView, self).get_context_data(**kwargs)
        nm = None
        if self.kwargs:
            nm = self.kwargs.get('crlname')
        rv['crlname'] = nm
        return rv

    def render_to_response(self, context):
        context.pop('view')
        return JsonResponse(context)
