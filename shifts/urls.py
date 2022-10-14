from django.urls import include, path

from . import views

app_name = 'shifter'
handler404 = 'shifts.views.page_not_found'
urlpatterns = [
    path('', views.index, name='index'),
    path('planning', views.index_post, name='index-post'),
    path('today', views.todays, name='today'),
    path('user', views.user, name='user'),
    path('user/rev/<int:rid>', views.user, name='user'),
    path('user/<int:u>', views.user, name='user'),
    path('user/<int:u>/rev/<int:rid>', views.user, name='user'),

    path('team', views.team, name='team'),
    path('t', views.team_simple, name='team-simple'),  # FIXME add/id/remove?
    path('calendar.ics', views.icalendar_view, name='calendar'),
    path('ical', views.icalendar, name='calendar_public'),
    path('dates', views.dates, name='dates'),
    path('slots-update', views.dates_slots_update, name='slots-update-post'),
    path('phonebook', views.phonebook, name='phonebook'),
    path('phonebook-post', views.phonebook_post, name='phonebook-post'),
    path('ioc-update', views.ioc_update, name='ioc-update'),
    path('scheduled-work-time', views.scheduled_work_time, name='scheduled_work_time'),
    path('shifts', views.shifts, name='shifts'),
    path('shift-upload-csv', views.shifts_upload, name="shift-upload"),
    path('shift-upload-csv-post', views.shifts_upload_post, name="shift-upload-post"),
    path('shift-update', views.shifts_update, name="shift-update"),
    path('shift-update-post', views.shifts_update_post, name="shift-update-post"),
    path('assets', views.assets, name="assets"),
    path('assets-post', views.assets_post, name="assets-post"),
    path('assets-post-close', views.assets_post_close, name="assets-post-close"),
]
