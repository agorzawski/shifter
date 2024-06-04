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
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', '9e4@&tw46$l31)zrqe3wi+-slqm(ruvz&se0^%9#6(_w3ui!c0')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DJANGO_DEBUG', "False") == "True" or os.getenv('DJANGO_DEBUG', "False") == "1"

ALLOWED_HOSTS = list(filter(None, os.getenv('DJANGO_ALLOWED_HOSTS', "").split(',')))

# Application definition

INSTALLED_APPS = [
    'members.apps.MembersConfig',
    'shifts.apps.ShiftsConfig',
    'studies.apps.StudiesConfig',
    'assets.apps.AssetsConfig',
    'crispy_forms',
    "crispy_bootstrap5",
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'guardian',
    'watson',
    'notifications',
    'django_cron',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'watson.middleware.SearchContextMiddleware',
]


CRON_CLASSES = [
    'shifter.cron.MyCronJob',
    # ...
]

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend', # this is default
    'guardian.backends.ObjectPermissionBackend',
)

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
                'shifts.permanent_contexts.operation_crew_context',
                'shifts.permanent_contexts.useful_contact_context',
                'shifts.permanent_contexts.application_context',
                'shifts.permanent_contexts.rota_maker_role',
                'shifts.permanent_contexts.nav_bar_context',
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

DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'


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
LOGIN_URL = '/accounts/login/'


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
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
STATICFILES_FINDERS = ['npm.finders.NpmFinder',
                       'django.contrib.staticfiles.finders.FileSystemFinder',
                       'django.contrib.staticfiles.finders.AppDirectoriesFinder',
                       ]

NPM_FILE_PATTERNS = {
    'bootstrap': ['dist/css/bootstrap.min.css.map', 'dist/css/bootstrap.min.css',
                  'dist/js/bootstrap.bundle.min.js', 'dist/js/bootstrap.bundle.min.js.map'],
    'fullcalendar': ['main.min.css', 'main.min.css.map', 'main.min.js', 'main.min.js.map'],
    'highcharts': ['highcharts.js', 'modules/sankey.js', 'modules/dependency-wheel.js',
                   'modules/exporting.js', 'modules/export-data.js', 'modules/accessibility.js'],
    'jquery': ['dist/jquery.min.js', 'dist/jquery.min.js.map'],
    '@fortawesome': ['fontawesome-free/*'],
    'bootstrap-icons': ['*'],
    'select2': ['dist/css/select2.min.css', 'dist/js/*'],
    'datatables.net': ['js/jquery.dataTables.min.js'],
    'datatables.net-select': ['js/dataTables.select.min.js'],
    'datatables.net-bs5': ['js/dataTables.bootstrap5.min.js', 'css/dataTables.bootstrap5.min.css', 'images/*'],
    'datatables.net-searchpanes-bs5': ['js/searchPanes.bootstrap5.min.js', 'css/searchPanes.bootstrap5.min.css'],
    'datatables.net-searchpanes': ['js/dataTables.searchPanes.min.js'],
    'datatables.net-buttons-dt': ['css/buttons.dataTables.min.css'],
    'datatables.net-buttons': ['js/buttons.print.min.js', 'js/buttons.html5.min.js', 'js/dataTables.buttons.min.js'],
    'moment': ['min/moment-with-locales.min.js', 'min/moment-with-locales.min.js.map'],
    'daterangepicker': ['daterangepicker.css', 'daterangepicker.js'],
    'typeahead.js': ['dist/typeahead.bundle.min.js']
}


MAIN_PAGE_HOME_BUTTON = os.getenv('MAIN_PAGE_HOME_BUTTON', 'Shifter')
APP_REPO = os.getenv('APP_REPO', 'NO REPO PROVIDED')
APP_REPO_ICON = os.getenv('APP_REPO_ICON', 'https://github.githubassets.com/favicon.ico')
CONTROL_ROOM_PHONE_NUMBER = os.getenv('CONTROL_ROOM_PHONE_NUMBER', 'No number provided.')
WWW_EXTRA_INFO = os.getenv('WWW_EXTRA_INFO', '')
PHONEBOOK_NAME = os.getenv('PHONEBOOK_NAME', 'Phonebook')

NUMBER_OF_HOURS_BEFORE_SHIFT_SLOT_CHANGES = os.getenv('NUMBER_OF_HOURS_BEFORE_SHIFT_SLOT_CHANGES', 2)
DEFAULT_SHIFT_SLOT = os.getenv('DEFAULT_SHIFT_SLOT', 'NWH')  # requires one NormalWorkingHours
DEFAULT_SHIFTER_TO_JSON = os.getenv('DEFAULT_SHIFTER_TO_JSON', ['SL', 'OP', 'STL'])
DEFAULT_SPECIAL_SHIFT_ROLES = os.getenv('DEFAULT_SPECIAL_SHIFT_ROLES', ['ASL', 'AOP'])

SHIFTER_TEST_INSTANCE = os.getenv("SHIFTER_TEST_INSTANCE", 'False').lower() in ('true', '1', 't')
SHIFTER_PRODUCTION_INSTANCE = os.getenv('SHIFTER_PRODUCTION_INSTANCE', '')
STOP_DEV_MESSAGES = os.getenv('STOP_DEV_MESSAGES', 'False').lower() in ('true', '1', 't')

CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"
