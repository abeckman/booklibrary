import os
from django.contrib import admin
from django.urls import include, path
from django.views.static import serve
from django.conf import settings
from django.conf.urls.static import static

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),

    path('booklibrary/', include(('booklibrary.urls', 'booklibrary'), namespace='booklibrary')),

    # Static HTML site browser
    path('site/<path:path>', serve,
         {'document_root': os.path.join(BASE_DIR, 'site'), 'show_indexes': True},
         name='site_path'),

    path('favicon.ico', serve, {
        'path': 'favicon.ico',
        'document_root': os.path.join(BASE_DIR, 'booklibrary/static'),
    }),
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

if settings.DEBUG:
    urlpatterns += [path('__debug__/', include('debug_toolbar.urls'))]
