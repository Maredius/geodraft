"""
Administrative views for managing users, groups, and roles.
Only accessible by admins.
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth import get_user_model
from geonode.groups.models import GroupProfile
from .models import UserRole
from .permissions import PermissionManager
from .forms import AssignRoleForm, CreateGroupForm

User = get_user_model()


def is_admin(user):
    """Check if user is an admin"""
    return PermissionManager.is_admin(user)


@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    """
    Main admin dashboard for managing users, groups, and roles.
    """
    # Get statistics
    total_users = User.objects.count()
    total_groups = GroupProfile.objects.count()
    total_roles = UserRole.objects.count()
    
    # Get recent roles assigned
    recent_roles = UserRole.objects.select_related('user', 'group').order_by('-created_at')[:10]
    
    context = {
        'total_users': total_users,
        'total_groups': total_groups,
        'total_roles': total_roles,
        'recent_roles': recent_roles,
    }
    
    return render(request, 'versioned_editing/admin/dashboard.html', context)


@login_required
@user_passes_test(is_admin)
def manage_users(request):
    """
    List and manage users.
    """
    users = User.objects.all().order_by('username')
    
    # Add role information for each user
    users_with_roles = []
    for user in users:
        user_roles = UserRole.objects.filter(user=user).select_related('group')
        users_with_roles.append({
            'user': user,
            'roles': user_roles,
            'groups': PermissionManager.get_user_groups(user),
            'is_admin': PermissionManager.is_admin(user)
        })
    
    context = {
        'users_with_roles': users_with_roles,
    }
    
    return render(request, 'versioned_editing/admin/manage_users.html', context)


@login_required
@user_passes_test(is_admin)
def manage_user_roles(request, user_id):
    """
    Manage roles for a specific user.
    """
    target_user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        form = AssignRoleForm(request.POST)
        if form.is_valid():
            try:
                PermissionManager.assign_role(
                    admin_user=request.user,
                    target_user=target_user,
                    group=form.cleaned_data['group'],
                    role=form.cleaned_data['role'],
                    can_approve_merges=form.cleaned_data.get('can_approve_merges'),
                    can_manage_branches=form.cleaned_data.get('can_manage_branches', True)
                )
                messages.success(request, f"Role assigned to {target_user.username}")
                return redirect('versioned_editing:manage_user_roles', user_id=user_id)
            except Exception as e:
                messages.error(request, f"Error assigning role: {e}")
    else:
        form = AssignRoleForm()
    
    # Get current roles
    user_roles = UserRole.objects.filter(user=target_user).select_related('group')
    
    context = {
        'target_user': target_user,
        'user_roles': user_roles,
        'form': form,
    }
    
    return render(request, 'versioned_editing/admin/manage_user_roles.html', context)


@login_required
@user_passes_test(is_admin)
def remove_user_role(request, role_id):
    """
    Remove a role from a user.
    """
    if request.method == 'POST':
        role = get_object_or_404(UserRole, id=role_id)
        user = role.user
        
        try:
            PermissionManager.remove_role(
                admin_user=request.user,
                target_user=role.user,
                group=role.group,
                role=role.role
            )
            messages.success(request, f"Role removed from {user.username}")
        except Exception as e:
            messages.error(request, f"Error removing role: {e}")
        
        return redirect('versioned_editing:manage_user_roles', user_id=user.id)
    
    return redirect('versioned_editing:manage_users')


@login_required
@user_passes_test(is_admin)
def manage_groups(request):
    """
    List and manage groups.
    """
    groups = GroupProfile.objects.all().order_by('title')
    
    # Add member information for each group
    groups_with_members = []
    for group in groups:
        members = PermissionManager.get_group_members(group)
        groups_with_members.append({
            'group': group,
            'members': members,
            'total_members': sum(len(m) for m in members.values())
        })
    
    context = {
        'groups_with_members': groups_with_members,
    }
    
    return render(request, 'versioned_editing/admin/manage_groups.html', context)


@login_required
@user_passes_test(is_admin)
def group_detail(request, group_id):
    """
    View and manage a specific group.
    """
    group = get_object_or_404(GroupProfile, id=group_id)
    members = PermissionManager.get_group_members(group)
    
    # Get all user roles in this group
    user_roles = UserRole.objects.filter(group=group).select_related('user').order_by('role', 'user__username')
    
    context = {
        'group': group,
        'members': members,
        'user_roles': user_roles,
    }
    
    return render(request, 'versioned_editing/admin/group_detail.html', context)


@login_required
@user_passes_test(is_admin)
def add_user_to_group(request, group_id):
    """
    Add a user to a group with a specific role.
    """
    group = get_object_or_404(GroupProfile, id=group_id)
    
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        role = request.POST.get('role')
        
        if user_id and role:
            target_user = get_object_or_404(User, id=user_id)
            
            try:
                PermissionManager.assign_role(
                    admin_user=request.user,
                    target_user=target_user,
                    group=group,
                    role=role
                )
                messages.success(request, f"Added {target_user.username} to {group.title} as {role}")
            except Exception as e:
                messages.error(request, f"Error adding user: {e}")
        
        return redirect('versioned_editing:group_detail', group_id=group_id)
    
    # Get users not in this group
    users_in_group = UserRole.objects.filter(group=group).values_list('user_id', flat=True)
    available_users = User.objects.exclude(id__in=users_in_group).order_by('username')
    
    context = {
        'group': group,
        'available_users': available_users,
    }
    
    return render(request, 'versioned_editing/admin/add_user_to_group.html', context)


@login_required
@user_passes_test(is_admin)
def api_search_users(request):
    """
    API endpoint to search users (for autocomplete).
    """
    query = request.GET.get('q', '')
    if len(query) < 2:
        return JsonResponse({'users': []})
    
    users = User.objects.filter(username__icontains=query)[:10]
    
    return JsonResponse({
        'users': [
            {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'is_admin': PermissionManager.is_admin(user)
            }
            for user in users
        ]
    })
