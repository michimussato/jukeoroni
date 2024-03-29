"""
Django settings for jukeoroni project.

Generated by 'django-admin startproject' using Django 3.2.5.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.2/ref/settings/
"""
import logging
import os

from jukeoroni._secrets import DJANGO_SECRET_KEY
from pathlib import Path
from player.jukeoroni.settings import Settings


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
# For JukeOroni is this probably not a big issue
SECRET_KEY = DJANGO_SECRET_KEY

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {
            'format': '[{asctime}] [{levelname:<8}] [{threadName}|{thread}], File "{pathname}", line {lineno}, in {funcName}:    {message}',
            'style': '{',
            'datefmt': '%m-%d-%Y %H:%M:%S',
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'file': {
            'level': 'ERROR',
            # 'class': 'logging.FileHandler',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'when': 'midnight',
            'interval': 1,
            'backupCount': 7,
            'filename': os.path.join(Settings.LOG_ROOT, 'django_error.log'),
            'formatter': 'simple',
        },
        'file_juke_box': {
            'level': 'DEBUG',
            # 'class': 'logging.FileHandler',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'when': 'midnight',
            'interval': 1,
            'backupCount': 7,
            'filename': os.path.join(Settings.LOG_ROOT, 'jukebox_error.log'),
            'formatter': 'simple',
        },
        'file_meditation_box': {
            'level': 'DEBUG',
            # 'class': 'logging.FileHandler',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'when': 'midnight',
            'interval': 1,
            'backupCount': 7,
            'filename': os.path.join(Settings.LOG_ROOT, 'meditationbox_error.log'),
            'formatter': 'simple',
        },
        'file_video_box': {
            'level': 'DEBUG',
            # 'class': 'logging.FileHandler',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'when': 'midnight',
            'interval': 1,
            'backupCount': 7,
            'filename': os.path.join(Settings.LOG_ROOT, 'videobox_error.log'),
            'formatter': 'simple',
        },
        'file_create_update_track_list': {
            'level': 'DEBUG',
            # 'class': 'logging.FileHandler',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'when': 'midnight',
            'interval': 1,
            'backupCount': 7,
            'filename': os.path.join(Settings.LOG_ROOT, 'create_update_track_list_error.log'),
            'formatter': 'simple',
        },
        'file_create_update_track_list_missing_cover': {
            'level': 'ERROR',
            # 'class': 'logging.FileHandler',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'when': 'midnight',
            'interval': 1,
            'backupCount': 7,
            'filename': Settings.MISSING_COVERS_FILE,
            'formatter': 'simple',
        },
        'file_track_loader': {
            'level': 'DEBUG',
            # 'class': 'logging.FileHandler',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'when': 'midnight',
            'interval': 1,
            'backupCount': 7,
            'filename': os.path.join(Settings.LOG_ROOT, 'track_loader_error.log'),
            'formatter': 'simple',
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['console', 'file'],
            # 'propagate': False,
            'level': 'DEBUG',
        },
        'PIL': {
            'handlers': ['console', 'file'],
            # 'propagate': True,
            'level': 'WARNING',
        },
        'urllib': {
            'handlers': ['console', 'file'],
            # 'propagate': True,
            'level': 'WARNING',
        },
        'urllib3': {
            'handlers': ['console', 'file'],
            # 'propagate': True,
            'level': 'WARNING',
        },
        'selenium': {
            'handlers': ['console', 'file'],
            # 'propagate': True,
            'level': 'WARNING',
        },
        'asyncio': {
            'handlers': ['console', 'file'],
            # 'propagate': True,
            'level': 'WARNING',
        },
        'omxplayer': {
            'handlers': ['console', 'file'],
            # 'propagate': True,
            'level': 'WARNING',
        },
        'player.jukeoroni': {
            'handlers': ['console'],
            # 'propagate': True,
            'level': 'INFO',
        },
        'player.jukeoroni.clock': {
            'handlers': ['file'],
            # 'propagate': True,
            'level': 'INFO',
        },
        # 'player.jukeoroni.discogs': {
        #     'handlers': ['file_juke_box'],
        #     # 'propagate': True,
        #     'level': 'INFO',
        # },
        'player.jukeoroni.juke_box': {
            'handlers': ['file_juke_box'],
            # 'propagate': True,
            'level': 'DEBUG',
        },
        'player.jukeoroni.meditation_box': {
            'handlers': ['file_meditation_box'],
            # 'propagate': True,
            'level': 'DEBUG',
        },
        'player.jukeoroni.video_box': {
            'handlers': ['file_video_box'],
            # 'propagate': True,
            'level': 'DEBUG',
        },
        'player.jukeoroni.create_update_track_list': {
            'handlers': ['file_create_update_track_list', 'file_create_update_track_list_missing_cover'],
            # 'propagate': True,
            'level': 'DEBUG',
        },
        'player.jukeoroni.track_loader': {
            'handlers': ['file_track_loader'],
            # 'propagate': True,
            'level': 'DEBUG',
        },
    },
    'root': {
        'level': 'DEBUG',
        'handlers': ['file']
    }
}


LOG = logging.getLogger(__name__)
LOG.setLevel(Settings.DJANGO_LOGGING_LEVEL)


ALLOWED_HOSTS = ['*']


# Application definition

INSTALLED_APPS = [
    'player.apps.PlayerConfig',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_bootstrap5',
    'django_object_actions',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'jukeoroni.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [(os.path.join(BASE_DIR, 'templates')), ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'jukeoroni.wsgi.application'


# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': BASE_DIR / 'db.sqlite3',
#         # 'NAME': BASE_DIR / '..' / 'db.sqlite3',
#     }
# }

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'jukeoroni_db',
        'USER': 'pi',
        'PASSWORD': '1234',
        'HOST': 'localhost',
        'PORT': '',
    }
}

LOG.critical(f'USING DB {str(os.path.abspath(DATABASES["default"]["NAME"]))} (engine: {str(os.path.abspath(DATABASES["default"]["ENGINE"]))})')

# Password validation
# https://docs.djangoproject.com/en/3.2/ref/settings/#auth-password-validators

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


# Internationalization
# https://docs.djangoproject.com/en/3.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

# TIME_ZONE = 'UTC'
TIME_ZONE = 'Europe/Zurich'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/

# STATIC_ROOT = '/data/venv/lib/python3.7/site-packages/django/contrib/admin'

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')
# STATICFILES_DIRS = [
#    os.path.join(BASE_DIR, 'player/static/'),
# ]

# STATICFILES_DIRS = [
#     BASE_DIR / "static",
#     '/data/venv/lib/python3.7/site-packages/django/contrib/admin',
# ]

# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
