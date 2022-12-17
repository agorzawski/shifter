from django.urls import include, path

from shifts.views import desiderata
from shifts.views import main as views

urlpatterns = [
    path('user', desiderata.user, name='desiderata.user'),
    path('add', desiderata.add, name='desiderata.add'),
    path('edit', desiderata.edit, name='desiderata.edit'),
    path('delete', desiderata.delete, name='desiderata.delete'),
    path('get_user_desiderata', desiderata.get_user_desiderata, name='desiderata.get_user_desiderata'),
    path('team_view/<int:team_id>', desiderata.team_view, name='desiderata.team_view'),
    path('get_team_desiderata', desiderata.get_team_desiderata, name='desiderata.get_team_desiderata'),
    path('options/', include('django.contrib.auth.urls')),
]
