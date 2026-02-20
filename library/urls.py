import os
from django.contrib import admin # orig
from django.urls import include, path, re_path # from polls and catalog apps
from django.views.static import serve # from polls and catalog apps
from django.conf import settings
from django.conf.urls.static import static
import debug_toolbar

app_name = "booklibrary" # from polls for template namespace

urlpatterns = [
    re_path(r'^admin/', admin.site.urls), # orig
    path('booklibrary/', include('booklibrary.urls')), # modified from polls app, same as catalog app
    path('blog/', include('blog.urls')),
    path('newblog/', include('newblog.urls')),
    #Add URL maps to redirect the base URL to our application
    path('', include(('booklibrary.urls', 'booklibrary'), namespace='booklibrary')),
]

urlpatterns += [
    path('accounts/', include('django.contrib.auth.urls')), # from DJ4E
]

# Serve the static HTML
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # from polls and catalog apps
urlpatterns += [
    re_path(r'^site/(?P<path>.*)$', serve,
        {'document_root': os.path.join(BASE_DIR, 'site'),
         'show_indexes': True},
        name='site_path'
        ),
]
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) # catalog way of doing above

# Serve the favicon - Keep for later
urlpatterns += [
    path('favicon.ico', serve, {
            'path': 'favicon.ico',
            'document_root': os.path.join(BASE_DIR, 'booklibrary/static'),
        }
    ),
]

if settings.DEBUG:
    urlpatterns += [
        path("__debug__/", include(debug_toolbar.urls)),
    ]

