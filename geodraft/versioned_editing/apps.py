"""
App configuration for versioned editing
"""
from django.apps import AppConfig


class VersionedEditingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'versioned_editing'
    verbose_name = 'Versioned Editing'

    def ready(self):
        """Import signals when app is ready"""
        import versioned_editing.signals
