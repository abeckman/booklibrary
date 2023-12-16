"""library URL Configuration
The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin # orig
from django.urls import include, path # from polls and catalog apps
import os
from django.views.static import serve
from django.conf import settings
from django.conf.urls.static import static
# from django.contrib.auth import views as auth_views
# from django.views.generic import RedirectView # from catalog
# from django.conf import settings # from catalog for static
# from django.conf.urls.static import static # from catalog for including static URL - not used?
import debug_toolbar

from django.urls import re_path # suggested replacement for orig url

"""from myapp.views import home

urlpatterns = [
    re_path(r'^$', home, name='home'),
    re_path(r'^myapp/', include('myapp.urls'),
]
"""
# app_name = "booklibrary"

urlpatterns = [
    re_path(r'^admin/', admin.site.urls), # orig
    path('booklibrary/', include('booklibrary.urls')), # modified from polls app, same as catalog app
    path('blog/', include('blog.urls')),
    path('newblog/', include('newblog.urls')),
#    path('__debug__/', include(debug_toolbar.urls)),
    #Add URL maps to redirect the base URL to our application
    path('', include(('booklibrary.urls', 'booklibrary'), namespace='booklibrary')),
#    path('', RedirectView.as_view(url='booklibrary/', permanent=True)), # catalog alternative to above
# Above doesn't work - missing namespace?
    re_path(r'^oauth/', include('social_django.urls', namespace='social')),
]

#Add Django site authentication urls (for login, logout, password management) - from catalog

urlpatterns += [
    path('accounts/', include('django.contrib.auth.urls')),
]

# Serve the static HTML
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
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

# Template for search functions
#urlpatterns += [
#    path('mybooks/', views.LoanedBooksByUserListView.as_view(), name='my-borrowed'),
#]

# Switch to social login if it is configured - Keep for later
#try:
#    from . import github_settings
#    social_login = 'registration/login_social.html'
#    urlpatterns.insert(0,
#                       path('accounts/login/', auth_views.LoginView.as_view(template_name=social_login))
#                       )
#    print('Using', social_login, 'as the login template')
#except:
#    print('Using registration/login.html as the login template')

# References

# https://docs.djangoproject.com/en/3.0/ref/urls/#include
