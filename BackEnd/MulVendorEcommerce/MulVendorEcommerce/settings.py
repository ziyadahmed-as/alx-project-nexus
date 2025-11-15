import os
from pathlib import Path
from dotenv import load_dotenv
from datetime import timedelta

# Build paths inside the project
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables
load_dotenv(os.path.join(BASE_DIR, '.env'))

# ========== CORE SETTINGS ==========
SECRET_KEY = os.getenv('SECRET_KEY')
if not SECRET_KEY:
    raise ValueError("SECRET_KEY must be set in .env file")

DEBUG = os.getenv('DEBUG', 'False') == 'True'
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

# ========== URL CONFIGURATION ==========
ROOT_URLCONF = 'MulVendorEcommerce.urls'

# ========== WSGI CONFIGURATION ==========
WSGI_APPLICATION = 'MulVendorEcommerce.wsgi.application'
# ========== AUTHENTICATION SETTINGS ==========

Asgi_APPLICATION = 'MulVendorEcommerce.asgi.application'

# ========== AUTH USER MODEL ==========
# Ensure this matches your User model's app label and model name
# This is case-sensitive, so ensure it matches exactly with your User model definition
AUTH_USER_MODEL = 'Users.User'  # Adjust this if your User model is in a different app or has a different name

# ========== CORS SETTINGS ==========
CORS_ALLOWED_ORIGINS = os.getenv('CORS_ALLOWED_ORIGINS', 'http://localhost:3000').split(',')
CORS_ALLOW_CREDENTIALS = True
# ========== CSRF TRUSTED ORIGINS ==========
CSRF_TRUSTED_ORIGINS = os.getenv('CSRF_TRUSTED_ORIGINS', 'http://localhost:3000').split(',')


# ========== REDIS & CACHE CONFIGURATION ==========
# Unified Redis configuration (Docker-compatible)
# settings.py

# Redis Configuration (add anywhere)
REDIS_HOST = 'localhost'  # or 'redis' if using Docker
REDIS_PORT = 6379
REDIS_DB = 0
REDIS_PASSWORD = ''  # If you have password protection
REDIS_TIMEOUT = 5  # seconds
REDIS_CONFIG = {
    'ENABLED': os.getenv('REDIS_ENABLED', 'False') == 'True',
    'HOST': REDIS_HOST, 
    'PORT': REDIS_PORT,
    'DB': REDIS_DB,
    'PASSWORD': REDIS_PASSWORD,
    'TIMEOUT': REDIS_TIMEOUT,
}

# Use Redis for caching if enabled, otherwise fallback to LocMemCache
if REDIS_CONFIG['ENABLED']:
    CACHES = {
        "default": {    
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": f"redis://{REDIS_CONFIG['HOST']}:{REDIS_CONFIG['PORT']}/{REDIS_CONFIG['DB']}",
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
                "PASSWORD": REDIS_CONFIG['PASSWORD'],
                "SOCKET_TIMEOUT": REDIS_CONFIG['TIMEOUT'],
                "SOCKET_CONNECT_TIMEOUT": REDIS_CONFIG['TIMEOUT'],
                "IGNORE_EXCEPTIONS": True,  # Prevents crashes when Redis is down
            }
        }
    }   

else:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "unique-snowflake",
            "TIMEOUT": 300,  # Default timeout for LocMemCache
        }
    }

# ========== DATABASE (Docker-Compatible) ==========
# Use environment variables for database configuration
# This allows for easy configuration in Docker or local development
# Ensure that the environment variables are set in your .env file or Docker environment
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'biyyo',          # Database name
        'USER': 'root',           # Database user
        'PASSWORD': '',           # Database password
        'HOST': 'localhost',      # Database host
        'PORT': '3306',           # Database port
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            'charset': 'utf8mb4',
        }
    }
}

# ========== APPLICATION DEFINITION ==========
# This is the list of installed applications
# Ensure that 'Users' is included in the INSTALLED_APPS list
# This is necessary for Django to recognize the User model and its serializers
from django.contrib.auth import get_user_model

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third-party
    'rest_framework',
    'rest_framework_simplejwt',
    'drf_yasg',
    'corsheaders',
    'django_filters',
    'django_redis',  # Required for Redis cache backend
      
    # Local apps
    'Users',
    'products.apps.ProductsConfig',
    'orders',
    'notifications',
]

# ========== MIDDLEWARE ==========
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

