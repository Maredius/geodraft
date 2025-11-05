"""
URL configuration for Geodraft project.
Extends GeoNode URLs with versioned editing functionality.
"""

from django.conf.urls import include
from django.urls import path
from geonode.urls import urlpatterns as geonode_urlpatterns

# Add versioned editing URLs
urlpatterns = [
    path('versioned-editing/', include('versioned_editing.urls')),
] + geonode_urlpatterns
