"""
Project-level URL configuration for the booklibrary project.

Routes:
  /                Redirect → /booklibrary/ (home)
  /admin/          Django admin
  /accounts/       Auth views (login, logout, password reset, …)
  /booklibrary/    Main app (namespace: booklibrary)
  /site/<path>     Static HTML site browser
  /favicon.ico     Favicon
  /__debug__/      Django Debug Toolbar (DEBUG only)
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path
from django.views.generic import RedirectView
from django.views.static import serve

urlpatterns = [
    path('', RedirectView.as_view(pattern_name='booklibrary:index', permanent=False)),

    path('admin/', admin.site.urls),

    # Explicit login entry so reverse('login') resolves without a namespace.
    # Must precede the auth include to take precedence.
    path('accounts/login/', auth_views.LoginView.as_view(), name='login'),
    path('accounts/', include('django.contrib.auth.urls')),

    path('booklibrary/', include(('booklibrary.urls', 'booklibrary'), namespace='booklibrary')),

    # Static HTML site browser
    path('site/<path:path>', serve,
         {'document_root': settings.BASE_DIR / 'site', 'show_indexes': False},
         name='site_path'),

    path('favicon.ico', serve, {
        'path': 'favicon.ico',
        'document_root': settings.BASE_DIR / 'booklibrary' / 'static',
    }),
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

if settings.DEBUG:
    urlpatterns += [path('__debug__/', include('debug_toolbar.urls'))]
