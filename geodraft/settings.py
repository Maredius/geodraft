"""
Django settings for Geodraft project.
Based on GeoNode with versioned editing extensions.
"""

import os
from geonode.settings import *

# Project name
PROJECT_NAME = 'geodraft'

# Geodraft specific settings
GEODRAFT_VERSION = '1.0.0'

# Add versioned_editing app to installed apps
INSTALLED_APPS += (
    'versioned_editing',
)

# Database configuration
# GeoNode uses two databases: default (Django) and datastore (PostGIS)
DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': os.getenv('GEONODE_DATABASE', 'geonode'),
        'USER': os.getenv('GEONODE_DATABASE_USER', 'postgres'),
        'PASSWORD': os.getenv('GEONODE_DATABASE_PASSWORD', 'postgres'),
        'HOST': os.getenv('DATABASE_HOST', 'db'),
        'PORT': os.getenv('DATABASE_PORT', '5432'),
        'CONN_MAX_AGE': 0,
        'CONN_TOUT': 900,
        'OPTIONS': {
            'connect_timeout': 10,
        }
    },
    'datastore': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': os.getenv('GEONODE_GEODATABASE', 'geonode_data'),
        'USER': os.getenv('GEONODE_GEODATABASE_USER', 'postgres'),
        'PASSWORD': os.getenv('GEONODE_GEODATABASE_PASSWORD', 'postgres'),
        'HOST': os.getenv('GEODATABASE_HOST', 'db'),
        'PORT': os.getenv('GEODATABASE_PORT', '5432'),
        'CONN_MAX_AGE': 0,
        'CONN_TOUT': 900,
        'OPTIONS': {
            'connect_timeout': 10,
        }
    }
}

# GeoServer configuration
OGC_SERVER = {
    'default': {
        'BACKEND': 'geonode.geoserver',
        'LOCATION': os.getenv('GEOSERVER_LOCATION', 'http://geoserver:8080/geoserver/'),
        'PUBLIC_LOCATION': os.getenv('GEOSERVER_PUBLIC_LOCATION', 'http://localhost:8080/geoserver/'),
        'USER': os.getenv('GEOSERVER_ADMIN_USER', 'admin'),
        'PASSWORD': os.getenv('GEOSERVER_ADMIN_PASSWORD', 'geoserver'),
        'DATASTORE': 'datastore',
    }
}

# Site URL
SITEURL = os.getenv('SITEURL', 'http://localhost:8000/')

# Static and media files
STATIC_ROOT = '/mnt/volumes/statics/static/'
MEDIA_ROOT = '/mnt/volumes/media/'

# Versioned editing specific settings
VERSIONED_EDITING = {
    'ENABLE_AUTO_VERSIONING': True,
    'MAX_VERSIONS_PER_FEATURE': 100,
    'DEFAULT_BRANCH_NAME': 'master',
    'MERGE_STRATEGIES': ['auto', 'manual', 'theirs', 'ours'],
    'ENABLE_CONFLICT_DETECTION': True,
    'AUDIT_LOG_ENABLED': True,
}

# Permissions for versioned editing
# Users with these roles can approve merge requests
VERSIONED_EDITING_VALIDATORS = ['validator', 'admin']

# REST Framework configuration for API
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 50,
}

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'versioned_editing': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}
