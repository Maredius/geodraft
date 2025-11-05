"""
Custom template tags for versioned editing.
Adds "Edit" button to GeoNode layer detail pages.
"""
from django import template
from django.urls import reverse
from versioned_editing.models import EditBranch

register = template.Library()


@register.inclusion_tag('versioned_editing/includes/edit_button.html', takes_context=True)
def show_edit_button(context, layer):
    """
    Display edit button for vector layers.
    Usage in template: {% show_edit_button layer %}
    """
    request = context.get('request')
    user = request.user if request else None
    
    # Only show for vector layers
    can_show = layer.subtype == 'vector' if hasattr(layer, 'subtype') else False
    
    # Check if user has edit permission
    can_edit = False
    if user and user.is_authenticated and can_show:
        can_edit = user.has_perm('change_resourcebase', layer.get_self_resource())
    
    # Check if master branch exists
    has_master_branch = EditBranch.objects.filter(
        layer=layer,
        name='master',
        status='active'
    ).exists()
    
    return {
        'layer': layer,
        'can_edit': can_edit,
        'can_show': can_show,
        'has_master_branch': has_master_branch,
        'edit_url': reverse('versioned_editing:layer_editor', kwargs={'layer_id': layer.id}) if can_show else None,
    }


@register.filter
def get_active_branches_count(layer):
    """
    Get count of active branches for a layer.
    Usage: {{ layer|get_active_branches_count }}
    """
    return EditBranch.objects.filter(layer=layer, status='active').count()
