from pathlib import Path
import os

# Base Directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Seguridad
SECRET_KEY = 'django-insecure-*jbj*g(^k==yk!xc#ylgld1w+@mp3h87+(cpoj9gg8c+a=w)!r'
DEBUG = True  # Cambiar a False en producción
ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# Aplicaciones instaladas
INSTALLED_APPS = [
    'calendarios',
    'django_filters',
    'horarios',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'widget_tweaks',
    'rest_framework',
]

# Middleware
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'sgvh.urls'

# Templates
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
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

# Aplicación WSGI
WSGI_APPLICATION = 'sgvh.wsgi.application'

# Base de Datos
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

# Validación de Contraseñas
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',},
]

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ],
}

# Internacionalización
LANGUAGE_CODE = 'es'
TIME_ZONE = 'America/Bogota'
USE_I18N = True
USE_TZ = False

# Archivos Estáticos
# Configuración de archivos estáticos
STATIC_URL = '/static/'

STATICFILES_DIRS = [
    # Eliminar esta línea que causa el warning
    # os.path.join(BASE_DIR, 'static'),
    os.path.join(BASE_DIR, 'horarios', 'static'),
]

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Configuración de archivos media
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Asegúrate de que tienes esto en tu archivo urls.py principal
'''
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Tus otras URLs
]

if settings.DEBUG:
    # Servir archivos estáticos en desarrollo
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    # Servir archivos media en desarrollo
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
'''

# Configuración de Autenticación Personalizada
AUTH_USER_MODEL = 'horarios.Administrador'  # Modelo personalizado para usuarios (administradores)

# Especifica los backends de autenticación
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',  # Backend predeterminado
]

# Redirección de Login
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'admin_dashboard'
LOGOUT_REDIRECT_URL = 'login'

# Configuraciones de Seguridad
# En producción, activa estas configuraciones
# SECURE_SSL_REDIRECT = True
# SESSION_COOKIE_SECURE = True
# CSRF_COOKIE_SECURE = True
# SECURE_BROWSER_XSS_FILTER = True
# SECURE_CONTENT_TYPE_NOSNIFF = True
# Configuración de sesiones

SESSION_COOKIE_AGE = 3600 * 24 * 7  # 1 semana en segundos
SESSION_SAVE_EVERY_REQUEST = True  # Actualiza la cookie de sesión en cada petición

# Archivo predeterminado para claves primarias
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
