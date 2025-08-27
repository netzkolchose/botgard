from pathlib import Path

# admin site overrides
from django.utils.translation import gettext_lazy as _

import decouple

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = Path(__file__).resolve().parent.parent

# --- CI variables --

POSTGRES_PASSWORD = decouple.config('POSTGRES_PASSWORD', default='')
POSTGRES_DATABASE = decouple.config('POSTGRES_DATABASE', default='postgres')
POSTGRES_USER = decouple.config('POSTGRES_USER', default='postgres')
POSTGRES_HOST = decouple.config('POSTGRES_HOST', default='localhost')
POSTGRES_PORT = decouple.config('POSTGRES_PORT', default='5432')

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = decouple.config(
    'DJANGO_SECRET_KEY',
    default='L3RFrJsYJco5PB-IW4I9T6Z-GMt_2RcW52zC-aiX85irpghG2QlHUhU5em8vwQGZ'
)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = decouple.config("DJANGO_DEBUG", default=True, cast=bool)

ALLOWED_HOSTS = decouple.config('DJANGO_ALLOWED_HOSTS', default="*").split()
CSRF_TRUSTED_ORIGINS = decouple.config("DJANGO_CSRF_TRUSTED_ORIGINS", default="").split()

TIME_ZONE = decouple.config('DJANGO_TIME_ZONE', default='Europe/Berlin')


# ------------

STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'

# Application definition

# Note: apps need to be ordered by dependency of foreign key models
# for tools/autocomplete.py to work.
# This can be changed however, by creating separate forms.py for each app
# right now they are created in each models.py
INSTALLED_APPS = [
    'modeltranslation',         # internationalization for models
    'config_app.apps.ConfigAppConfig',
    'botman.apps.BotmanConfig',
    'sidebar',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.humanize',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.postgres',

    'config_tables.apps.ConfigTablesConfig',
    'species.apps.SpeciesConfig',
    'individuals.apps.IndividualsConfig',
    'entrybook.apps.EntryBookConfig',
    'plantimages.apps.PlantimagesConfig',
    'seedcatalog.apps.SeedcatalogConfig',
    'tickets.apps.TicketsConfig',
    'labels.apps.LabelsConfig',
    'ajax.apps.AjaxConfig',
    'easy_thumbnails',
    'BotGard',
]


THUMBNAIL_ALIASES = {
    '': {
        'preview': {'size': (50, 50), 'crop': True},
        'large_preview': {'size': (500, 500), 'crop': True},
    },
}

DIRS = [
    'templates'
]


MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'tools.global_request.GlobalRequestMiddleware',
]

ROOT_URLCONF = 'BotGard.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': ['templates/'],
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

WSGI_APPLICATION = 'BotGard.wsgi.application'


# Database

if POSTGRES_PASSWORD:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': POSTGRES_DATABASE,
            'USER': POSTGRES_USER,
            'PASSWORD': POSTGRES_PASSWORD,
            'HOST': POSTGRES_HOST,
            'PORT': POSTGRES_PORT,
        }
    }
else:
    DATABASES = {
        'default': {
            'CONN_MAX_AGE': 0,
            'ENGINE': 'django.db.backends.sqlite3',
            'HOST': 'localhost',
            'NAME': 'db.sqlite3',
            'PASSWORD': '',
            'PORT': '',
            'USER': ''
        }
    }

DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'


# Password validation

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

LANGUAGE_CODE = 'en'

LANGUAGES = [
  ('de', _('German')),
  ('en', _('English')),
]

LOCALE_PATHS = [
    BASE_DIR / 'locale'
]


USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'static'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / "media"

IS_POSTGRES = "postgres" in DATABASES.get("default", {}).get("ENGINE", "")
