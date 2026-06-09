import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-change-this-in-production')
DEBUG = os.getenv('DEBUG', 'True') == 'True'
ALLOWED_HOSTS_RAW = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1,.onrender.com')
ALLOWED_HOSTS = [host.strip() for host in ALLOWED_HOSTS_RAW.split(',') if host.strip()]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Сторонние приложения
    'crispy_forms',
    'crispy_bootstrap5',
    # Наши приложения
    'products',
    'orders',
    'accounts',
    'django_extensions'
]
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'accounts.middleware.EmailVerificationMiddleware',  # ← ИСПРАВЛЕНО
]

ROOT_URLCONF = 'config.urls'

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

WSGI_APPLICATION = 'config.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'ru-ru'
TIME_ZONE = 'Europe/Moscow'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Настройки crispy-forms
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

# Настройки авторизации
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'
LOGIN_URL = 'login'


# ============================================
# НАСТРОЙКИ ПЛАТЁЖНОЙ СИСТЕМЫ (ЮMoney)
# ============================================
YOOMONEY_WALLET = os.getenv('YOOMONEY_WALLET', '')
YOOMONEY_SECRET_KEY = os.getenv('YOOMONEY_SECRET_KEY', '')
YOOMONEY_TEST_MODE = os.getenv('YOOMONEY_TEST_MODE', 'True')  # ← Важно: строка 'True'



# ============================================
# НАСТРОЙКИ N8N КОНСУЛЬТАНТА
# ============================================
# Точный URL вашего вебхука (с UUID)
N8N_WEBHOOK_URL = os.getenv(
    'N8N_WEBHOOK_URL', 
    'https://ridozororoo.beget.app/webhook/751260db-047d-42c3-a8a5-e6f6fd7da5ff/chat'
)
N8N_TIMEOUT = int(os.getenv('N8N_TIMEOUT', '30'))


# ============================================
# НАСТРОЙКИ ОТПРАВКИ ПИСЕМ (EMAIL)
# ============================================
# Для демо: письма выводятся в консоль сервера
# Для продакшена: раскомментируй блок SMTP ниже

# 🔹 Консольный бэкенд (демо-режим)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# 🔹 SMTP-бэкенд (продакшен — раскомментируй и настрой)
EMAIL_BACKEND = os.getenv('EMAIL_BACKEND')
EMAIL_HOST = os.getenv('EMAIL_HOST')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS') == 'True'
EMAIL_USE_SSL = os.getenv('EMAIL_USE_SSL') == 'True'
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', EMAIL_HOST_USER)

# 🔹 Общие настройки
EMAIL_SUBJECT_PREFIX = '[Магазин Рыбок] '
EMAIL_TIMEOUT = 30  # секунд

# 🔹 Настройки кодов верификации
VERIFICATION_CODE_LENGTH = 6
VERIFICATION_CODE_EXPIRE_MINUTES = 10  # код действителен 10 минут

# Получите бесплатный ключ: https://developer.tech.yandex.ru/
YANDEX_MAPS_API_KEY = os.getenv('YANDEX_MAPS_API_KEY', '')

# ============================================
# ПРОДАКШЕН-НАСТРОЙКИ (для Beget)
# ============================================
DEBUG = os.getenv('DEBUG', 'False') == 'True'  # Обязательно False!
ALLOWED_HOSTS = ['x95142ym.beget.tech', 'www.x95142ym.beget.tech', 'localhost', '127.0.0.1']

# Статика и медиа для продакшена
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATIC_URL = '/static/'

MEDIA_ROOT = BASE_DIR / 'media'
MEDIA_URL = '/media/'

# CSRF_TRUSTED_ORIGINS: обязательно для работы форм и AJAX на HTTPS-доменах
CSRF_TRUSTED_ORIGINS_RAW = os.getenv('CSRF_TRUSTED_ORIGINS', 'https://*.onrender.com')
CSRF_TRUSTED_ORIGINS = [origin.strip() for origin in CSRF_TRUSTED_ORIGINS_RAW.split(',') if origin.strip()]

# Безопасность
CSRF_TRUSTED_ORIGINS = ['http://x95142ym.beget.tech/']
SECURE_SSL_REDIRECT = False  # Beget сам редиректит
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Для Render.com
import dj_database_url
DATABASES = {
    'default': dj_database_url.config(default='sqlite:///db.sqlite3')
}

# Static files
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

if not DEBUG:
    SECURE_SSL_REDIRECT = False  # Render сам обрабатывает HTTPS
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'