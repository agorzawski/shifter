"""
Django settings for shifter project.

Generated by 'django-admin startproject' using Django 3.1.3.

For more information on this file, see
https://docs.djangoproject.com/en/3.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.1/ref/settings/
"""

from pathlib import Path
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = bool(os.getenv('DJANGO_DEBUG', "False"))

ALLOWED_HOSTS = list(filter(None, os.getenv('DJANGO_ALLOWED_HOSTS',"").split(',')))


# Application definition

INSTALLED_APPS = [
    'members.apps.MembersConfig',
    'shifts.apps.ShiftsConfig',

    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
#    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'shifter.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'shifter.wsgi.application'


# Database
# https://docs.djangoproject.com/en/3.1/ref/settings/#databases


if os.getenv('DJANGO_LOCAL_DEV'):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': os.getenv('DATABASE_ENGINE'),
            'HOST': os.getenv('DATABASE_HOST'),
            'PORT': os.getenv('DATABASE_PORT'),
            'NAME': os.getenv('DATABASE_NAME'),
            'USER': os.getenv('DATABASE_USER'),
            'PASSWORD': os.getenv('DATABASE_PASSWORD')
        }
    }


SERVICE_ACCOUNT_EMAIL = os.getenv('DJANGO_SERVICE_ACCOUNT_EMAIL', 'noreply@ess.eu')
SERVICE_ACCOUNT_USER = os.getenv('DJANGO_SERVICE_ACCOUNT_USER', 'noreply')
SERVICE_ACCOUNT_PASSWORD = os.getenv('DJANGO_SERVICE_ACCOUNT_PASSWORD')

DEFAULT_FROM_EMAIL = SERVICE_ACCOUNT_EMAIL
EMAIL_FILE_PATH = os.path.join(BASE_DIR, 'sent_emails')

if DEBUG:
    EMAIL_BACKEND = 'django.core.mail.backends.filebased.EmailBackend'

elif SERVICE_ACCOUNT_PASSWORD:
    EMAIL_HOST = 'smtp-relay.esss.lu.se'
    EMAIL_PORT = 587
    EMAIL_HOST_USER = SERVICE_ACCOUNT_EMAIL
    EMAIL_HOST_PASSWORD = SERVICE_ACCOUNT_PASSWORD
    EMAIL_USE_TLS = True

else:
    EMAIL_HOST = 'smtp-relay.esss.lu.se'
    EMAIL_PORT = 25



# Password validation
# https://docs.djangoproject.com/en/3.1/ref/settings/#auth-password-validators

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

AUTH_USER_MODEL = 'members.Member'

LOGIN_REDIRECT_URL = '/user'
LOGOUT_REDIRECT_URL = '/'
LOGIN_URL = 'options/login/'

# Internationalization
# https://docs.djangoproject.com/en/3.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Europe/Stockholm'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.1/howto/static-files/

STATIC_URL = '/static/'
#STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
#STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MAIN_PAGE_HOME_BUTTON = os.getenv('MAIN_PAGE_HOME_BUTTON', 'Shifter')
APP_REPO = os.getenv('APP_REPO', 'NO REPO PROVIDED')
APP_REPO_ICON = os.getenv('APP_REPO_ICON', 'https://github.githubassets.com/favicon.ico')
CONTROL_ROOM_PHONE_NUMBER = os.getenv('CONTROL_ROOM_PHONE_NUMBER', 'No number provided.')
WWW_EXTRA_INFO = os.getenv('WWW_EXTRA_INFO', '')
PHONEBOOK_NAME = os.getenv('PHONEBOOK_NAME', 'Phonebook')

SHIFTER_TEST_INSTANCE = os.getenv("SHIFTER_TEST_INSTANCE", 'False').lower() in ('true', '1', 't')
SHIFTER_PRODUCTION_INSTANCE = os.getenv('SHIFTER_PRODUCTION_INSTANCE', '')
STOP_DEV_MESSAGES = os.getenv('STOP_DEV_MESSAGES', 'False').lower() in ('true', '1', 't')
