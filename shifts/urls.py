from django.urls import include, path

from . import views
app_name='shifter'
urlpatterns = [
    path('', views.index, name='index'),
    path('today', views.todays, name='today'),
    path('user', views.user, name='user'),
    path('team', views.team, name='team'),
    path('calendar.ics', views.icalendar_view, name='calendar'),
    path('dates', views.dates, name='dates'),
    path('phonebook', views.phonebook, name='phonebook'),
    path('ioc-update', views.ioc_update, name='ioc-update'),
    path('shift-upload-csv', views.shifts_upload, name="shift-upload"),
    path('shift-update', views.shifts_update, name="shift-update"),
    path('accounts/', include('django.contrib.auth.urls')),  # new
    path('options/', include('django.contrib.auth.urls')),
]
