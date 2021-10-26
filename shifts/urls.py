from django.urls import include, path

from . import views
app_name='shifter'
urlpatterns = [
    path('', views.index, name='index'),
    path('planning', views.index_post, name='index-post'),
    path('today', views.todays, name='today'),
    path('user', views.user, name='user'),
    path('u', views.user_simple, name='user-simple'),
    path('team', views.team, name='team'),
    path('t', views.team_simple, name='team-simple'),
    path('calendar.ics', views.icalendar_view, name='calendar'),
    path('ical', views.icalendar, name='calendar_public'),
    path('dates', views.dates, name='dates'),
    path('phonebook', views.phonebook, name='phonebook'),
    path('phonebook-post', views.phonebook_post, name='phonebook-post'),
    path('ioc-update', views.ioc_update, name='ioc-update'),
    path('shift-upload-csv', views.shifts_upload, name="shift-upload"),
    path('shift-upload-csv-post', views.shifts_upload_post, name="shift-upload-post"),
    path('shift-update', views.shifts_update, name="shift-update"),
    path('shift-update-post', views.shifts_update_post, name="shift-update-post"),
]
