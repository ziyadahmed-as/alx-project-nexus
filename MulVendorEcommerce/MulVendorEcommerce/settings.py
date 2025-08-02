
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-^ukbxh&8r61@!_pqat&=8mw4dfs=1n5qjyyqh54o)oe1itygei'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'analytics',
    'Users',
    'notifications',
    'orders',
    'products',
    'support',
    'vendors',
    
    'rest_framework',
    'rest_framework_simplejwt',
    'drf_yasg',
    'corsheaders',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
]

ROOT_URLCONF = 'MulVendorEcommerce.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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

WSGI_APPLICATION = 'MulVendorEcommerce.wsgi.application'


# Resting API configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    
    # 'DEFAULT_RENDERER_CLASSES': (
    #     'rest_framework.renderers.JSONRenderer',
    # ),
    # ...
}
# DRF Yasg (Swagger) Settings
# In your settings.py file, carefully check the SWAGGER_SETTINGS dictionary:
SWAGGER_SETTINGS = {
    'SECURITY_DEFINITIONS': {  # ← Make sure all keys have colons
        'Bearer': {
            'type': 'apiKey',
            'name': 'Authorization',
            'in': 'header',
            'description': 'JWT authentication. Example: "Bearer {token}"'
        }
    },
    # ... rest of your configuration ...
}

SWAGGER_SETTINGS = {
    'SECURITY_DEFINITIONS': {
        'Bearer': {
            'type': 'apiKey',
            'name': 'Authorization',
            'in': 'header',
            'description': 'JWT authentication. Example: "Bearer {token}"'
        }
    },
    'USE_SESSION_AUTH': False,  # Set True if using session auth
    'JSON_EDITOR': True,  # Enable JSON editor
    'DEFAULT_INFO': 'MulVendorEcommerce.urls.urls.schema_view',  # Update with your project name
    'LOGIN_URL': 'rest_framework:login',  # If using session auth
    'LOGOUT_URL': 'rest_framework:logout',  # If using session auth
    
    # UI Customization
    'DEEP_LINKING': True,  # Allow direct linking to operations
    'PERSIST_AUTH': True,  # Save auth status across refreshes
    'REFETCH_SCHEMA_ON_LOGOUT': True,  # Clear cache on logout
    
    # Display Options
    'DOC_EXPANSION': 'list',  # ['list', 'full', 'none']
    'SHOW_REQUEST_HEADERS': True,
    'OPERATIONS_SORTER': 'alpha',  # Sort endpoints alphabetically
    'TAGS_SORTER': 'alpha',  # Sort tags alphabetically
    'DISPLAY_OPERATION_ID': False,
    
    # Performance
    'VALIDATOR_URL': None,  # Disable schema validator (better performance)
    
    # For production safety
    'DEFAULT_MODEL_RENDERING': 'MulVendorEcommerce.urls.schema_view',  # Update with your project name
    'DEFAULT_MODEL_DEPTH': 1,
}

# ReDoc Settings
REDOC_SETTINGS = {
    'LAZY_RENDERING': True,  # Better performance for large APIs
    'HIDE_HOSTNAME': False,  # Show API hostname
    'EXPAND_RESPONSES': 'all',  # Expand response examples
    'PATH_IN_MIDDLE': False,  # Better path display
    'HIDE_LOADING': False,  # Show loading animation
    'SCROLL_Y_OFFSET': 60,  # Adjust for fixed headers
    'THEME': {
        'SPACING': {'UNIT': 5, 'SECTION': 10},
        'COLORS': {
            'TEXT': '#333333',
            'PRIMARY': '#4285F4',  # Google blue
        },
        'TYPEOGRAPHY': {
            'FONT_FAMILY': '"Roboto", sans-serif',
            'FONT_SIZE': '14px',
            'HEADERS_FONT_FAMILY': '"Google Sans", sans-serif',
        }
    }
}




import os
if os.name == 'nt':  # Only for Windows
    OSGEO4W = r"C:\OSGeo4W"
    os.environ['OSGEO4W_ROOT'] = OSGEO4W
    os.environ['GDAL_DATA'] = os.path.join(OSGEO4W, "share", "gdal")
    os.environ['PROJ_LIB'] = os.path.join(OSGEO4W, "share", "proj")
    os.environ['PATH'] = OSGEO4W + r'\bin;' + os.environ['PATH']

# Simple JWT configuration
# https://django-rest-framework-simplejwt.readthedocs.io/en/latest/settings.html
from datetime import timedelta
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': None,
    
    'AUTH_HEADER_TYPES': ('Bearer',),
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
}

AUTH_USER_MODEL = 'Users.User'

# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
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

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = 'static/'

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
