"""
URL configuration for versioned editing.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views, api_views, admin_views

# API router for REST endpoints
router = DefaultRouter()
router.register(r'branches', api_views.EditBranchViewSet, basename='branch')
router.register(r'features', api_views.FeatureVersionViewSet, basename='feature')
router.register(r'merge-requests', api_views.MergeRequestViewSet, basename='merge-request')

app_name = 'versioned_editing'

urlpatterns = [
    # Web views for UI
    path('layer/<int:layer_id>/editor/', views.layer_editor, name='layer_editor'),
    path('layer/<int:layer_id>/branches/', views.branch_list, name='branch_list'),
    path('branch/<uuid:branch_id>/', views.branch_detail, name='branch_detail'),
    path('merge-request/<uuid:mr_id>/', views.merge_request_detail, name='merge_request_detail'),
    
    # Admin views for managing users, groups, and roles
    path('admin/', admin_views.admin_dashboard, name='admin_dashboard'),
    path('admin/users/', admin_views.manage_users, name='manage_users'),
    path('admin/users/<int:user_id>/roles/', admin_views.manage_user_roles, name='manage_user_roles'),
    path('admin/roles/<uuid:role_id>/remove/', admin_views.remove_user_role, name='remove_user_role'),
    path('admin/groups/', admin_views.manage_groups, name='manage_groups'),
    path('admin/groups/<int:group_id>/', admin_views.group_detail, name='group_detail'),
    path('admin/groups/<int:group_id>/add-user/', admin_views.add_user_to_group, name='add_user_to_group'),
    path('admin/api/search-users/', admin_views.api_search_users, name='api_search_users'),
    
    # REST API
    path('api/', include(router.urls)),
]
