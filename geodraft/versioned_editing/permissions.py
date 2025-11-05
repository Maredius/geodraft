"""
Permission management for versioned editing.
Implements role-based access control with Admin, Validator, and Editor roles.
"""
from django.contrib.auth import get_user_model
from geonode.groups.models import GroupProfile
from .models import UserRole, EditBranch, MergeRequest

User = get_user_model()


class PermissionManager:
    """
    Manages permissions for versioned editing based on user roles.
    
    Role hierarchy:
    - Admin: Full access to everything
    - Validator: Can validate edits in their group(s)
    - Editor: Can edit data in their group(s)
    """
    
    @staticmethod
    def is_admin(user):
        """Check if user is an admin (superuser or has admin role)"""
        if user.is_superuser:
            return True
        return UserRole.objects.filter(user=user, role='admin').exists()
    
    @staticmethod
    def is_validator_in_group(user, group):
        """Check if user is a validator in a specific group"""
        if user.is_superuser:
            return True
        return UserRole.objects.filter(
            user=user,
            group=group,
            role__in=['validator', 'admin']
        ).exists()
    
    @staticmethod
    def is_editor_in_group(user, group):
        """Check if user is an editor in a specific group"""
        if user.is_superuser:
            return True
        return UserRole.objects.filter(
            user=user,
            group=group,
            role__in=['editor', 'validator', 'admin']
        ).exists()
    
    @staticmethod
    def can_create_branch(user, layer):
        """Check if user can create a branch for a layer"""
        # Admins can always create branches
        if PermissionManager.is_admin(user):
            return True
        
        # Check if layer belongs to a group where user has editor+ role
        if hasattr(layer, 'group') and layer.group:
            return PermissionManager.is_editor_in_group(user, layer.group)
        
        # Check user's permissions on the layer resource
        return user.has_perm('change_resourcebase', layer.get_self_resource())
    
    @staticmethod
    def can_edit_branch(user, branch):
        """Check if user can edit a branch"""
        # Admins can edit any branch
        if PermissionManager.is_admin(user):
            return True
        
        # Check if user is the branch creator
        if branch.created_by == user:
            return True
        
        # Check if user has editor role in branch's group
        if branch.group:
            return PermissionManager.is_editor_in_group(user, branch.group)
        
        return False
    
    @staticmethod
    def can_delete_branch(user, branch):
        """Check if user can delete a branch"""
        # Cannot delete master branch
        if branch.is_master():
            return False
        
        # Admins can delete any branch
        if PermissionManager.is_admin(user):
            return True
        
        # Users can delete their own branches
        if branch.created_by == user:
            # Check if they have branch management permission
            if branch.group:
                role = UserRole.objects.filter(
                    user=user,
                    group=branch.group,
                    can_manage_branches=True
                ).first()
                return role is not None
            return True
        
        return False
    
    @staticmethod
    def can_create_merge_request(user, source_branch, target_branch):
        """Check if user can create a merge request"""
        # Must be able to edit source branch
        if not PermissionManager.can_edit_branch(user, source_branch):
            return False
        
        # Branches must be in same layer
        if source_branch.layer != target_branch.layer:
            return False
        
        # Cannot merge to itself
        if source_branch == target_branch:
            return False
        
        return True
    
    @staticmethod
    def can_approve_merge_request(user, merge_request):
        """Check if user can approve a merge request"""
        # Admins can approve any merge request
        if PermissionManager.is_admin(user):
            return True
        
        # Check if user is validator in target branch's group
        if merge_request.target_branch.group:
            return UserRole.objects.filter(
                user=user,
                group=merge_request.target_branch.group,
                role__in=['validator', 'admin'],
                can_approve_merges=True
            ).exists()
        
        return False
    
    @staticmethod
    def can_manage_users(user):
        """Check if user can manage other users (add/remove from groups, assign roles)"""
        return PermissionManager.is_admin(user)
    
    @staticmethod
    def can_manage_groups(user):
        """Check if user can create/delete groups"""
        return PermissionManager.is_admin(user)
    
    @staticmethod
    def can_manage_data_library(user):
        """Check if user can manage the data library (add/remove layers)"""
        return PermissionManager.is_admin(user)
    
    @staticmethod
    def get_user_groups(user):
        """Get all groups where user has any role"""
        if user.is_superuser:
            return GroupProfile.objects.all()
        
        user_roles = UserRole.objects.filter(user=user).select_related('group')
        return GroupProfile.objects.filter(
            id__in=[role.group.id for role in user_roles]
        )
    
    @staticmethod
    def get_user_role_in_group(user, group):
        """Get user's highest role in a group"""
        if user.is_superuser:
            return 'admin'
        
        # Get highest role (admin > validator > editor)
        role_priority = {'admin': 3, 'validator': 2, 'editor': 1}
        roles = UserRole.objects.filter(user=user, group=group).values_list('role', flat=True)
        
        if not roles:
            return None
        
        return max(roles, key=lambda r: role_priority.get(r, 0))
    
    @staticmethod
    def assign_role(admin_user, target_user, group, role, can_approve_merges=None, can_manage_branches=True):
        """
        Assign a role to a user in a group.
        Only admins can assign roles.
        """
        if not PermissionManager.can_manage_users(admin_user):
            raise PermissionError("Only admins can assign roles")
        
        # Validate role
        if role not in ['admin', 'validator', 'editor']:
            raise ValueError(f"Invalid role: {role}")
        
        # Auto-set can_approve_merges for validators and admins
        if can_approve_merges is None:
            can_approve_merges = role in ['validator', 'admin']
        
        user_role, created = UserRole.objects.update_or_create(
            user=target_user,
            group=group,
            role=role,
            defaults={
                'can_approve_merges': can_approve_merges,
                'can_manage_branches': can_manage_branches
            }
        )
        
        return user_role
    
    @staticmethod
    def remove_role(admin_user, target_user, group, role):
        """
        Remove a role from a user in a group.
        Only admins can remove roles.
        """
        if not PermissionManager.can_manage_users(admin_user):
            raise PermissionError("Only admins can remove roles")
        
        UserRole.objects.filter(
            user=target_user,
            group=group,
            role=role
        ).delete()
    
    @staticmethod
    def get_group_members(group):
        """Get all users with roles in a group"""
        user_roles = UserRole.objects.filter(group=group).select_related('user')
        return {
            'admins': [ur.user for ur in user_roles if ur.role == 'admin'],
            'validators': [ur.user for ur in user_roles if ur.role == 'validator'],
            'editors': [ur.user for ur in user_roles if ur.role == 'editor'],
        }
