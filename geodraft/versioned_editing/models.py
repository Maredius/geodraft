"""
Models for versioned editing system.
Integrates with GeoNode layers for collaborative editing.
Supports role-based permissions with Admin, Validator, and Editor roles.
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.gis.db import models as gis_models
from django.utils import timezone
from geonode.layers.models import Dataset
from geonode.groups.models import GroupProfile
import uuid

User = get_user_model()


class UserRole(models.Model):
    """
    Defines user roles within groups for versioned editing.
    A user can have different roles in different groups.
    
    Roles:
    - admin: Full system access, manages data library, users, groups, and permissions
    - validator: Validates edits from editors in their group(s)
    - editor: Edits data in their group(s)
    """
    ROLE_CHOICES = [
        ('admin', 'Administrator'),
        ('validator', 'Validator'),
        ('editor', 'Editor'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='versioned_editing_roles')
    group = models.ForeignKey(
        GroupProfile, 
        on_delete=models.CASCADE, 
        related_name='versioned_editing_roles',
        help_text="GeoNode group this role applies to"
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    
    # Permissions can be further customized per user
    can_approve_merges = models.BooleanField(
        default=False,
        help_text="Can approve merge requests (automatically True for validators and admins)"
    )
    can_manage_branches = models.BooleanField(
        default=True,
        help_text="Can create and delete branches"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'versioned_editing_user_role'
        unique_together = [['user', 'group', 'role']]
        indexes = [
            models.Index(fields=['user', 'role']),
            models.Index(fields=['group', 'role']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.role} in {self.group.title}"
    
    def save(self, *args, **kwargs):
        # Auto-enable merge approval for validators and admins
        if self.role in ['validator', 'admin']:
            self.can_approve_merges = True
        super().save(*args, **kwargs)


class EditBranch(models.Model):
    """
    Represents an editing branch for a GeoNode layer.
    Similar to Git branches - users create branches to make edits.
    Branches are associated with groups for permission management.
    """
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('merged', 'Merged'),
        ('closed', 'Closed'),
        ('deleted', 'Deleted'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, help_text="Branch name")
    description = models.TextField(blank=True, null=True)
    
    # Link to GeoNode layer
    layer = models.ForeignKey(
        Dataset,
        on_delete=models.CASCADE,
        related_name='edit_branches',
        help_text="GeoNode layer this branch belongs to"
    )
    
    # Link to GeoNode group for permissions
    group = models.ForeignKey(
        GroupProfile,
        on_delete=models.CASCADE,
        related_name='edit_branches',
        null=True,
        blank=True,
        help_text="GeoNode group this branch belongs to for permission management"
    )
    
    # Branch hierarchy
    parent_branch = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='child_branches',
        help_text="Parent branch (typically 'master')"
    )
    
    # User and status
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_branches')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    merged_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'versioned_editing_branch'
        unique_together = [['layer', 'name', 'created_by']]
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['layer', 'status']),
            models.Index(fields=['created_by', 'status']),
            models.Index(fields=['group', 'status']),
        ]

    def __str__(self):
        return f"{self.layer.name} - {self.name}"

    def is_master(self):
        """Check if this is the master branch"""
        return self.parent_branch is None and self.name == 'master'
    
    def can_user_edit(self, user):
        """Check if user can edit this branch"""
        # Admins can edit any branch
        if user.is_superuser:
            return True
        
        # Check if user has editor role in the branch's group
        if self.group:
            return UserRole.objects.filter(
                user=user,
                group=self.group,
                role__in=['editor', 'validator', 'admin']
            ).exists()
        
        # If no group, check if user is the creator
        return self.created_by == user


class FeatureVersion(models.Model):
    """
    Stores versions of features (spatial data) in a branch.
    Each edit creates a new version.
    """
    OPERATION_CHOICES = [
        ('CREATE', 'Create'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete'),
        ('MERGE', 'Merge'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Branch and feature identification
    branch = models.ForeignKey(EditBranch, on_delete=models.CASCADE, related_name='feature_versions')
    feature_id = models.UUIDField(help_text="Identifies the feature across versions")
    version = models.IntegerField(default=1, help_text="Version number")
    
    # Spatial data
    geometry = gis_models.GeometryField(
        srid=4326,
        help_text="Feature geometry in WGS84"
    )
    properties = models.JSONField(
        default=dict,
        help_text="Feature properties/attributes"
    )
    
    # Operation and status
    operation = models.CharField(max_length=20, choices=OPERATION_CHOICES)
    is_deleted = models.BooleanField(default=False)
    
    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    comment = models.TextField(blank=True, null=True, help_text="Edit comment")

    class Meta:
        db_table = 'versioned_editing_feature_version'
        ordering = ['feature_id', '-version']
        indexes = [
            models.Index(fields=['branch', 'feature_id']),
            models.Index(fields=['branch', 'is_deleted']),
            models.Index(fields=['feature_id', 'version']),
        ]

    def __str__(self):
        return f"Feature {self.feature_id} v{self.version} ({self.operation})"


class MergeRequest(models.Model):
    """
    Merge request to merge changes from one branch to another.
    Requires validation by a validator or admin in the group.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('merged', 'Merged'),
        ('conflicts', 'Has Conflicts'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Branches
    source_branch = models.ForeignKey(
        EditBranch,
        on_delete=models.CASCADE,
        related_name='merge_requests_as_source'
    )
    target_branch = models.ForeignKey(
        EditBranch,
        on_delete=models.CASCADE,
        related_name='merge_requests_as_target'
    )
    
    # Request details
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Users
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_merge_requests'
    )
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_merge_requests'
    )
    
    # Review details
    review_comment = models.TextField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'versioned_editing_merge_request'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['source_branch', 'status']),
            models.Index(fields=['created_by', 'status']),
        ]

    def __str__(self):
        return f"MR: {self.source_branch.name} → {self.target_branch.name}"
    
    def can_user_approve(self, user):
        """Check if user can approve this merge request"""
        # Superusers can always approve
        if user.is_superuser:
            return True
        
        # Check if user has validator or admin role in the target branch's group
        if self.target_branch.group:
            return UserRole.objects.filter(
                user=user,
                group=self.target_branch.group,
                role__in=['validator', 'admin'],
                can_approve_merges=True
            ).exists()
        
        return False
    
    def get_validators(self):
        """Get all users who can validate this merge request"""
        if not self.target_branch.group:
            return User.objects.filter(is_superuser=True)
        
        validator_roles = UserRole.objects.filter(
            group=self.target_branch.group,
            role__in=['validator', 'admin'],
            can_approve_merges=True
        ).select_related('user')
        
        return [role.user for role in validator_roles]


