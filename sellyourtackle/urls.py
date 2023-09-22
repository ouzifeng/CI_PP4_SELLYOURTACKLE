from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('auth/', include('auth_app.urls')),
    path('', include('tackle.urls')),
    
]
