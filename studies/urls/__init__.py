from .ajax import urlpatterns as ajax
from .main import urlpatterns as main
from django.urls import include, path

app_name = 'studies'
urlpatterns = [
    path('', include(main)),
    path('ajax/', include(ajax)),
]