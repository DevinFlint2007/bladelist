from pathlib import Path
from decouple import config
import dj_database_url
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# --- BRANDING SETTINGS ---
SITE_NAME = 'Hype Advertising'

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', cast=bool, default=False)

# Combined ALLOWED_HOSTS for both local and Render
ALLOWED_HOSTS = [
    'hype-advertising.onrender.com', 
    '.onrender.com', 
    'localhost', 
    '127.0.0.1', 
    '.bladelist.gg'
]

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'main_site.apps.MainSiteConfig',  
    'api.apps.ApiConfig',
    'bladebotlist', 
    'django_hosts',
    'rest_framework',
    'rest_framework.authtoken',
]

MIDDLEWARE = [
    'django_hosts.middleware.HostsRequestMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django_hosts.middleware.HostsResponseMiddleware',
]

ROOT_URLCONF = 'bladebotlist.urls'
ROOT_HOSTCONF = 'bladebotlist.hosts'
DEFAULT_HOST = "www"

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

WSGI_APPLICATION = 'bladebotlist.wsgi.application'

# --- DATABASE CONFIGURATION ---
# Fixed to handle Port 22552 and SSL requirements for Aiven
DATABASES = {
    'default': dj_database_url.config(
        default=config('DATABASE_URL'),
        conn_max_age=600,
        conn_health_checks=True,
        ssl_require=True
    )
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': ('rest_framework.permissions.IsAuthenticated',),
    'DEFAULT_AUTHENTICATION_CLASSES': ('rest_framework.authentication.TokenAuthentication',),
    'DEFAULT_RENDERER_CLASSES': ('rest_framework.renderers.JSONRenderer',)
}

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'assets'
STATICFILES_DIRS = [BASE_DIR / 'static']

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Sensitive variables
OAUTH_CLIENT_ID = config('OAUTH_CLIENT_ID')
OAUTH_CLIENT_SECRET = config('OAUTH_CLIENT_SECRET')
ENCRYPTION_SALT = config('ENCRYPTION_SALT')
ENCRYPTION_ITERATION = config('ENCRYPTION_ITERATION', cast=int, default=100000)
DISCORD_API_TOKEN = config('DISCORD_API_TOKEN')
AUTH_HANDLER_URL = config('AUTH_HANDLER_URL')
AUTH_CALLBACK_URL = config('AUTH_CALLBACK_URL')
LOG_CHANNEL_ID = config('LOG_CHANNEL_ID')
