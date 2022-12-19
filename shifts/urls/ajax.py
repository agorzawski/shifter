from django.urls import include, path

from shifts.views import ajax as ajax_views

urlpatterns = [
    path('get_events', ajax_views.get_events, name='ajax.get_events'),
    path('get_studies', ajax_views.get_studies, name='ajax.get_studies'),
    path('get_user_events', ajax_views.get_user_events, name='ajax.get_user_events'),
    path('get_user_future_events', ajax_views.get_user_future_events, name='ajax.get_user_future_events'),
    path('get_team_events', ajax_views.get_team_events, name='ajax.get_team_events'),
    path('get_holidays', ajax_views.get_holidays, name='ajax.get_holidays'),
    path('get_revision_name', ajax_views.get_revision_name, name='ajax.get_revision_name'),
]
