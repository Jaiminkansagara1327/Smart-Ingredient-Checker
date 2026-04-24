from pathlib import Path
import os
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')

# Security Settings
_secret_key = os.getenv('SECRET_KEY')
if not _secret_key:
    import warnings
    warnings.warn("SECRET_KEY environment variable is not set! Using an insecure default for local dev only.")
    _secret_key = 'django-insecure-local-dev-only-do-not-use-in-production'
SECRET_KEY = _secret_key
DEBUG = os.getenv('DEBUG', 'False') == 'True'
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_simplejwt.token_blacklist',  # Required for ROTATE_REFRESH_TOKENS
    'corsheaders',
    'drf_spectacular',
    'accounts',
    'analyzer',
]

# ====================
# API Documentation
# ====================
SPECTACULAR_SETTINGS = {
    'TITLE': 'Ingrexa API',
    'DESCRIPTION': (
        'High-performance AI-driven API for smart ingredient analysis. '
        'Search products from OpenFoodFacts, analyze ingredients using GPT-4o-mini, '
        'OCR label scanning, scientific NOVA/Nutri-Score, and healthier alternative suggestions.'
    ),
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'CONTACT': {'name': 'Jaimin Kansagara', 'url': 'https://github.com/Jaiminkansagara1327'},
    'LICENSE': {'name': 'MIT'},
    'TAGS': [
        {'name': 'Analysis', 'description': 'Ingredient text and barcode analysis endpoints.'},
        {'name': 'Search', 'description': 'Product search via OpenFoodFacts.'},
        {'name': 'Healthier Alternatives', 'description': 'Find better product alternatives.'},
        {'name': 'Contact', 'description': 'Contact form submission.'},
        {'name': 'Auth', 'description': 'Authentication endpoints (JWT).'},
        {'name': 'User Data', 'description': 'User saved data: favorites and analysis history.'},
        {'name': 'Support', 'description': 'Public support/donation links.'},
        {'name': 'Health', 'description': 'Health check and monitoring.'},
    ],
}



ROOT_URLCONF = 'foodview_api.urls'

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

WSGI_APPLICATION = 'foodview_api.wsgi.application'


# Database Configuration
import dj_database_url

# Default to SQLite for local development
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Override with Database URL for Production (Render + Supabase Pooler)
# Using conn_max_age=0 because Supabase uses PgBouncer (transaction pooling mode),
# which is incompatible with persistent connections (conn_max_age > 0).
# DISABLE_SERVER_SIDE_CURSORS is also required for PgBouncer transaction pooling.
db_from_env = dj_database_url.config(
    conn_max_age=0,   # Required for PgBouncer / Supabase connection pooler
    ssl_require=True, # Force SSL for Supabase
)
if db_from_env:
    db_from_env['DISABLE_SERVER_SIDE_CURSORS'] = True
    DATABASES['default'].update(db_from_env)

# Static Files (Whitenoise)
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Allow Render Hosting
if not DEBUG:
    # Use ALLOWED_HOSTS env var in production. E.g. "myapp.onrender.com,www.myapp.com"
    render_hosts = os.getenv('RENDER_EXTERNAL_HOSTNAME', '')
    if render_hosts:
        ALLOWED_HOSTS += [render_hosts]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Needs to be right after SecurityMiddleware
    'corsheaders.middleware.CorsMiddleware',
    'analyzer.middleware.SecurityHeadersMiddleware',   # Custom: Security headers
    'analyzer.middleware.IPRateLimitMiddleware',       # Custom: Global rate limiting
    'analyzer.middleware.RequestValidationMiddleware', # Custom: Suspicious pattern detection
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# CORS Settings
CORS_ALLOWED_ORIGINS = os.getenv(
    'CORS_ALLOWED_ORIGINS',
    'http://localhost:3000,http://127.0.0.1:3000'
).split(',')
CORS_ALLOW_CREDENTIALS = True

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Email Settings
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True') == 'True'
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
CONTACT_EMAIL_RECIPIENT = os.getenv('CONTACT_EMAIL_RECIPIENT', EMAIL_HOST_USER)
EMAIL_TIMEOUT = 10  # 10 second timeout for SMTP connections

# Fallback to console for development
if not EMAIL_HOST_USER or not EMAIL_HOST_PASSWORD:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Production Security Settings
if not DEBUG:
    # HTTPS/SSL Settings
    SECURE_SSL_REDIRECT = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    
    # Cookie Security
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    CSRF_COOKIE_SECURE = True
    CSRF_COOKIE_HTTPONLY = True
    CSRF_COOKIE_SAMESITE = 'Lax'
    
    # Security Headers
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    
    # HSTS (HTTP Strict Transport Security)
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    
    # Content Security Policy
    CSP_DEFAULT_SRC = ("'self'",)
    CSP_SCRIPT_SRC = ("'self'", "'unsafe-inline'")
    CSP_STYLE_SRC = ("'self'", "'unsafe-inline'", "https://fonts.googleapis.com")
    CSP_FONT_SRC = ("'self'", "https://fonts.gstatic.com")
    CSP_IMG_SRC = ("'self'", "data:", "https:")
    CSP_CONNECT_SRC = ("'self'",)
    
