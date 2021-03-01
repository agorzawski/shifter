from django.urls import path

from . import views
app_name='shifter'
urlpatterns = [
    path('', views.index, name='index'),
    path('today', views.todays, name='today'),
    path('user', views.user, name='user'),
    path('calendar.ics', views.icalendar_view, name='calendar'),
    path('dates', views.dates, name='dates'),
    path('ioc-update', views.ioc_update, name='ioc-update'),
    path('shift-upload-csv', views.shifts_upload, name="shift-upload"),
]
