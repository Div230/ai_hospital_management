"""
Django settings for AI Hospital Management System.
"""
from pathlib import Path
from datetime import timedelta
from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=True, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1,testserver').split(',')

# Render (and similar platforms) sit behind an HTTPS-terminating proxy —
# without these, Django can't tell the original request was HTTPS, which
# breaks CSRF validation on the admin login and any POST from a browser.
CSRF_TRUSTED_ORIGINS = [f'https://{host}' for host in ALLOWED_HOSTS if host not in ('localhost', '127.0.0.1', 'testserver')]
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

INSTALLED_APPS = [
    'daphne',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # third party
    'channels',
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'django_filters',
    'drf_spectacular',

    # local apps
    'accounts',
    'core',
    'patients',
    'doctors',
    'hospital_admin',
    'laboratory',
    'pharmacy',
    'appointments',
    'ai_assistant',
    'notifications',
    'django_celery_beat',
    'realtime',
    'prescription_reader',
]

ASGI_APPLICATION = 'config.asgi.application'

# In-memory by default so real-time features (ambulance tracking, video call
# signaling) work out of the box with zero extra setup in a single-process
# demo run. Switch to Redis for production / multi-process deployments by
# setting USE_REDIS_CHANNEL_LAYER=True (needs Redis running).
if config('USE_REDIS_CHANNEL_LAYER', default=False, cast=bool):
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels_redis.core.RedisChannelLayer',
            'CONFIG': {'hosts': [config('CELERY_BROKER_URL', default='redis://localhost:6379/0')]},
        }
    }
else:
    CHANNEL_LAYERS = {
        'default': {'BACKEND': 'channels.layers.InMemoryChannelLayer'},
    }

AUTH_USER_MODEL = 'accounts.User'

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
    'core.middleware.AuditLogMiddleware',
]

CORS_ALLOWED_ORIGINS = config(
    'CORS_ALLOWED_ORIGINS',
    default='http://localhost:3000,http://127.0.0.1:3000'
).split(',')
CORS_ALLOW_CREDENTIALS = True

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# Database — Postgres in prod (via DATABASE_URL on Render), SQLite fallback for quick local demo
import dj_database_url

if config('USE_SQLITE', default=False, cast=bool):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
elif config('DATABASE_URL', default=''):
    DATABASES = {
        'default': dj_database_url.config(
            default=config('DATABASE_URL'),
            conn_max_age=600,
            ssl_require=config('DB_SSL_REQUIRE', default=False, cast=bool),
        )
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': config('DB_NAME', default='healthcare_db'),
            'USER': config('DB_USER', default='postgres'),
            'PASSWORD': config('DB_PASSWORD'),
            'HOST': config('DB_HOST', default='localhost'),
            'PORT': config('DB_PORT', default='5432'),
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'EXCEPTION_HANDLER': 'core.exceptions.custom_exception_handler',
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=30),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'AI Hospital Management System API',
    'DESCRIPTION': 'AI-powered multi-role healthcare platform (Patient, Doctor, Hospital Admin, Lab, Pharmacy)',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
}

# --- Third-party integrations (demo mode uses console/log fallback) ---
GEMINI_API_KEY = config('GEMINI_API_KEY', default='')
GROQ_API_KEY = config('GROQ_API_KEY', default='')
TWILIO_ACCOUNT_SID = config('TWILIO_ACCOUNT_SID', default='')
TWILIO_AUTH_TOKEN = config('TWILIO_AUTH_TOKEN', default='')
TWILIO_WHATSAPP_NUMBER = config('TWILIO_WHATSAPP_NUMBER', default='')
TWILIO_SMS_NUMBER = config('TWILIO_SMS_NUMBER', default='')

# --- Web Push (VAPID) ---
# Demo keypair pre-filled below so push notifications work out of the box;
# generate your own for a real deployment (see README).
VAPID_PUBLIC_KEY = config(
    'VAPID_PUBLIC_KEY',
    default='',
)
VAPID_PRIVATE_KEY = config(
    'VAPID_PRIVATE_KEY',
    default='',
)
VAPID_ADMIN_EMAIL = config('VAPID_ADMIN_EMAIL', default='admin@aihms.example.test')

EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=False, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')

# --- Celery (background jobs: scheduled reminders, notifications) ---
# Requires Redis running (redis-server) for actual async execution.
# Demo mode: if Redis isn't reachable, these tasks simply won't fire —
# everything else in the app works fine without Celery running.
CELERY_BROKER_URL = config('CELERY_BROKER_URL', default='redis://localhost:6379/0')
CELERY_RESULT_BACKEND = config('CELERY_RESULT_BACKEND', default='redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

import os

_log_dir = BASE_DIR / 'logs'
_handlers_available = ['console']
_logging_handlers_config = {
    'console': {'class': 'logging.StreamHandler', 'formatter': 'verbose'},
}

# Only add the file handler if the logs directory actually exists and is
# writable (local dev). Render's filesystem doesn't have this folder unless
# we create it, and an empty folder can't be committed to Git anyway.
if os.path.isdir(_log_dir):
    _logging_handlers_config['file'] = {
        'class': 'logging.FileHandler',
        'filename': _log_dir / 'app.log',
        'formatter': 'verbose',
    }
    _handlers_available.append('file')

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {'format': '[{asctime}] {levelname} {name}: {message}', 'style': '{'},
    },
    'handlers': _logging_handlers_config,
    'root': {'handlers': ['console'], 'level': 'INFO'},
    'loggers': {
        'django': {'handlers': ['console'], 'level': 'INFO', 'propagate': False},
        'healthcare': {'handlers': _handlers_available, 'level': 'DEBUG', 'propagate': False},
    },
}

# Operator-owned configuration. No external provider receives data by default.
EXTERNAL_AI_ENABLED = config('EXTERNAL_AI_ENABLED', default=False, cast=bool)
OUTBOUND_NOTIFICATIONS_ENABLED = config('OUTBOUND_NOTIFICATIONS_ENABLED', default=False, cast=bool)
OUTBOUND_WEBHOOKS_ENABLED = False  # Re-enable only after endpoint/tenant security review.
TESSERACT_CMD = config('TESSERACT_CMD', default='tesseract')
VISION_BASE_URL = config('VISION_BASE_URL', default='')
VISION_API_KEY = config('VISION_API_KEY', default='')
VISION_MODEL = config('VISION_MODEL', default='')
VISION_IS_EXTERNAL = config('VISION_IS_EXTERNAL', default=True, cast=bool)
MAX_UPLOAD_BYTES = 10 * 1024 * 1024
DATA_UPLOAD_MAX_MEMORY_SIZE = MAX_UPLOAD_BYTES + 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 2 * 1024 * 1024
FILE_UPLOAD_PERMISSIONS = 0o600
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@aihms.example.test')
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    if len(SECRET_KEY) < 50:
        raise ValueError('Production SECRET_KEY must contain at least 50 characters.')

CACHES = {'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}}
if config('USE_REDIS_CHANNEL_LAYER', default=False, cast=bool):
    CACHES = {'default': {'BACKEND': 'django.core.cache.backends.redis.RedisCache', 'LOCATION': CELERY_BROKER_URL}}
REST_FRAMEWORK['DEFAULT_THROTTLE_CLASSES'] = [
    'rest_framework.throttling.AnonRateThrottle', 'rest_framework.throttling.UserRateThrottle',
]
REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'] = {'anon': '40/min', 'user': '240/min', 'login': '5/min'}
CELERY_TASK_ACKS_LATE = True
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
CELERY_BROKER_TRANSPORT_OPTIONS = {'visibility_timeout': 240}
CELERY_BEAT_SCHEDULE = {
    'recover-prescription-jobs': {'task': 'prescription_reader.tasks.dispatch_pending', 'schedule': 30.0},
}

SIMPLE_JWT['CHECK_REVOKE_TOKEN'] = True
CELERY_TASK_PUBLISH_RETRY = False
CELERY_BROKER_CONNECTION_TIMEOUT = 2
