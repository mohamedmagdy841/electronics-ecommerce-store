from pathlib import Path
import os
from dotenv import load_dotenv
from datetime import timedelta
# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv()
# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG') == 'True'

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS').split(',')
CSRF_TRUSTED_ORIGINS = os.environ.get(
    'CSRF_TRUSTED_ORIGINS'
).split(',')

# Application definition

INSTALLED_APPS = [
    "unfold",
    "unfold.contrib.filters",
    "unfold.contrib.forms",
    "unfold.contrib.inlines",
    "unfold.contrib.import_export",
    
    
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    'rest_framework',
    'rest_framework_simplejwt.token_blacklist',
    'djoser',
    'social_django',
    'import_export',
    "debug_toolbar",
    'django_filters',
    'drf_spectacular',
    "corsheaders",
    
    'accounts',
    'products',
    'cart',
    'orders',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    "corsheaders.middleware.CorsMiddleware",
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'social_django.middleware.SocialAuthExceptionMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware'
]

ROOT_URLCONF = 'backend.urls'

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

WSGI_APPLICATION = 'backend.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': BASE_DIR / 'db.sqlite3',
#     }
# }

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('POSTGRES_DB'),
        'USER': os.environ.get('POSTGRES_USER'),
        'PASSWORD': os.environ.get('POSTGRES_PASSWORD'),
        'HOST': os.environ.get('POSTGRES_HOST'),
        'PORT': os.environ.get('POSTGRES_PORT'),
    }
}



# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Egypt'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'mediafiles'

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_USER_MODEL = 'accounts.User'

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('EMAIL_HOST')
EMAIL_PORT = os.environ.get('EMAIL_PORT')
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
EMAIL_USE_TLS = True


AUTHENTICATION_BACKENDS = [
    'social_core.backends.google.GoogleOAuth2',
    'social_core.backends.github.GithubOAuth2',
    'accounts.backends.EmailOrPhoneBackend',
    'django.contrib.auth.backends.ModelBackend',
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'backend.throttling.BurstRateThrottle',
        'backend.throttling.SustainedRateThrottle',
        'rest_framework.throttling.ScopedRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '20/minute',
        'burst': '60/minute',
        'sustained': '2000/day',
        'login': '5/minute',
        'register': '5/minute',
        'send_otp': '3/minute',
        'verify_otp': '5/minute',
    },
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'ElectroShop API',
    'DESCRIPTION': 'API for the ElectroShop project',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,
    'SECURITY': [{'BearerAuth': []}], 
    'SWAGGER_UI_SETTINGS': {'persistAuthorization': True},
    'TAGS': [
        {'name': 'Accounts', 'description': 'Auth, registration, OTP'},
        {'name': 'Products', 'description': 'Product catalog & variants'},
        {'name': 'Cart', 'description': 'Cart operations for guests & users'},
        {'name': 'Orders', 'description': 'Checkout & order management'},
        {'name': 'Wishlist', 'description': 'User wishlist'},
        {'name': 'Categories', 'description': 'Browse categories & subcategories'},
        {'name': 'Brands', 'description': 'Brand directory'},
        {'name': 'Home', 'description': 'Homepage widgets (latest, weekly deal)'},
        {'name': 'Reviews', 'description': 'Product review threads'},
    ],
    
    
    'POSTPROCESSING_HOOKS': [
        'drf_spectacular.hooks.postprocess_schema_enums',
        'backend.schema_hooks.move_auth_to_accounts',
    ],
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=2),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'AUTH_HEADER_TYPES': ('Bearer',),
    
    
    # Additional security settings
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': False,
}

DJOSER = {
    'LOGIN_FIELD': 'email',
    'USER_CREATE_PASSWORD_RETYPE': True,
    'SEND_CONFIRMATION_EMAIL':True,
    'PASSWORD_CHANGED_EMAIL_CONFIRMATION':True,
    'SERIALIZERS': {
        'user_create': 'accounts.serializers.CustomUserCreateSerializer',
        'current_user': 'accounts.serializers.CustomUserSerializer',
    },
    'TOKEN_MODEL': None,
    'SEND_ACTIVATION_EMAIL': True,
    'PASSWORD_RESET_CONFIRM_URL': 'password-reset-confirm/{uid}/{token}',
    'ACTIVATION_URL': 'activate/{uid}/{token}',
    'DOMAIN': '127.0.0.1:8000',
    'SITE_NAME': 'ElectroShop',
    "EMAIL": {
        'activation': 'accounts.email.ActivationEmail',
        'confirmation': 'accounts.email.ConfirmationEmail',
        'password_reset': 'accounts.email.PasswordResetEmail',
        'password_changed_confirmation': 'accounts.email.PasswordChangedConfirmationEmail',
    },
    'SOCIAL_AUTH_ALLOWED_REDIRECT_URIS': [
        'http://localhost:3000/social/callback/',
    ],
    'SOCIAL_AUTH_TOKEN_STRATEGY': 'djoser.social.token.jwt.TokenStrategy',
}

