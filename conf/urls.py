"""capnlog URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.contrib import admin

from apps.www.views import HomeView, BlogView, VisitorsView, PhotosView, WeatherView, BlogDetailView, BlogEditView, BlogCreateView, \
    api_post, wrapped_login, wrapped_logout, BoatCamView, DayInTheLifeView, AdilHourView, AdilHomeView, api_is_scheduled, \
    WebcamView, WcMonthView
from apps.www import urls as api_urls

urlpatterns = [

    url(r'^$', BlogView.as_view(), name='home'),
    # url(r'^blog$', BlogView.as_view(), name='blog-home'),
    url(r'^blog/view/(?P<slug>[-\w]+)/$', BlogDetailView.as_view(), name='blog-detail'),
    url(r'^blog/edit/(?P<slug>[-\w]+)/$', BlogEditView.as_view(), name='blog-edit'),
    url(r'^blog/add$', BlogCreateView.as_view(), name='blog-add'),
    url(r'^visitors$', VisitorsView.as_view(), name='visitors'),
    url(r'^photos$', PhotosView.as_view(), name='photos'),
    url(r'^weather$', WeatherView.as_view(), name='weather'),
    url(r'^boat_cam$', BoatCamView.as_view(), name='boat_cam'),
    url(r'^adil$', AdilHomeView.as_view(), name='adil_home'),
    url(r'^api_post/(?P<slug>[-\w]+)/$', api_post, name='api_post'),
    url(r'^api_sched/(?P<slug>[-\w]+)/$', api_is_scheduled, name='is_sched'),

    url(r'^webcam/(?P<slug>[-\w]+)/$', WebcamView.as_view(), name='webcam'),
    url(r'^webcam/(?P<slug>[-\w]+)/(?P<year>[0-9]{4})/(?P<month>[0-9]{2})/$', WcMonthView.as_view(), name='wc_month'),
    url(r'^webcam/(?P<slug>[-\w]+)/(?P<year>[0-9]{4})/(?P<month>[0-9]{2})/(?P<day>[0-9]{2})/$', DayInTheLifeView.as_view(), name='adil'),
    url(r'^webcam/(?P<slug>[-\w]+)/(?P<year>[0-9]{4})/(?P<month>[0-9]{2})/(?P<day>[0-9]{2})/(?P<hour>[0-9]{2})/$', AdilHourView.as_view(), name='adil_hour'),

    url(r'^login/$', wrapped_login, name='login'),
    url(r'^logout/$', wrapped_logout, name='logout'),

    url(r'^admin/', admin.site.urls),

    url('^api/', include(api_urls))
]