from django.utils.translation import gettext_lazy as _  
from django.core.cache import cache
from django.conf import settings
# ========== CACHING CONFIGURATION ==========
# Use Redis for caching if enabled, otherwise fallback to LocMemCache
REDIS_CONFIG = {    
    'ENABLED': True,  # Set to False to use LocMemCache
    'HOST': 'localhost',  # Redis host
    'PORT': 6379,         # Redis port
    'DB': 0,             # Redis database number
    'PASSWORD': '',      # Redis password if any
    'TIMEOUT': 5,        # Redis timeout in seconds
}   
if REDIS_CONFIG['ENABLED']:
    CACHES = {
        "default": {    
            "BACKEND": "django_redis.cache.RedisCache",     
            "LOCATION": f"redis://{REDIS_CONFIG['HOST']}:{REDIS_CONFIG['PORT']}/{REDIS_CONFIG['DB']}",
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
                "PASSWORD": REDIS_CONFIG['PASSWORD'],
                "SOCKET_TIMEOUT": REDIS_CONFIG['TIMEOUT'],
                "SOCKET_CONNECT_TIMEOUT": REDIS_CONFIG['TIMEOUT'],
                "IGNORE_EXCEPTIONS": True,  # Prevents crashes when Redis is down
            }
        }
    }
    
else:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "unique-snowflake",
            "TIMEOUT": 300,  # Default timeout for LocMemCache
        }
    }   
# ========== REST FRAMEWORK ==========
REST_FRAMEWORK = {
    # Authentication
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',  # JWT
        'rest_framework.authentication.SessionAuthentication',        # Browser sessions
    ],
    
    # Filtering
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
    ],
    
    # Rendering
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',  # Optional - remove if not needed
    ],
    
    # Permission (add this if you want default permission classes)
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',  # Default to require auth
        # or use this for more flexibility:
        # 'rest_framework.permissions.AllowAny',
    ],
    
    # Pagination (optional but recommended)
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}
#configure drf-yasg for API documentation
# Extended Swagger Configuration
SWAGGER_SETTINGS = {
    'SECURITY_DEFINITIONS': {
        'Bearer': {
            'type': 'apiKey',
            'name': 'Authorization',
            'in': 'header',
            'description': 'JWT authentication. Example: "Bearer {token}"'
        }
    },
    'USE_SESSION_AUTH': False,  # Disable Django session auth
    'JSON_EDITOR': True,  # Enable JSON editor
    'REFETCH_SCHEMA_WITH_AUTH': True,  # Update schema when auth is added
    'REFETCH_SCHEMA_ON_LOGOUT': True,  # Clear schema on logout
    
    # Operation configuration
    'OPERATIONS_SORTER': 'alpha',  # Sort endpoints alphabetically
    'TAGS_SORTER': 'alpha',  # Sort tags alphabetically
    'DEEP_LINKING': True,  # Allow direct linking to operations
    
    # UI customization
    'DEFAULT_MODEL_RENDERING': 'model',  # Show model schemas
    'DEFAULT_MODEL_DEPTH': 2,  # Depth of model schema rendering
    'SHOW_REQUEST_HEADERS': True,  # Show request headers section
    'SHOW_OPERATION_ID': True,  # Show operation IDs in the UI
    'VALIDATOR_URL': None,  # Disable external validator URL
    'USE_SESSION_AUTH': False,  # Disable session auth in Swagger UI
}   

 
# Template configuration
# This is necessary for drf-yasg to generate schemas correctly
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
            'libraries': {  # Add this if using custom template tags
                'staticfiles': 'django.templatetags.static',
            }
        },
    },
]

# ========== JWT SETTINGS ==========
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
}

# ========== AUTHENTICATION BACKENDS ==========
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',  # Default backend
]   


# ========== INTERNATIONALIZATION ==========
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

# ========== STATIC & MEDIA ==========
# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')  # For production
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),  # For development
]

# Media files (user uploaded)
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# ========== SECURITY ==========
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

# ========== DOCKER-SPECIFIC SETTINGS ==========
# These environment variables should be set in docker-compose.yml
if os.getenv('DOCKER_ENV', 'False') == 'True':
    # Override Redis host for Docker
    REDIS_CONFIG['HOST'] = 'redis'
    # Override DB host for Docker
    DATABASES['default']['HOST'] = 'db'
    # Additional Docker-specific settings
    CSRF_TRUSTED_ORIGINS = [f"https://{host}" for host in ALLOWED_HOSTS if host != '*']