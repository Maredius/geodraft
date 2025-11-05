"""
REST framework serializers for versioned editing.
"""
from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer
from .models import EditBranch, FeatureVersion, MergeRequest, MergeConflict


class EditBranchSerializer(serializers.ModelSerializer):
    """Serializer for EditBranch model"""
    layer_name = serializers.CharField(source='layer.name', read_only=True)
    creator_username = serializers.CharField(source='created_by.username', read_only=True)
    parent_branch_name = serializers.CharField(source='parent_branch.name', read_only=True, allow_null=True)
    
    class Meta:
        model = EditBranch
        fields = [
            'id', 'name', 'description', 'layer', 'layer_name',
            'parent_branch', 'parent_branch_name', 'created_by',
            'creator_username', 'status', 'created_at', 'merged_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'merged_at', 'updated_at']


class FeatureVersionSerializer(GeoFeatureModelSerializer):
    """Serializer for FeatureVersion model with GeoJSON support"""
    branch_name = serializers.CharField(source='branch.name', read_only=True)
    creator_username = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = FeatureVersion
        geo_field = 'geometry'
        fields = [
            'id', 'branch', 'branch_name', 'feature_id', 'version',
            'geometry', 'properties', 'operation', 'is_deleted',
            'created_by', 'creator_username', 'created_at', 'comment'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'feature_id', 'version']


class MergeConflictSerializer(serializers.ModelSerializer):
    """Serializer for MergeConflict model"""
    source_version_data = FeatureVersionSerializer(source='source_version', read_only=True)
    target_version_data = FeatureVersionSerializer(source='target_version', read_only=True)
    
    class Meta:
        model = MergeConflict
        fields = [
            'id', 'merge_request', 'feature_id', 'conflict_type',
            'source_version', 'source_version_data',
            'target_version', 'target_version_data',
            'resolved', 'resolution_strategy',
            'resolved_geometry', 'resolved_properties',
            'resolved_by', 'resolved_at'
        ]
        read_only_fields = ['id', 'merge_request', 'resolved_at']


class MergeRequestSerializer(serializers.ModelSerializer):
    """Serializer for MergeRequest model"""
    source_branch_name = serializers.CharField(source='source_branch.name', read_only=True)
    target_branch_name = serializers.CharField(source='target_branch.name', read_only=True)
    layer_name = serializers.CharField(source='source_branch.layer.name', read_only=True)
    creator_username = serializers.CharField(source='created_by.username', read_only=True)
    reviewer_username = serializers.CharField(source='reviewed_by.username', read_only=True, allow_null=True)
    conflicts_count = serializers.SerializerMethodField()
    
    class Meta:
        model = MergeRequest
        fields = [
            'id', 'source_branch', 'source_branch_name',
            'target_branch', 'target_branch_name', 'layer_name',
            'title', 'description', 'status',
            'created_by', 'creator_username',
            'reviewed_by', 'reviewer_username', 'review_comment',
            'conflicts_count',
            'created_at', 'updated_at', 'reviewed_at'
        ]
        read_only_fields = [
            'id', 'created_by', 'reviewed_by', 'status',
            'created_at', 'updated_at', 'reviewed_at'
        ]
    
    def get_conflicts_count(self, obj):
        """Get count of conflicts for this merge request"""
        return obj.conflicts.count()
    
    def validate(self, data):
        """Validate merge request data"""
        source = data.get('source_branch')
        target = data.get('target_branch')
        
        if source == target:
            raise serializers.ValidationError("Source and target branches must be different")
        
        if source.layer != target.layer:
            raise serializers.ValidationError("Branches must belong to the same layer")
        
        return data
