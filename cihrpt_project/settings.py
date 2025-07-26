"""
Django settings for CIHRPT (CIHR Projects Tracker) project.
"""

import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Import environment configuration (production)
try:
    from decouple import config
    import dj_database_url
    HAS_DECOUPLE = True
except ImportError:
    HAS_DECOUPLE = False

# SECURITY WARNING: keep the secret key used in production secret!
if HAS_DECOUPLE:
    SECRET_KEY = config('SECRET_KEY', default='django-insecure-your-secret-key-here-change-in-production')
    DEBUG = config('DEBUG', default=True, cast=bool)
    ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1,cihrpt.xeradb.com').split(',')
else:
    SECRET_KEY = 'django-insecure-your-secret-key-here-change-in-production'
    DEBUG = True
    ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'cihrpt.xeradb.com']

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'tracker',
    'rest_framework',
]

MIDDLEWARE = [
    'django.middleware.cache.UpdateCacheMiddleware',  # Must be first
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.cache.FetchFromCacheMiddleware',  # Must be last
]

# Cache middleware settings
CACHE_MIDDLEWARE_ALIAS = 'default'
CACHE_MIDDLEWARE_SECONDS = config('CACHE_MIDDLEWARE_SECONDS', default=600, cast=int) if HAS_DECOUPLE else 300
CACHE_MIDDLEWARE_KEY_PREFIX = 'cihrpt'

ROOT_URLCONF = 'cihrpt_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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

WSGI_APPLICATION = 'cihrpt_project.wsgi.application'

# Database
if HAS_DECOUPLE:
    # Production database configuration
    DATABASES = {
        'default': dj_database_url.config(
            default=config('DATABASE_URL', default=f'sqlite:///{BASE_DIR}/db.sqlite3')
        )
    }
    
    # Database connection optimization for production
    DATABASES['default'].update({
        'CONN_MAX_AGE': config('DB_CONN_MAX_AGE', default=60, cast=int),
        'OPTIONS': {
            'connect_timeout': 20,
        }
    })
else:
    # Development database configuration
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

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
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'

if HAS_DECOUPLE:
    # Production static files configuration
    STATIC_ROOT = config('STATIC_ROOT', default=str(BASE_DIR / 'staticfiles'))
    MEDIA_ROOT = config('MEDIA_ROOT', default=str(BASE_DIR / 'media'))
    MEDIA_URL = '/media/'
else:
    # Development static files configuration
    STATIC_ROOT = BASE_DIR / 'staticfiles'

STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Caching Configuration
if HAS_DECOUPLE:
    # Production: Redis cache
    CACHES = {
        'default': {
            'BACKEND': config('CACHE_BACKEND', default='django.core.cache.backends.redis.RedisCache'),
            'LOCATION': config('REDIS_URL', default='redis://127.0.0.1:6379/1'),
            'KEY_PREFIX': 'cihrpt',
            'TIMEOUT': config('CACHE_TIMEOUT', default=300, cast=int),
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                'CONNECTION_POOL_KWARGS': {
                    'max_connections': 50,
                    'retry_on_timeout': True,
                },
                'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',
                'SERIALIZER': 'django_redis.serializers.pickle.PickleSerializer',
            }
        }
    }
    
    # Session storage in Redis for production
    SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
    SESSION_CACHE_ALIAS = 'default'
    SESSION_COOKIE_AGE = config('SESSION_COOKIE_AGE', default=3600, cast=int)  # 1 hour
else:
    # Development: Local memory cache
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'cihrpt-cache',
            'TIMEOUT': 300,
            'OPTIONS': {
                'MAX_ENTRIES': 1000,
                'CULL_FREQUENCY': 3,
            }
        }
    }

# Proxy settings for production
if HAS_DECOUPLE:
    USE_X_FORWARDED_HOST = config('USE_X_FORWARDED_HOST', default=False, cast=bool)
    USE_X_FORWARDED_PORT = config('USE_X_FORWARDED_PORT', default=False, cast=bool)

# Security settings for production
if HAS_DECOUPLE and not DEBUG:
    SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=False, cast=bool)  # Nginx handles this
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_HSTS_SECONDS = config('SECURE_HSTS_SECONDS', default=31536000, cast=int)
    SECURE_HSTS_INCLUDE_SUBDOMAINS = config('SECURE_HSTS_INCLUDE_SUBDOMAINS', default=True, cast=bool)
    SECURE_HSTS_PRELOAD = config('SECURE_HSTS_PRELOAD', default=True, cast=bool)
    SECURE_CONTENT_TYPE_NOSNIFF = config('SECURE_CONTENT_TYPE_NOSNIFF', default=True, cast=bool)
    SECURE_BROWSER_XSS_FILTER = config('SECURE_BROWSER_XSS_FILTER', default=True, cast=bool)

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# CIHRPT specific settings
if HAS_DECOUPLE:
    CIHRPT_DATA_DIR = Path(config('CIHRPT_DATA_DIR', default=str(BASE_DIR / 'cihr_projects_jsons')))
    CIHRPT_CSV_FILE = Path(config('CIHRPT_CSV_FILE', default=str(BASE_DIR / 'cihr_projects.csv')))
else:
    CIHRPT_DATA_DIR = BASE_DIR / 'cihr_projects_jsons'
    CIHRPT_CSV_FILE = BASE_DIR / 'cihr_projects.csv'

# REST Framework configuration
REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 50,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
}

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': str(BASE_DIR / 'cihrpt.log'),
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