INTERNAL_IPS = [
    "127.0.0.1",
    "localhost"
]

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://global-redis:6379/0',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# Google OAuth2 keys
SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = os.environ.get('SOCIAL_AUTH_GOOGLE_OAUTH2_KEY')
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = os.environ.get('SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET')

# Github OAuth2 keys
SOCIAL_AUTH_GITHUB_KEY = os.environ.get('SOCIAL_AUTH_GITHUB_KEY')
SOCIAL_AUTH_GITHUB_SECRET = os.environ.get('SOCIAL_AUTH_GITHUB_SECRET')

# Required by social-auth-app-django
SOCIAL_AUTH_JSONFIELD_ENABLED = True
LOGIN_REDIRECT_URL = '/'

SOCIAL_AUTH_GITHUB_SCOPE = ['user:email']

TWILIO_SID = os.environ.get('TWILIO_SID')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')

# Frontend URL
FRONTEND_URL = os.environ.get('FRONTEND_URL', 'http://localhost:3000')

# Stripe keys
STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY')
STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY')
STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET')

# Paypal keys
PAYPAL_CLIENT_ID = os.environ.get('PAYPAL_CLIENT_ID')
PAYPAL_CLIENT_SECRET = os.environ.get('PAYPAL_CLIENT_SECRET')
PAYPAL_API_BASE = os.environ.get('PAYPAL_API_BASE')
PAYPAL_CURRENCY = os.environ.get('PAYPAL_CURRENCY')
PAYMENT_RETURN_URL = FRONTEND_URL + "/payment/success"
PAYMENT_CANCEL_URL = FRONTEND_URL + "/payment/cancel"

# Paymob keys
PAYMOB_API_KEY = os.environ.get('PAYMOB_API_KEY')
PAYMOB_API_BASE = os.environ.get('PAYMOB_API_BASE')
PAYMOBE_PUBLIC_KEY = os.environ.get('PAYMOBE_PUBLIC_KEY')
PAYMOB_CURRENCY = os.environ.get('PAYMOB_CURRENCY')
PAYMOB_INTEGRATIONS = os.getenv("PAYMOB_INTEGRATIONS", "")
PAYMOB_INTEGRATIONS = PAYMOB_INTEGRATIONS.split(",") if PAYMOB_INTEGRATIONS else []

# Security headers
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"

# SSL / HTTPS
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "True") == "True"
CSRF_COOKIE_SECURE = os.getenv("CSRF_COOKIE_SECURE", "True") == "True"
SECURE_SSL_REDIRECT = os.getenv("SECURE_SSL_REDIRECT", "True") == "True"

# HSTS (enable once you confirm HTTPS is working everywhere)
SECURE_HSTS_SECONDS = int(os.getenv("SECURE_HSTS_SECONDS", "31536000"))  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = os.getenv("SECURE_HSTS_INCLUDE_SUBDOMAINS", "True") == "True"
SECURE_HSTS_PRELOAD = os.getenv("SECURE_HSTS_PRELOAD", "True") == "True"

# CORS
CORS_ALLOWED_ORIGINS = os.getenv("CORS_ALLOWED_ORIGINS", "").split(",")
CORS_ALLOW_CREDENTIALS = True

# Required if using HttpOnly cookies with cross-site frontend
SESSION_COOKIE_SAMESITE = os.getenv("SESSION_COOKIE_SAMESITE", "None")
SESSION_COOKIE_HTTPONLY = True

CSRF_COOKIE_SAMESITE = os.getenv("CSRF_COOKIE_SAMESITE", "None") 
CSRF_COOKIE_HTTPONLY = True

SECURE_CROSS_ORIGIN_OPENER_POLICY = "same-origin"

# Logs
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {"class": "logging.StreamHandler"},
    },
    "root": {
        "handlers": ["console"],
        "level": "WARNING",
    },
    "loggers": {
        "django.security": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
        "django.request": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
    },
}
