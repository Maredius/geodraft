"""
Django admin configuration for versioned editing models.
"""
from django.contrib import admin
from django.contrib.gis.admin import OSMGeoAdmin
from .models import UserRole, EditBranch, FeatureVersion, MergeRequest, MergeConflict, AuditLog


@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = ['user', 'group', 'role', 'can_approve_merges', 'can_manage_branches', 'created_at']
    list_filter = ['role', 'can_approve_merges', 'can_manage_branches', 'group']
    search_fields = ['user__username', 'user__email', 'group__title']
    readonly_fields = ['id', 'created_at', 'updated_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'group', 'role')
        }),
        ('Permissions', {
            'fields': ('can_approve_merges', 'can_manage_branches')
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(EditBranch)
class EditBranchAdmin(admin.ModelAdmin):
    list_display = ['name', 'layer', 'group', 'created_by', 'status', 'created_at', 'merged_at']
    list_filter = ['status', 'created_at', 'layer', 'group']
    search_fields = ['name', 'description', 'layer__name', 'group__title']
    readonly_fields = ['id', 'created_at', 'updated_at']
    date_hierarchy = 'created_at'


@admin.register(FeatureVersion)
class FeatureVersionAdmin(OSMGeoAdmin):
    list_display = ['feature_id', 'version', 'branch', 'operation', 'created_by', 'created_at']
    list_filter = ['operation', 'is_deleted', 'created_at', 'branch']
    search_fields = ['feature_id', 'properties']
    readonly_fields = ['id', 'created_at']
    date_hierarchy = 'created_at'


@admin.register(MergeRequest)
class MergeRequestAdmin(admin.ModelAdmin):
    list_display = ['title', 'source_branch', 'target_branch', 'status', 'created_by', 'created_at']
    list_filter = ['status', 'created_at', 'reviewed_at']
    search_fields = ['title', 'description']
    readonly_fields = ['id', 'created_at', 'updated_at']
    date_hierarchy = 'created_at'


@admin.register(MergeConflict)
class MergeConflictAdmin(OSMGeoAdmin):
    list_display = ['merge_request', 'feature_id', 'conflict_type', 'resolved', 'resolved_by']
    list_filter = ['conflict_type', 'resolved', 'resolution_strategy']
    search_fields = ['feature_id']
    readonly_fields = ['id', 'resolved_at']


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['action', 'user', 'entity_type', 'entity_id', 'created_at']
    list_filter = ['action', 'entity_type', 'created_at']
    search_fields = ['user__username', 'entity_id', 'details']
    readonly_fields = ['id', 'created_at']
    date_hierarchy = 'created_at'
