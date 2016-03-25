import json
import logging
import os

from datetime import datetime
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, JsonResponse, HttpResponse, HttpResponseBadRequest
from django.shortcuts import render
from django.contrib.auth.views import login, logout

# Create your views here.
from django.views.decorators.csrf import csrf_exempt
from rest_framework.authtoken.models import Token
from vanilla import ListView, DetailView, UpdateView, CreateView
from vanilla.views import TemplateView

from conf import settings

from .models import BlogEntry, Webcam, Snapshot
from .forms import BlogEntryForm
from .util import FileBasedImageManager

logger = logging.getLogger(__name__)


def wrapped_login(request):
#    ctx = _build_context(request, 'Login')
    ctx = {}
    ctx['page_title'] = 'Login'
    ctx['STATIC_URL'] = settings.STATIC_URL
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
    ctx['STATIC_URL'] = settings.STATIC_URL
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
        rv['STATIC_URL'] = settings.STATIC_URL
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
        rv['STATIC_URL'] = settings.STATIC_URL
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
        rv['STATIC_URL'] = settings.STATIC_URL
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
        rv['STATIC_URL'] = settings.STATIC_URL
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
        rv['STATIC_URL'] = settings.STATIC_URL
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

    def get_page_title(self):
        return 'San Diego Weather'


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


class DayInTheLifeView(WebsiteView):

    template_name = 'www/adil.html'
    webcam = None

    def get_page_title(self):
        return 'A Day in the Life'

    def get_context_data(self, **kwargs):
        rv = super(DayInTheLifeView, self).get_context_data(**kwargs)
        y = int(self.kwargs['year'])
        m = int(self.kwargs['month'])
        d = int(self.kwargs['day'])
        snaps = None
        try:
            wc = Webcam.objects.get(pk=1)
            self.webcam = wc
        except Webcam.DoesNotExist:
            pass
        rv['which_date'] = datetime(y, m, d)
        rv['snaps_by_hour'] = self._build_sbh(y, m, d)
        return rv

    def _build_sbh(self, y, m, d):
        sbh = []
        for i in range(0,24):
            hr = datetime(y, m, d, i, 0)
            snaps = self._find_sbh(y, m, d, i)
            sbh.append({"hour": hr, "snaps": snaps})
        return sbh

    def _find_sbh(self, y, m, d, hr):
        dfrom = datetime(y, m, d, hr, 0)
        dto = datetime(y, m, d, hr, 59)
        return self.webcam.snapshot_set.filter(ts_create__range=(dfrom, dto)).order_by('ts_create')

    def get(self, request, *args, **kwargs):
        rv = super(DayInTheLifeView, self).get(request, *args, **kwargs)
        return rv


class AdilHourView(TemplateView):

    template_name = 'www/adil_hour.html'

    def get_context_data(self, **kwargs):
        rv = super(AdilHourView, self).get_context_data(**kwargs)
        y = int(self.kwargs['year'])
        m = int(self.kwargs['month'])
        d = int(self.kwargs['day'])
        h = int(self.kwargs['hour'])
        snaps = None
        try:
            wc = Webcam.objects.get(pk=1)
            dfrom = datetime(y, m, d, h, 0)
            dto = datetime(y, m, d, h, 59)
            snaps = wc.snapshot_set.filter(ts_create__range=(dfrom, dto)).order_by('-ts_create')
        except Webcam.DoesNotExist:
            pass
        rv['STATIC_URL'] = settings.STATIC_URL
        rv['snaps'] = snaps
        return rv


@csrf_exempt
def api_post(request):
    if request.method == 'POST':
        logger.debug('api_post')
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
        ss = save_image(d)
        # d['result'] = "success"
        # d['user_id'] = u.id
        return JsonResponse({"result": "success", "user_id": u.id, "img_id": ss.id })
    return HttpResponseBadRequest()

def save_image(d):
    cid = d['cam_id'] or 0
    try:
        wc = Webcam.objects.get(pk=cid)
    except Webcam.DoesNotExist:
        logger.debug('webcam not found: %d' % cid)
        return
    fnm = d['fname'] or None
    img = d['imgdata'] or None
    if fnm is None or img is None:
        logger.debug('save_image: bad data')
        return
    path = os.path.join(settings.WEBCAM_IMAGE_PATH, fnm)
    logger.debug('save_image: %s' % path)
    fout = open(path, "wb")
    fout.write(img.decode("base64"))
    fout.close()
    ss = Snapshot()
    ss.webcam = wc
    ss.img_name = fnm
    ss.img_path = settings.WEBCAM_IMAGE_PATH
    ss.save()
    return ss