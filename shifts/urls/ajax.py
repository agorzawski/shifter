from django.urls import include, path

from shifts.views import ajax as ajax_views

urlpatterns = [
    path('get_events', ajax_views.get_events, name='ajax.get_events'),
    path('get_user_events', ajax_views.get_user_events, name='ajax.get_user_events'),
    path('get_users_events', ajax_views.get_users_events, name='ajax.get_users_events'),
    # path('get_user_future_events', ajax_views.get_user_future_events, name='ajax.get_user_future_events'),
    #path('get_team_events', ajax_views.get_team_events, name='ajax.get_team_events'),
    path('get_holidays', ajax_views.get_holidays, name='ajax.get_holidays'),
    path('get_assets', ajax_views.get_assets, name='ajax.get_assets'),
    path('get_hr_codes', ajax_views.get_hr_codes, name='ajax.get_hr_codes'),
    path('get_team_hr_codes', ajax_views.get_team_hr_codes, name='ajax.get_team_hr_codes'),
    path('get_team_breakdown', ajax_views.get_shift_breakdown, name='ajax.get_team_breakdown'),
    path('get_shifts_for_exchange', ajax_views.get_shifts_for_exchange, name='ajax.get_shifts_for_exchange'),
    path('search', ajax_views.search, name='ajax.search')
]
