# core/settings.py
"""Configuración principal del proyecto ERP Django — W01 a W18."""

import os
import sys
from datetime import timedelta
from pathlib import Path

import environ
from celery.schedules import crontab

# ── 1. Directorio Base ──────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent

# ── 2. Variables de Entorno ────────────────────────────────────────────────
env = environ.Env(DEBUG=(bool, True))
environ.Env.read_env(BASE_DIR / '.env')

# Clave secreta con fallback seguro y protección .strip()
SECRET_KEY = (os.getenv('SECRET_KEY') or env('SECRET_KEY', default='django-insecure-dev-key-w15-segura')).strip()
DEBUG = env.bool('DEBUG', default=True)
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['localhost', '127.0.0.1', '*'])

# ── 3. Aplicaciones Instaladas ─────────────────────────────────────────────
INSTALLED_APPS = [
    # Jazzmin DEBE ir antes de django.contrib.admin
    'jazzmin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',  # Requerido por django-allauth

    # Apps de Terceros
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'rest_framework',
    'rest_framework.authtoken',
    'django_filters',
    'whitenoise.runserver_nostatic',
    'anymail',

    # Apps del ERP
    'clientes',
    'proveedores',
    'productos',
    'ventas',
    'reportes',
    'configuracion',
    'catalogo',
]

# ── 4. Middlewares ──────────────────────────────────────────────────────────
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # WhiteNoise en posición 1
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',  # Middleware de Allauth
]

ROOT_URLCONF = 'core.urls'

# ── 5. Templates y Context Processors ───────────────────────────────────────
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
                # Context processor del carrito de compras (W13)
                'catalogo.context_processors.carrito_info',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'

# ── 6. Base de Datos ────────────────────────────────────────────────────────
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# ── 7. Validación de Contraseñas ───────────────────────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ── 8. Internacionalización ────────────────────────────────────────────────
LANGUAGE_CODE = 'es-mx'
TIME_ZONE = 'America/Mexico_City'
USE_I18N = True
USE_TZ = True

# ── 9. Archivos Estáticos y Media ──────────────────────────────────────────
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ── 10. Autenticación y Allauth ────────────────────────────────────────────
LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/productos/'
LOGOUT_REDIRECT_URL = '/'

SITE_ID = 1

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

ACCOUNT_LOGIN_METHODS = {'username'}
ACCOUNT_EMAIL_REQUIRED = False
ACCOUNT_EMAIL_VERIFICATION = 'none'
ACCOUNT_LOGOUT_ON_GET = True
ACCOUNT_SESSION_REMEMBER = True

# ── 11. Django REST Framework ──────────────────────────────────────────────
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}

# ── 12. Configuración de Stripe ─────────────────────────────────────────────
STRIPE_SECRET_KEY = (os.getenv('STRIPE_SECRET_KEY') or env('STRIPE_SECRET_KEY', default='sk_test_placeholder')).strip()
STRIPE_PUBLISHABLE_KEY = (os.getenv('STRIPE_PUBLISHABLE_KEY') or env('STRIPE_PUBLISHABLE_KEY', default='pk_test_placeholder')).strip()
STRIPE_WEBHOOK_SECRET = (os.getenv('STRIPE_WEBHOOK_SECRET') or env('STRIPE_WEBHOOK_SECRET', default='whsec_placeholder')).strip()

# ── 13. Tema Jazzmin ────────────────────────────────────────────────────────
JAZZMIN_SETTINGS = {
    'site_title': 'ERP Django',
    'site_header': 'ERP UTEC Celaya',
    'site_brand': '📦 ERP Django',
    'welcome_sign': 'Bienvenido al Sistema ERP · UTEC Celaya',
    'copyright': 'MC. Román Fernando López González · UTEC Celaya',
    'site_icon': None,
    'site_logo': None,
    'search_model': ['clientes.Cliente', 'productos.Producto'],
    'topmenu_links': [
        {'name': 'Inicio ERP', 'url': '/', 'new_window': False},
        {'name': 'Productos', 'url': '/productos/'},
        {'name': 'Clientes', 'url': '/clientes/'},
        {'name': 'Ventas', 'url': '/ventas/'},
        {'name': 'Catálogo', 'url': '/catalogo/'},
    ],
    'usermenu_links': [
        {'name': 'Ver ERP', 'url': '/', 'new_window': False},
    ],
    'order_with_respect_to': [
        'clientes',
        'proveedores',
        'productos',
        'ventas',
        'configuracion',
        'auth',
    ],
    'icons': {
        'auth': 'fas fa-users-cog',
        'auth.user': 'fas fa-user',
        'auth.Group': 'fas fa-users',
        'clientes.Cliente': 'fas fa-user-tie',
        'proveedores.Proveedor': 'fas fa-truck',
        'productos.Categoria': 'fas fa-tags',
        'productos.Producto': 'fas fa-box',
        'ventas.Venta': 'fas fa-file-invoice-dollar',
        'ventas.DetalleVenta': 'fas fa-list',
        'ventas.Pedido': 'fas fa-shopping-cart',
        'configuracion.ConfiguracionERP': 'fas fa-cogs',
    },
    'default_icon_parents': 'fas fa-folder',
    'default_icon_children': 'fas fa-circle',
    'related_modal_active': True,
    'custom_css': 'erp_custom.css',
    'show_sidebar': True,
    'navigation_expanded': True,
    'hide_apps': [],
    'hide_models': [],
    'changeform_format': 'horizontal_tabs',
    'language_chooser': False,
}

