from django.urls import include, path
from django.contrib.auth.decorators import login_required
from studies.views import main as views

app_name = 'studies'
handler404 = 'studies.views.page_not_found'
urlpatterns = [
   path('', login_required(views.StudyView.as_view()), name='study_request'),
   path('<int:sid>', login_required(views.SingleStudyView.as_view()), name='single_study_view'),
   path('close', views.studies_close, name='studies-close'),
]
