import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import login, logout
from django.core.urlresolvers import reverse
from django.http import JsonResponse, HttpResponse, HttpResponseBadRequest

# Create your views here.
from django.views.decorators.csrf import csrf_exempt
from rest_framework.authtoken.models import Token
from vanilla import ListView, DetailView, UpdateView, CreateView
from vanilla.views import TemplateView

from .models import BlogEntry, Snapshot, TempHumidity
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
        tz = timezone.get_current_timezone()
        ct = timezone.make_aware(datetime.now(), tz)
        # dlt = timedelta(days=1)
        # firstD = first_day_before(datetime(ct.year, ct.month, 1, tzinfo=tz), 6)
        # lastD = last_day_after(last_day_of_month(ct), 5)
        # curD = firstD
        # allD = []
        schOn = []
        schOff = []
        if self.object:
            rv['page_title'] = self.object.name
            if len(self.object.schedule) > 0:
                sch = json.loads(self.object.schedule)
                if sch:
                    all = sch.get('all', None)
                    if all:
                        schOn = all.get('on', None)
                        schOff = all.get('off', None)
            # fst = self.object.snapshot_set.earliest('ts_create')
            # lst = self.object.snapshot_set.latest('ts_create')
            # rv['first_day'] = fst.ts_create
            # rv['last_day'] = lst.ts_create
        rv['now'] = ct
        # rv['all_days'] = allD
        rv['scheduled_on'] = schOn
        rv['scheduled_off'] = schOff
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
        ct = timezone.make_aware(datetime(y, m, 1), tz)
        tday = timezone.make_aware(datetime.now(), tz)
        dlt = timedelta(days=1)
        firstD = first_day_before(timezone.make_aware(datetime(y, m, 1), tz), 6)
        lastD = last_day_after(last_day_of_month(ct), 5)
        curD = firstD
        allD = []
        schOn = []
        schOff = []
        if self.object:
            rv['page_title'] = '%s - %s' % (self.object.name, ct.strftime('%b %Y'))
            if len(self.object.schedule) > 0:
                sch = json.loads(self.object.schedule)
                if sch:
                    all = sch.get('all', None)
                    if all:
                        schOn = all.get('on', None)
                        schOff = all.get('off', None)
            while curD <= lastD:
                sfd = self.object.snaps_for_day(curD)
                cnt = sfd.count()
                fst = None
                lst = None
                if cnt > 0:
                    fst = sfd.earliest('ts_create')
                    lst = sfd.latest('ts_create')
                allD.append({'day': curD, 'count': cnt, 'earliest': fst, 'latest': lst })
                curD = curD + dlt
        # rv['webcam'] = self.webcam
        dlt = timedelta(days=1)
        pm = firstD - dlt
        nm = lastD + dlt
        rv['prev_month'] = pm
        if nm < tday:
            rv['next_month'] = nm
        rv['first_day'] = firstD
        rv['last_day'] = lastD
        rv['now'] = ct
        rv['all_days'] = allD

        if self.object:
            if len(self.object.schedule) > 0:
                sch = json.loads(self.object.schedule)
                if sch:
                    all = sch.get('all', None)
                    if all:
                        schOn = all.get('on', None)
                        schOff = all.get('off', None)
            fst = self.object.snapshot_set.earliest('ts_create')
            lst = self.object.snapshot_set.latest('ts_create')
            rv['first_day'] = fst.ts_create
            rv['last_day'] = lst.ts_create
        rv['scheduled_on'] = schOn
        rv['scheduled_off'] = schOff

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

    def get_page_title(self):
        return 'A Day in Pictures'

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
        snaps = None
        try:
            self.webcam =  Webcam.objects.get(slug=cslug)
        except Webcam.DoesNotExist:
            pass
        rv['webcam'] = self.webcam
        rv['all_dates'] = None if self.webcam is None else self.webcam.snapshot_set.all().datetimes('ts_create', 'day')
        rv['which_date'] = wdate
        rv['prev_date'] = pdate
        if ndate < td:
            rv['next_date'] = ndate
        rv['snaps_by_hour'] = self._build_sbh(y, m, d)
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
        # self.stations = None
        self.kind = None
        # self.names = {"KSAN": "San Diego", "KPHX": "Phoenix", "KOKC": "OKC", "KTEB": "Hackensack"}

    def get_context_data(self, **kwargs):
        tz = timezone.get_current_timezone()
        cur_tm = datetime.now(tz)
        dlt = timedelta(hours=DEF_HOURS)
        st_tm = cur_tm - dlt
        sp = None
        data = []
        # for st in self.stations:
        vals = []
        tmps = []
        hums = []
        list = TempHumidity.objects.filter(reading_time__gte=st_tm).order_by('reading_time')
        for c in list:
            # rt = timezone.make_aware(c.reading_time, tz)
            if sp is None:
                sp = c.reading_time
            # v = None
            # if self.kind == 't':
            #     v = c.temperature
            # elif self.kind == 'h':
            #     v = c.humidity
            # elif self.kind == 'b':
            #     v = c.pressure
            # elif self.kind == 'w':
            #     v = c.wind_mph
            # elif self.kind == 'p':
            #     v = c.precip_1h
            v = c.temperature
            if v:
                if v < -1000:
                    v = 0
                tmps.append(float('%.2f' % v))
            v = c.humidity
            if v:
                if v < -1000:
                    v = 0
                hums.append(float('%.2f' % v))
        if sp is None:
            sp = datetime.now()
        sp = timezone.localtime(sp, tz)
        data.append({'name': 'station-01', 'start': {'yy': sp.year, 'mm': sp.month-1, 'dd': sp.day, 'hh': sp.hour, 'mi': sp.minute}, 'temp': tmps, 'hum': hums})
        return {'result': data}

    def get(self, request, *args, **kwargs):
        # s = request.GET.get('stations', 'KSAN,KPHX')
        # self.stations = s.split(',')
        self.kind = request.GET.get('kind', 't')
        return super(AjaxChartView, self).get(request, *args, **kwargs)

    def render_to_response(self, context):
        s = json.dumps(context)
        return HttpResponse(s, content_type='application/json')


