from django.urls import path, include
from . import views

urlpatterns = [


    # User profile update and dashboard
    path('profile/', views.profile_update, name='profile_update'),
    path('dashboard/', views.dashboard, name='dashboard'),
]
