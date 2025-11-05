"""
REST API views for versioned editing.
Provides programmatic access to branches, features, and merge requests.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.shortcuts import get_object_or_404
from geonode.layers.models import Dataset
from .models import EditBranch, FeatureVersion, MergeRequest, MergeConflict, AuditLog
from .serializers import (
    EditBranchSerializer,
    FeatureVersionSerializer,
    MergeRequestSerializer,
    MergeConflictSerializer
)
from .services import MergeService, ConflictDetector
import uuid


class EditBranchViewSet(viewsets.ModelViewSet):
    """
    API endpoints for managing edit branches.
    """
    serializer_class = EditBranchSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = EditBranch.objects.all()
        
        # Filter by layer
        layer_id = self.request.query_params.get('layer_id')
        if layer_id:
            queryset = queryset.filter(layer_id=layer_id)
        
        # Filter by user
        user_only = self.request.query_params.get('user_only')
        if user_only:
            queryset = queryset.filter(created_by=self.request.user)
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset.select_related('layer', 'created_by', 'parent_branch')
    
    def perform_create(self, serializer):
        branch = serializer.save(created_by=self.request.user)
        
        # Log action
        AuditLog.objects.create(
            user=self.request.user,
            action='CREATE_BRANCH',
            entity_type='branch',
            entity_id=branch.id,
            details={
                'branch_name': branch.name,
                'layer_id': str(branch.layer.id),
                'layer_name': branch.layer.name
            }
        )
    
    @action(detail=True, methods=['delete'])
    def soft_delete(self, request, pk=None):
        """Soft delete a branch by changing its status"""
        branch = self.get_object()
        
        # Check if user owns the branch or is admin
        if branch.created_by != request.user and not request.user.is_superuser:
            return Response(
                {'error': 'You do not have permission to delete this branch'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if branch.is_master():
            return Response(
                {'error': 'Cannot delete master branch'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        branch.status = 'deleted'
        branch.save()
        
        # Log action
        AuditLog.objects.create(
            user=request.user,
            action='DELETE_BRANCH',
            entity_type='branch',
            entity_id=branch.id,
            details={'branch_name': branch.name}
        )
        
        return Response({'message': 'Branch deleted successfully'})


class FeatureVersionViewSet(viewsets.ModelViewSet):
    """
    API endpoints for managing feature versions.
    """
    serializer_class = FeatureVersionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = FeatureVersion.objects.all()
        
        # Filter by branch
        branch_id = self.request.query_params.get('branch_id')
        if branch_id:
            queryset = queryset.filter(branch_id=branch_id)
        
        # Filter by feature_id
        feature_id = self.request.query_params.get('feature_id')
        if feature_id:
            queryset = queryset.filter(feature_id=feature_id)
        
        # Exclude deleted features by default
        include_deleted = self.request.query_params.get('include_deleted', 'false')
        if include_deleted.lower() != 'true':
            queryset = queryset.filter(is_deleted=False)
        
        return queryset.select_related('branch', 'created_by')
    
    def perform_create(self, serializer):
        """Create a new feature version"""
        feature = serializer.save(
            created_by=self.request.user,
            operation='CREATE',
            feature_id=uuid.uuid4(),
            version=1
        )
        
        # Log action
        AuditLog.objects.create(
            user=self.request.user,
            action='CREATE_FEATURE',
            entity_type='feature',
            entity_id=feature.id,
            details={
                'feature_id': str(feature.feature_id),
                'branch_id': str(feature.branch.id)
            }
        )
    
    def perform_update(self, serializer):
        """Update creates a new version of the feature"""
        old_feature = self.get_object()
        
        # Create new version
        feature = serializer.save(
            created_by=self.request.user,
            operation='UPDATE',
            feature_id=old_feature.feature_id,
            version=old_feature.version + 1
        )
        
        # Log action
        AuditLog.objects.create(
            user=self.request.user,
            action='UPDATE_FEATURE',
            entity_type='feature',
            entity_id=feature.id,
            details={
                'feature_id': str(feature.feature_id),
                'version': feature.version
            }
        )
    
    @action(detail=True, methods=['delete'])
    def soft_delete(self, request, pk=None):
        """Soft delete a feature by creating a delete version"""
        feature = self.get_object()
        
        # Create delete version
        delete_version = FeatureVersion.objects.create(
            branch=feature.branch,
            feature_id=feature.feature_id,
            version=feature.version + 1,
            geometry=feature.geometry,
            properties=feature.properties,
            operation='DELETE',
            is_deleted=True,
            created_by=request.user
        )
        
        # Log action
        AuditLog.objects.create(
            user=request.user,
            action='DELETE_FEATURE',
            entity_type='feature',
            entity_id=delete_version.id,
            details={'feature_id': str(feature.feature_id)}
        )
        
        return Response({'message': 'Feature deleted successfully'})
    
    @action(detail=False, methods=['get'])
    def history(self, request):
        """Get version history for a specific feature"""
        feature_id = request.query_params.get('feature_id')
        if not feature_id:
            return Response(
                {'error': 'feature_id parameter required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        versions = FeatureVersion.objects.filter(
            feature_id=feature_id
        ).order_by('version')
        
        serializer = self.get_serializer(versions, many=True)
        return Response(serializer.data)


class MergeRequestViewSet(viewsets.ModelViewSet):
    """
    API endpoints for managing merge requests.
    """
    serializer_class = MergeRequestSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = MergeRequest.objects.all()
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by layer
        layer_id = self.request.query_params.get('layer_id')
        if layer_id:
            queryset = queryset.filter(source_branch__layer_id=layer_id)
        
        return queryset.select_related(
            'source_branch',
            'target_branch',
            'created_by',
            'reviewed_by'
        ).prefetch_related('conflicts')
    
    def perform_create(self, serializer):
        """Create merge request and detect conflicts"""
        merge_request = serializer.save(created_by=self.request.user)
        
        # Detect conflicts
        conflict_detector = ConflictDetector()
        conflicts = conflict_detector.detect_conflicts(
            merge_request.source_branch,
            merge_request.target_branch
        )
        
        # Create conflict records
        for conflict_data in conflicts:
            MergeConflict.objects.create(
                merge_request=merge_request,
                **conflict_data
            )
        
        # Update merge request status if conflicts found
        if conflicts:
            merge_request.status = 'conflicts'
            merge_request.save()
        
        # Log action
        AuditLog.objects.create(
            user=self.request.user,
            action='CREATE_MERGE_REQUEST',
            entity_type='merge_request',
            entity_id=merge_request.id,
            details={
                'title': merge_request.title,
                'source_branch': str(merge_request.source_branch.id),
                'target_branch': str(merge_request.target_branch.id),
                'conflicts_count': len(conflicts)
            }
        )
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve and merge a merge request"""
        merge_request = self.get_object()
        
        # Check permissions
        if not self._can_approve(request.user):
            return Response(
                {'error': 'You do not have permission to approve merge requests'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check for unresolved conflicts
        unresolved_conflicts = merge_request.conflicts.filter(resolved=False).count()
        if unresolved_conflicts > 0:
            return Response(
                {'error': f'Cannot merge: {unresolved_conflicts} unresolved conflicts'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Perform merge
        merge_service = MergeService()
        try:
            merge_service.merge_branches(
                merge_request.source_branch,
                merge_request.target_branch
            )
            
            # Update merge request
            merge_request.status = 'merged'
            merge_request.reviewed_by = request.user
            merge_request.reviewed_at = timezone.now()
            merge_request.save()
            
            # Update source branch
            merge_request.source_branch.status = 'merged'
            merge_request.source_branch.merged_at = timezone.now()
            merge_request.source_branch.save()
            
            # Log action
            AuditLog.objects.create(
                user=request.user,
                action='APPROVE_MERGE_REQUEST',
                entity_type='merge_request',
                entity_id=merge_request.id,
                details={'status': 'merged'}
            )
            
            return Response({
                'message': 'Merge request approved and merged successfully',
                'merge_request': self.get_serializer(merge_request).data
            })
        except Exception as e:
            return Response(
                {'error': f'Merge failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject a merge request"""
        merge_request = self.get_object()
        
        # Check permissions
        if not self._can_approve(request.user):
            return Response(
                {'error': 'You do not have permission to reject merge requests'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Update merge request
        merge_request.status = 'rejected'
        merge_request.reviewed_by = request.user
        merge_request.reviewed_at = timezone.now()
        merge_request.review_comment = request.data.get('comment', '')
        merge_request.save()
        
        # Log action
        AuditLog.objects.create(
            user=request.user,
            action='REJECT_MERGE_REQUEST',
            entity_type='merge_request',
            entity_id=merge_request.id,
            details={'status': 'rejected'}
        )
        
        return Response({
            'message': 'Merge request rejected',
            'merge_request': self.get_serializer(merge_request).data
        })
    
    @action(detail=True, methods=['get'])
    def conflicts(self, request, pk=None):
        """Get conflicts for a merge request"""
        merge_request = self.get_object()
        conflicts = merge_request.conflicts.all()
        serializer = MergeConflictSerializer(conflicts, many=True)
        return Response(serializer.data)
    
    def _can_approve(self, user):
        """Check if user can approve merge requests"""
        return user.is_superuser or \
               (hasattr(user, 'profile') and 
                hasattr(user.profile, 'role') and
                user.profile.role in ['validator', 'admin'])
