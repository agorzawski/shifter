from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('today', views.todays, name='today'),
    path('dates', views.dates, name='dates'),
    path('ioc-update', views.ioc_update, name='ioc-update'),
]