class MergeConflict(models.Model):
    """
    Represents a conflict detected during merge request.
    """
    CONFLICT_TYPE_CHOICES = [
        ('GEOMETRY', 'Geometry Conflict'),
        ('PROPERTIES', 'Properties Conflict'),
        ('BOTH', 'Geometry and Properties Conflict'),
        ('DELETE', 'Delete Conflict'),
    ]

    RESOLUTION_CHOICES = [
        ('SOURCE', 'Use Source Version'),
        ('TARGET', 'Use Target Version'),
        ('MANUAL', 'Manual Resolution'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    merge_request = models.ForeignKey(
        MergeRequest,
        on_delete=models.CASCADE,
        related_name='conflicts'
    )
    
    feature_id = models.UUIDField(help_text="Feature with conflict")
    conflict_type = models.CharField(max_length=20, choices=CONFLICT_TYPE_CHOICES)
    
    # Versions involved in conflict
    source_version = models.ForeignKey(
        FeatureVersion,
        on_delete=models.CASCADE,
        related_name='conflicts_as_source'
    )
    target_version = models.ForeignKey(
        FeatureVersion,
        on_delete=models.CASCADE,
        related_name='conflicts_as_target',
        null=True,
        blank=True
    )
    
    # Resolution
    resolved = models.BooleanField(default=False)
    resolution_strategy = models.CharField(
        max_length=20,
        choices=RESOLUTION_CHOICES,
        null=True,
        blank=True
    )
    resolved_geometry = gis_models.GeometryField(srid=4326, null=True, blank=True)
    resolved_properties = models.JSONField(null=True, blank=True)
    resolved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'versioned_editing_conflict'
        indexes = [
            models.Index(fields=['merge_request', 'resolved']),
        ]

    def __str__(self):
        return f"Conflict: {self.conflict_type} on feature {self.feature_id}"


class AuditLog(models.Model):
    """
    Audit trail for all versioned editing operations.
    """
    ACTION_CHOICES = [
        ('CREATE_BRANCH', 'Create Branch'),
        ('DELETE_BRANCH', 'Delete Branch'),
        ('CREATE_FEATURE', 'Create Feature'),
        ('UPDATE_FEATURE', 'Update Feature'),
        ('DELETE_FEATURE', 'Delete Feature'),
        ('CREATE_MERGE_REQUEST', 'Create Merge Request'),
        ('APPROVE_MERGE_REQUEST', 'Approve Merge Request'),
        ('REJECT_MERGE_REQUEST', 'Reject Merge Request'),
        ('RESOLVE_CONFLICT', 'Resolve Conflict'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    
    # Entity references
    entity_type = models.CharField(max_length=50)
    entity_id = models.UUIDField()
    
    # Details
    details = models.JSONField(default=dict)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'versioned_editing_audit_log'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['entity_type', 'entity_id']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return f"{self.action} by {self.user} at {self.created_at}"
