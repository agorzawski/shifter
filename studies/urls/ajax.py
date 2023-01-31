from django.urls import include, path

from studies.views import ajax as ajax_views

urlpatterns = [
    path('get_studies', ajax_views.get_studies, name='ajax.get_studies'),
    path('get_all_studies', ajax_views.get_all_studies, name='ajax.get_all_studies'),
]
