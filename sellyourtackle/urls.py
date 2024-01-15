from django.contrib import admin
from django.urls import path, include, re_path
from django.views.static import serve
import os
from django.conf import settings


urlpatterns = [
    path('admin/', admin.site.urls),
    path('auth/', include('auth_app.urls')),
    path('', include('tackle.urls')),
    path('accounts/', include('allauth.urls')),
    re_path(
        r'^\.well-known/apple-developer-merchantid-domain-association$',
        serve, {
            'document_root': os.path.join(
                settings.BASE_DIR,
                'verification-files',
                '.well-known'
            ),
            'path': 'apple-developer-merchantid-domain-association'
        }
    ),
]
