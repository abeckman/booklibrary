"""
Django settings for library project.
Generated by 'django-admin startproject' using Django 4.0.
For more information on this file, see
https://docs.djangoproject.com/en/4.0/topics/settings/
For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.0/ref/settings/
"""

#from pathlib import Path # orig
import os # orig
from distutils.util import strtobool # orig
import sys

sys.modules['fontawesomefree'] = __import__('fontawesomefree')

# Build paths inside the project like this: BASE_DIR / 'subdir'.
#BASE_DIR = Path(__file__).resolve().parent.parent
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Used for a default title
APP_NAME = 'Home Book Librarian'

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.0/howto/deployment/checklist/


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv("SECRET_KEY", '1ldyeqs!3!&(4(%qjj=6mgh+bj8@cq#h*c9hiifjd_o=r9mt^p')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = bool(strtobool(os.getenv("DEBUG", "true")))

# Not sure this is used
INTERNAL_IPS = ('HTTP_X_REAL_IP')

# https://docs.djangoproject.com/en/4.0/ref/settings/#std:setting-ALLOWED_HOSTS
#allowed_hosts = os.getenv("ALLOWED_HOSTS", ".localhost,127.0.0.1,[::1]")
#ALLOWED_HOSTS = list(map(str.strip, allowed_hosts.split(",")))
# Set hosts to allow any app on Heroku and the local testing URL
#ALLOWED_HOSTS = ['.herokuapp.com','127.0.0.1']
ALLOWED_HOSTS = ['*']

# Application definitions
INSTALLED_APPS = [
#    "pages.apps.PagesConfig",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    'django.contrib.staticfiles', # first six are default
    'django.contrib.humanize',
    'django_bootstrap_icons',
    'fontawesomefree',
#    'debug_toolbar',
    # Extensions - installed with pip3 / requirements.txt
    'django_extensions', # used to load database from CSV
    'crispy_forms',
    'rest_framework',
    'social_django',
    'booklibrary.apps.BooklibraryConfig', # apps added goes here
]

# When we get to crispy forms :)
CRISPY_TEMPLATE_PACK = 'bootstrap4'  # Add

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    'social_django.middleware.SocialAuthExceptionMiddleware',   # Add
#    'debug_toolbar.middleware.DebugToolbarMiddleware',
]

ROOT_URLCONF = 'library.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, "templates")],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
#                'home.context_processors.settings',      # Add
#                'booklibrary.context_processors.settings',      # Add
#                'social_django.context_processors.backends',  # Add
#                'social_django.context_processors.login_redirect', # Add
            ],
        },
    },
]

WSGI_APPLICATION = 'library.wsgi.application'

# Database
# https://docs.djangoproject.com/en/4.0/ref/settings/#databases

#DATABASES = {
#    'default': {
#        'ENGINE': 'django.db.backends.sqlite3',
#        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
#    }
#}

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'abeckman$booklibrary',
        'USER': 'abeckman',
        'PASSWORD': 'HamsterHaven20',
        'HOST': 'abeckman.mysql.pythonanywhere-services.com',
         'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}

# Default primary key field type
# https://docs.djangoproject.com/en/4.0/ref/settings/#default-auto-field
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField" # set default for primary key set automatically

# Password validation
# https://docs.djangoproject.com/en/4.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Sessions
# https://docs.djangoproject.com/en/4.0/ref/settings/#sessions
SESSION_ENGINE = "django.contrib.sessions.backends.signed_cookies"

# Redis
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

# Caching
# https://docs.djangoproject.com/en/4.0/topics/cache/
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": REDIS_URL,
    }
}

# Celery
# https://docs.celeryproject.org/en/stable/userguide/configuration.html
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL

"""
# Internationalization
# https://docs.djangoproject.com/en/4.0/topics/i18n/
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.0/howto/static-files/
STATIC_URL = "/static/"
STATICFILES_DIRS = ["/public", os.path.join(BASE_DIR, "..", "public")]
STATIC_ROOT = "/public_collected"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
"""

# Internationalization
# https://docs.djangoproject.com/en/4.0/topics/i18n/
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.0/howto/static-files/
STATIC_URL = '/static/'
# The absolute path to the directory where collectstatic will collect static files for deployment.
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# Add the settings below

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.BasicAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    )
}

# Configure the social login
#try:
#    from . import github_settings
#    SOCIAL_AUTH_GITHUB_KEY = github_settings.SOCIAL_AUTH_GITHUB_KEY
#    SOCIAL_AUTH_GITHUB_SECRET = github_settings.SOCIAL_AUTH_GITHUB_SECRET
#except:
#    print('When you want to use social login, please see dj4e-samples/github_settings-dist.py')

# https://python-social-auth.readthedocs.io/en/latest/configuration/django.html#authentication-backends
# https://simpleisbetterthancomplex.com/tutorial/2016/10/24/how-to-add-social-login-to-django.html
AUTHENTICATION_BACKENDS = (
#    'social_core.backends.github.GithubOAuth2',
    # 'social_core.backends.twitter.TwitterOAuth',
    # 'social_core.backends.facebook.FacebookOAuth2',

    'django.contrib.auth.backends.ModelBackend',
)

LOGOUT_REDIRECT_URL = '/'
LOGIN_REDIRECT_URL = '/' # from catalog
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend' # from catalog

# Don't set default LOGIN_URL - let django.contrib.auth set it when it is loaded
# LOGIN_URL = '/accounts/login'

# https://coderwall.com/p/uzhyca/quickly-setup-sql-query-logging-django
# https://stackoverflow.com/questions/12027545/determine-if-django-is-running-under-the-development-server

# Leave off for now
#import sys
#if (len(sys.argv) >= 2 and sys.argv[1] == 'runserver'):
#    print('Running locally')
#    LOGGING = {
#        'version': 1,
#        'disable_existing_loggers': False,
#        'handlers': {
#            'console': {
#                'level': 'DEBUG',
#                'class': 'logging.StreamHandler',
#            }
#        },
#        'loggers': {
#            'django.db.backends': {
#                'handlers': ['console'],
#                'level': 'DEBUG',
#            },
#        }
#    }
#
#
#def custom_show_toolbar(request.META.get('HTTP_X_REAL_IP', None) in INTERNAL_IPS):
#    return True
## Show toolbar, if the IP returned from HTTP_X_REAL_IP IS listed as INTERNAL_IPS in settings
#    if request.is_ajax():
#        return False
## Show toolbar, if the request is not ajax
#    return bool(settings.DEBUG)
## show toolbar if debug is true
#
#DEBUG_TOOLBAR_CONFIG = {
#    'SHOW_TOOLBAR_CALLBACK': custom_show_toolbar,
#}
#
#class SetRemoteAddrFromForwardedFor(object):
#    def process_request(self, request):
#        try:
#            real_ip = request.META['HTTP_X_FORWARDED_FOR']
#        except KeyError:
#            pass
#        else:
#            # HTTP_X_FORWARDED_FOR can be a comma-separated list of IPs.
#            # Take just the first one.
#            real_ip = real_ip.split(",")[0]
#            request.META['REMOTE_ADDR'] = real_ip