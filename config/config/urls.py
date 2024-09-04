from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('', include('index.urls')),
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),  # This includes allauth's login, register, etc.
    path('seo/', include('seo.urls')),  # Your SEO app's URLs
    path('user/', include('users.urls')),  # Your SEO app's URLs
]