from .ajax import urlpatterns as ajax
from .desiderata import urlpatterns as desiderata
from .main import urlpatterns as main
from django.urls import include, path

app_name = 'shifter'
handler404 = 'shifts.views.errors.page_not_found'
urlpatterns = [
    path('', include(main)),
    path('ajax/', include(ajax)),
    path('desiderata', include(desiderata)),
]