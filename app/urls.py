from django.conf.urls import url
from django.views.generic.base import RedirectView
from . import views

app_name = 'app'

favicon_view = RedirectView.as_view(url='/static/favicon.ico', permanent=True)

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^oauth/?$', views.oauth, name='oauth'),
    url(r'^callback/?$', views.callback, name='callback'),
    url(r'^connected/?$', views.connected, name='connected'),
    url(r'^account/?$', views.account, name='account'),
    url(r'^refresh/?$', views.refresh, name='refresh'),
]