@csrf_exempt
def post_img(request, *args, **kwargs):
    if request.method == 'POST':
        logger.debug('post_img')
        slg = kwargs['slug']
        try:
            wc = Webcam.objects.get(slug=slg)
        except Webcam.DoesNotExist:
            logger.debug('webcam not found: %d' % slg)
            return None
        auth = request.META['HTTP_AUTHORIZATION'] or None
        if auth is None or len(auth) < 10:
            return HttpResponseBadRequest()
        try:
            tkn = Token.objects.get(key=auth[6:])
        except Token.DoesNotExist:
            return HttpResponseBadRequest()
        u = tkn.user
        logger.debug('authorized: %s' % u.username)
        d = json.loads(request.body)
        ss = save_image(d, wc)
        if ss:
            return JsonResponse({"result": "success", "user_id": u.id, "img_id": ss.id })
    return HttpResponseBadRequest()


def save_image(d, wc):
    # cid = d['cam_id'] or 0
    # try:
    #     wc = Webcam.objects.get(pk=cid)
    # except Webcam.DoesNotExist:
    #     logger.debug('webcam not found: %d' % cid)
    #     return None
    # if not wc.is_scheduled():
    #     logger.debug('webcam scheduled off right now')
    #     return None
    fnm = d.get('fname', None)
    img = d.get('imgdata', None)
    opts = d.get('img_opts', None)
    if fnm is None or img is None:
        logger.debug('save_image: bad data')
        return None
    tz = timezone.get_current_timezone()
    n = datetime.now(tz)
    dir = os.path.join(settings.WEBCAM_IMAGE_PATH, '%04d' % n.year, '%02d' % n.month, '%02d' % n.day)
    if not os.path.exists(dir):
        os.makedirs(dir)
    path = os.path.join(dir, fnm)
    logger.debug('save_image: %s' % path)
    fout = open(path, "wb")
    fout.write(img.decode("base64"))
    fout.close()
    ss = Snapshot()
    ss.webcam = wc
    ss.img_name = fnm
    ss.img_path = dir[len(settings.WEBCAM_IMAGE_PATH)+1:]
    if opts:
        ss.img_opts = json.dumps(opts)
    ss.save()
    return ss


def api_is_scheduled(request, *args, **kwargs):
    if request.method != 'GET':
        return HttpResponseBadRequest()
    auth = request.META['HTTP_AUTHORIZATION'] or None
    if auth is None or len(auth) < 10:
        return HttpResponseBadRequest()
    try:
        tkn = Token.objects.get(key=auth[6:])
    except Token.DoesNotExist:
        return HttpResponseBadRequest()
    u = tkn.user
    logger.debug('authorized: %s' % u.username)
    slg = kwargs['slug']
    try:
        wc = Webcam.objects.get(slug=slg)
    except Webcam.DoesNotExist:
        logger.debug('webcam not found: %s' % slg)
        wc = None
    return HttpResponse(status=200 if wc and wc.is_scheduled() else 404)


@csrf_exempt
def post_rht(request, *args, **kwargs):
    if request.method == 'POST':
        logger.debug('post_rht')
        auth = request.META['HTTP_AUTHORIZATION'] or None
        if auth is None or len(auth) < 10:
            return HttpResponseBadRequest()
        try:
            tkn = Token.objects.get(key=auth[6:])
        except Token.DoesNotExist:
            return HttpResponseBadRequest()
        u = tkn.user
        logger.debug('authorized: %s' % u.username)
        d = json.loads(request.body)
        rht = save_rht(d)
        if rht:
            return JsonResponse({"result": "success", "user_id": u.id, "rht_id": rht.id })
    return HttpResponseBadRequest()


def save_rht(d):
    if d is None:
        return
    tm = d.get('time', None)
    t = d.get('temp', -999.99)
    h = d.get('humidity', -1.0)
    if tm is None or t == -999.99 or h == -1.0:
        return
    rtm = datetime.strptime(tm, '%Y-%m-%d %H:%M:%S')

    tk = TempHumidity.make_time_key(rtm)
    rht = None
    try:
        rht = TempHumidity.objects.get(time_key=tk)
    except TempHumidity.DoesNotExist:
        rht = None
    if rht is not None:
        return
    rht = TempHumidity()
    rht.time_key = tk
    rht.temperature = t
    rht.humidity = h
    rht.reading_time = timezone.make_aware(rtm, timezone.get_current_timezone())
    rht.save()
    return rht
