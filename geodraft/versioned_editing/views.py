"""
Views for versioned editing web interface.
Integrates with GeoNode layer detail pages.
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from geonode.layers.models import Dataset
from .models import EditBranch, MergeRequest, FeatureVersion
from .forms import CreateBranchForm, CreateMergeRequestForm


@login_required
def layer_editor(request, layer_id):
    """
    Main editor view for a layer.
    Launched from the "Edit" button on a GeoNode layer detail page.
    """
    layer = get_object_or_404(Dataset, id=layer_id)
    
    # Check if user has edit permission
    if not request.user.has_perm('change_resourcebase', layer.get_self_resource()):
        messages.error(request, "You don't have permission to edit this layer.")
        return redirect('layer_detail', layername=layer.alternate)
    
    # Get or create master branch
    master_branch, created = EditBranch.objects.get_or_create(
        layer=layer,
        name='master',
        parent_branch=None,
        defaults={
            'description': 'Master branch',
            'created_by': layer.owner,
            'status': 'active'
        }
    )
    
    # Get user's branches
    user_branches = EditBranch.objects.filter(
        layer=layer,
        created_by=request.user,
        status='active'
    ).exclude(name='master')
    
    # Get current branch from session or use master
    current_branch_id = request.session.get(f'layer_{layer_id}_branch', str(master_branch.id))
    current_branch = EditBranch.objects.filter(id=current_branch_id).first() or master_branch
    
    context = {
        'layer': layer,
        'master_branch': master_branch,
        'current_branch': current_branch,
        'user_branches': user_branches,
        'can_create_branch': True,
        'can_create_merge_request': user_branches.exists(),
    }
    
    return render(request, 'versioned_editing/editor.html', context)


@login_required
def branch_list(request, layer_id):
    """
    List all branches for a layer.
    """
    layer = get_object_or_404(Dataset, id=layer_id)
    
    branches = EditBranch.objects.filter(
        layer=layer,
        status__in=['active', 'merged']
    ).select_related('created_by', 'parent_branch')
    
    context = {
        'layer': layer,
        'branches': branches,
    }
    
    return render(request, 'versioned_editing/branch_list.html', context)


@login_required
def branch_detail(request, branch_id):
    """
    View details of a specific branch.
    """
    branch = get_object_or_404(EditBranch, id=branch_id)
    
    # Get feature versions in this branch
    feature_versions = FeatureVersion.objects.filter(
        branch=branch,
        is_deleted=False
    ).order_by('-created_at')[:50]
    
    # Get merge requests for this branch
    merge_requests = MergeRequest.objects.filter(
        source_branch=branch
    ).order_by('-created_at')
    
    context = {
        'branch': branch,
        'layer': branch.layer,
        'feature_versions': feature_versions,
        'merge_requests': merge_requests,
    }
    
    return render(request, 'versioned_editing/branch_detail.html', context)


@login_required
def merge_request_detail(request, mr_id):
    """
    View details of a merge request and handle approval/rejection.
    """
    merge_request = get_object_or_404(MergeRequest, id=mr_id)
    
    # Check if user can approve (validator or admin)
    can_approve = request.user.is_superuser or \
                  getattr(request.user, 'profile', None) and \
                  hasattr(request.user.profile, 'role') and \
                  request.user.profile.role in ['validator', 'admin']
    
    # Get conflicts
    conflicts = merge_request.conflicts.all()
    
    context = {
        'merge_request': merge_request,
        'layer': merge_request.source_branch.layer,
        'conflicts': conflicts,
        'can_approve': can_approve,
        'is_creator': merge_request.created_by == request.user,
    }
    
    return render(request, 'versioned_editing/merge_request_detail.html', context)
