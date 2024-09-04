from django.urls import path
from . import views

urlpatterns = [
    path('', views.seo_analysis_with_ai, name='seo_analysis_with_ai'),
]