JAZZMIN_UI_TWEAKS = {
    'navbar_small_text': False,
    'footer_small_text': False,
    'body_small_text': False,
    'brand_small_text': False,
    'brand_colour': 'navbar-dark',
    'accent': 'accent-navy',
    'navbar': 'navbar-dark',
    'no_navbar_border': False,
    'navbar_fixed': True,
    'layout_boxed': False,
    'footer_fixed': False,
    'sidebar_fixed': True,
    'sidebar': 'sidebar-dark-navy',
    'sidebar_nav_small_text': False,
    'sidebar_disable_expand': False,
    'sidebar_nav_child_indent': True,
    'sidebar_nav_compact_style': False,
    'sidebar_nav_legacy_style': False,
    'sidebar_nav_flat_style': False,
    'theme': 'default',
    'dark_mode_theme': None,
    'button_classes': {
        'primary': 'btn-primary',
        'secondary': 'btn-secondary',
        'info': 'btn-info',
        'warning': 'btn-warning',
        'danger': 'btn-danger',
        'success': 'btn-success',
    },
}

# ── 14. Celery — Cola de tareas asíncronas ──────────────────────────────────
# En Render: define REDIS_URL en Environment con la Internal Connection URL
# del Key Value. En local usa el valor por defecto (Redis en localhost).
REDIS_URL = env('REDIS_URL', default='redis://localhost:6379/0')
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL

# Arranque embebido de Celery dentro del servicio web (lo usa core/wsgi.py).
# En Render: true/true y gunicorn con --workers 1.
# En local (worker y beat en terminales aparte): déjalos en False.
CELERY_EMBEDDED_WORKER = env.bool('CELERY_EMBEDDED_WORKER', default=False)
CELERY_EMBEDDED_BEAT = env.bool('CELERY_EMBEDDED_BEAT', default=False)

CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'

CELERY_TIMEZONE = TIME_ZONE  # 'America/Mexico_City'

CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True

CELERY_TASK_SOFT_TIME_LIMIT = 300  # 5 minutos
CELERY_TASK_TIME_LIMIT = 360  # 6 minutos (límite duro)

CELERY_TASK_DEFAULT_QUEUE = 'erp_django'

# Para tests: se activa con @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
CELERY_TASK_ALWAYS_EAGER = 'test' in sys.argv
CELERY_TASK_EAGER_PROPAGATES = True

# ── 15. Correo Electrónico y SendGrid (W17) ─────────────────────────────────
SENDGRID_API_KEY = env('SENDGRID_API_KEY', default='')

# Si hay API key de SendGrid se usa SendGrid; si no, los correos salen en consola.
EMAIL_BACKEND = env(
    'EMAIL_BACKEND',
    default=(
        'anymail.backends.sendgrid.EmailBackend' if SENDGRID_API_KEY
        else 'django.core.mail.backends.console.EmailBackend'
    ),
)
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default='ERP Django <noreply@erp-django.com>')
EMAIL_SUBJECT_PREFIX = '[ERP Django] '

ADMIN_EMAIL = env('ADMIN_EMAIL', default='admin@erp-django.com')
ADMINS = [
    ('Admin ERP', ADMIN_EMAIL),
]

ANYMAIL = {
    'SENDGRID_API_KEY': SENDGRID_API_KEY,
}

# ── 16. Celery Beat — Tareas programadas (W18) ──────────────────────────────
CELERY_BEAT_SCHEDULE = {
    # Verificar stock bajo cada hora
    'verificar-stock-bajo-cada-hora': {
        'task': 'ventas.verificar_stock_bajo',
        'schedule': timedelta(hours=1),
        'args': (5,),  # umbral = 5 unidades
        'options': {'queue': 'erp_django'},
    },
    # Reporte de ventas diario a las 8:00 AM (hora local)
    'reporte-ventas-diario-8am': {
        'task': 'ventas.reporte_ventas_diario',
        'schedule': crontab(hour=8, minute=0),
        # Para PROBAR, cambia temporalmente la línea de arriba por:
        # 'schedule': crontab(minute='*/2'),
        'options': {'queue': 'erp_django'},
    },
}

CELERY_BEAT_TIMEZONE = TIME_ZONE  # 'America/Mexico_City'
