"""
Signal handlers for versioned editing.
Automatically create master branch for new vector layers.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from geonode.layers.models import Dataset
from .models import EditBranch
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Dataset)
def create_master_branch_for_layer(sender, instance, created, **kwargs):
    """
    Automatically create a 'master' branch when a new vector layer is created.
    """
    if created and instance.subtype == 'vector':
        try:
            # Check if master branch already exists
            master_exists = EditBranch.objects.filter(
                layer=instance,
                name='master',
                parent_branch=None
            ).exists()
            
            if not master_exists:
                EditBranch.objects.create(
                    name='master',
                    description='Master branch',
                    layer=instance,
                    created_by=instance.owner,
                    parent_branch=None,
                    status='active'
                )
                logger.info(f"Created master branch for layer: {instance.name}")
        except Exception as e:
            logger.error(f"Failed to create master branch for layer {instance.name}: {e}")
