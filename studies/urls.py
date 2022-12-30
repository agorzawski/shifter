from django.urls import include, path

from . import views

app_name = 'studies'
handler404 = 'studies.views.page_not_found'
urlpatterns = [
   path('request', views.request, name='request'),
   path('request-post', views.request_post, name='request-post'),
   path('request-post-close', views.request_post_close, name='request-post-close'),
]
