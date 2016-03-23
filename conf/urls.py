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
    api_post, wrapped_login, wrapped_logout, BoatCamView
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

    url(r'^api_post$', api_post, name='api_post'),

    url(r'^login/$', wrapped_login, name='login'),
    url(r'^logout/$', wrapped_logout, name='logout'),

    url(r'^admin/', admin.site.urls),

    url('^api/', include(api_urls))
]
