# Django settings for Playto payout engine
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'dev-secret-change-in-production-abc123xyz')
DEBUG = os.getenv('DJANGO_DEBUG', 'True') == 'True'
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '*').split(',')

# ── Applications ──────────────────────────────
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    'rest_framework',
    'payouts',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'payouts.middleware.IdempotencyMiddleware',
]

ROOT_URLCONF = 'playto.urls'

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

WSGI_APPLICATION = 'playto.wsgi.application'

# ── Database ──────────────────────────────────
if os.getenv('USE_SQLITE', 'False') == 'True':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME':     os.getenv('POSTGRES_DB',       'playto'),
            'USER':     os.getenv('POSTGRES_USER',     'playto'),
            'PASSWORD': os.getenv('POSTGRES_PASSWORD', 'playto'),
            'HOST':     os.getenv('POSTGRES_HOST',     'db'),
            'PORT':     os.getenv('POSTGRES_PORT',     '5432'),
            'CONN_MAX_AGE': 60,
            'OPTIONS': {
                'isolation_level': 'read committed',
            },
        }
    }

# ── Password validation ───────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ── Internationalisation ──────────────────────
LANGUAGE_CODE = 'en-us'
TIME_ZONE     = 'Asia/Kolkata'
USE_I18N      = True
USE_TZ        = True

# ── Static files ─────────────────────────────
STATIC_URL  = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ── CORS ─────────────────────────────────────
CORS_ALLOW_ALL_ORIGINS = True   # tighten in production

# ── Django REST Framework ─────────────────────
REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': ('rest_framework.renderers.JSONRenderer',),
    'DEFAULT_PARSER_CLASSES':   ('rest_framework.parsers.JSONParser',),
}

# ── Celery ────────────────────────────────────
if os.getenv('USE_MEMORY_BROKER', 'False') == 'True':
    CELERY_BROKER_URL = 'memory://'
    # Tasks run synchronously if we use memory without a worker, but for local testing:
    CELERY_TASK_ALWAYS_EAGER = True
else:
    CELERY_BROKER_URL        = os.getenv('REDIS_URL', 'redis://redis:6379/0')

CELERY_RESULT_BACKEND    = CELERY_BROKER_URL
CELERY_ACCEPT_CONTENT    = ['json']
CELERY_TASK_SERIALIZER   = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE          = 'Asia/Kolkata'
CELERY_TASK_TRACK_STARTED = True

# Periodic beat schedule
CELERY_BEAT_SCHEDULE = {
    'process-pending-payouts': {
        'task':     'payouts.tasks.process_pending_payouts',
        'schedule': 10.0,   # every 10 seconds
    },
    'retry-stuck-payouts': {
        'task':     'payouts.tasks.retry_stuck_payouts',
        'schedule': 15.0,   # every 15 seconds
    },
}

# ── Logging ───────────────────────────────────
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {'format': '{asctime} {levelname} {name} {message}', 'style': '{'},
    },
    'handlers': {
        'console': {'class': 'logging.StreamHandler', 'formatter': 'verbose'},
    },
    'root': {'handlers': ['console'], 'level': 'INFO'},
    'loggers': {
        'payouts': {'handlers': ['console'], 'level': 'DEBUG', 'propagate': False},
    },
}