else:
    # Development settings
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False

# REST Framework Security Settings
REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon':     '100/hour',   # 100 req/hr for anonymous users
        'user':     '1000/hour',  # Authenticated users default quota
        # Strict limits for credential endpoints (findings #6, #7, #12)
        # NOTE: DRF accepts only s/m/h/d as period identifiers.
        # The middleware layer enforces 5-per-15-min at the IP level;
        # these DRF throttles add a Redis-backed per-user-token limit.
        'login':    '5/hour',   # 5 attempts per hour per IP
        'register': '10/hour',  # Account creation limit
        'google':   '10/hour',  # OAuth flow limit
    },
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ],
    # Production: sanitise generic errors so stack traces are never exposed (finding #10)
    'EXCEPTION_HANDLER': 'accounts.exception_handler.safe_exception_handler',
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

# Request Size Limits (Prevent DoS attacks)
DATA_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5 MB
DATA_UPLOAD_MAX_NUMBER_FIELDS = 100

# Additional Security Settings
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
SECURE_CROSS_ORIGIN_OPENER_POLICY = 'same-origin'

# ============================================================
# SimpleJWT — short-lived tokens + rotation (findings #1-4)
# ============================================================
from datetime import timedelta
SIMPLE_JWT = {
    # Access token: 15 min — short enough to limit XSS blast radius
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),
    # Refresh token: 7 days with rotation (old token blacklisted on use)
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    # Sign with HS256 by default; upgrade to RS256 if you split auth service
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    # The access token is still sent in the Authorization header from the
    # frontend memory store — the refresh token is sent via HttpOnly cookie.
    'AUTH_HEADER_TYPES': ('Bearer',),
}

# ============================================================
# HttpOnly cookie settings for the refresh token (finding #1)
# ============================================================
# These are read by accounts/views.py when setting/reading the cookie.
JWT_AUTH_COOKIE          = 'ingrexa_refresh'   # cookie name
JWT_AUTH_COOKIE_SECURE   = not DEBUG           # HTTPS-only in prod
JWT_AUTH_COOKIE_HTTPONLY = True
JWT_AUTH_COOKIE_SAMESITE = 'Lax'              # allows cross-origin redirects
JWT_AUTH_COOKIE_MAX_AGE  = 7 * 24 * 60 * 60   # 7 days (matches refresh lifetime)

# Logging for Security Monitoring (Console only for development)
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django.security': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'analyzer': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}


# ============================================================
# Redis Cache (used for DRF throttling + general caching)
# ============================================================
# CACHE_URL example: redis://localhost:6379/1
# In production set REDIS_URL in .env  (Render / Railway give you one free)
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_URL,
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            # Silently ignore Redis errors so the app degrades gracefully
            # if Redis is temporarily unavailable.
            "IGNORE_EXCEPTIONS": True,
        },
        "TIMEOUT": 300,  # Default cache TTL: 5 minutes
        "KEY_PREFIX": "ingrexa",
    }
}

# Use Redis for Django sessions too (optional but faster than DB sessions)
# SESSION_ENGINE = "django.contrib.sessions.backends.cache"
# SESSION_CACHE_ALIAS = "default"

# ============================================================
# Celery Configuration
# ============================================================
# Broker  = Redis DB 0  (task queue)
# Backend = Redis DB 1  (task results / polling)
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")

# Serialize tasks as JSON (safer than pickle)
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TIMEZONE = TIME_ZONE
CELERY_ENABLE_UTC = True

# Keep task results in Redis for 1 hour, then auto-expire
CELERY_TASK_RESULT_EXPIRES = 3600

# If a task is soft-time-limited (raises SoftTimeLimitExceeded), kill
# it after 5 minutes maximum so workers never get permanently stuck.
CELERY_TASK_SOFT_TIME_LIMIT = 240  # 4 min soft limit
CELERY_TASK_TIME_LIMIT = 300      # 5 min hard kill

# Only acknowledge the task AFTER it finishes (safer against worker crashes)
CELERY_TASK_ACKS_LATE = True
CELERY_TASK_REJECT_ON_WORKER_LOST = True

# Prefetch 1 task at a time (prevents memory hogging with heavy ML tasks)
CELERY_WORKER_PREFETCH_MULTIPLIER = 1

# Task routing — keep analysis tasks in a dedicated queue so they don't
# block lightweight email tasks.
CELERY_TASK_ROUTES = {
    "analyzer.tasks.analyze_ingredients_task": {"queue": "analysis"},
    "analyzer.tasks.send_contact_email_task": {"queue": "email"},
}

