"""
Business logic services for versioned editing.
Handles merge operations and conflict detection.
"""
from django.db import transaction
from django.contrib.gis.geos import GEOSGeometry
from .models import EditBranch, FeatureVersion, MergeConflict
import logging

logger = logging.getLogger(__name__)


class ConflictDetector:
    """
    Detects conflicts between two branches.
    """
    
    def detect_conflicts(self, source_branch, target_branch):
        """
        Detect conflicts between source and target branches.
        Returns a list of conflict data dictionaries.
        """
        conflicts = []
        
        # Get all feature versions from both branches
        source_features = self._get_latest_features(source_branch)
        target_features = self._get_latest_features(target_branch)
        
        # Check for conflicts
        for feature_id, source_version in source_features.items():
            if feature_id in target_features:
                target_version = target_features[feature_id]
                conflict_type = self._detect_conflict_type(source_version, target_version)
                
                if conflict_type:
                    conflicts.append({
                        'feature_id': feature_id,
                        'conflict_type': conflict_type,
                        'source_version': source_version,
                        'target_version': target_version,
                    })
        
        return conflicts
    
    def _get_latest_features(self, branch):
        """
        Get latest version of each feature in a branch.
        Returns a dictionary mapping feature_id to FeatureVersion.
        """
        features = {}
        versions = FeatureVersion.objects.filter(branch=branch).order_by('feature_id', '-version')
        
        for version in versions:
            if version.feature_id not in features:
                features[version.feature_id] = version
        
        return features
    
    def _detect_conflict_type(self, source_version, target_version):
        """
        Determine the type of conflict between two versions.
        Returns conflict type string or None if no conflict.
        """
        # If both are base version (version 1), no conflict
        if source_version.version == 1 and target_version.version == 1:
            return None
        
        # If both have been modified
        if source_version.version > 1 and target_version.version > 1:
            # Check for geometry conflict
            geom_conflict = not source_version.geometry.equals(target_version.geometry)
            # Check for properties conflict
            prop_conflict = source_version.properties != target_version.properties
            
            if geom_conflict and prop_conflict:
                return 'BOTH'
            elif geom_conflict:
                return 'GEOMETRY'
            elif prop_conflict:
                return 'PROPERTIES'
        
        # Check for delete conflicts
        if source_version.is_deleted and target_version.version > 1 and not target_version.is_deleted:
            return 'DELETE'
        if target_version.is_deleted and source_version.version > 1 and not source_version.is_deleted:
            return 'DELETE'
        
        return None


class MergeService:
    """
    Handles merging of branches.
    """
    
    @transaction.atomic
    def merge_branches(self, source_branch, target_branch):
        """
        Merge source branch into target branch.
        Creates new feature versions in target branch.
        """
        logger.info(f"Merging branch {source_branch.name} into {target_branch.name}")
        
        # Get latest features from source branch
        source_features = self._get_latest_features(source_branch)
        target_features = self._get_latest_features(target_branch)
        
        merged_count = 0
        
        for feature_id, source_version in source_features.items():
            # Skip deleted features
            if source_version.is_deleted:
                continue
            
            # Check if feature exists in target
            if feature_id in target_features:
                target_version = target_features[feature_id]
                # Create new version in target if source is newer or different
                if source_version.version > target_version.version or \
                   not self._versions_equal(source_version, target_version):
                    self._create_merged_version(source_version, target_branch)
                    merged_count += 1
            else:
                # Feature doesn't exist in target, add it
                self._create_merged_version(source_version, target_branch)
                merged_count += 1
        
        logger.info(f"Merged {merged_count} features from {source_branch.name} to {target_branch.name}")
        return merged_count
    
    def _get_latest_features(self, branch):
        """
        Get latest version of each feature in a branch.
        """
        features = {}
        versions = FeatureVersion.objects.filter(branch=branch).order_by('feature_id', '-version')
        
        for version in versions:
            if version.feature_id not in features:
                features[version.feature_id] = version
        
        return features
    
    def _versions_equal(self, version1, version2):
        """
        Check if two feature versions are equal.
        """
        return (
            version1.geometry.equals(version2.geometry) and
            version1.properties == version2.properties
        )
    
    def _create_merged_version(self, source_version, target_branch):
        """
        Create a merged version of a feature in the target branch.
        """
        # Get next version number in target branch
        latest_in_target = FeatureVersion.objects.filter(
            branch=target_branch,
            feature_id=source_version.feature_id
        ).order_by('-version').first()
        
        next_version = (latest_in_target.version + 1) if latest_in_target else 1
        
        # Create new version
        merged_version = FeatureVersion.objects.create(
            branch=target_branch,
            feature_id=source_version.feature_id,
            version=next_version,
            geometry=source_version.geometry,
            properties=source_version.properties,
            operation='MERGE',
            created_by=source_version.created_by,
            comment=f"Merged from branch {source_version.branch.name}"
        )
        
        return merged_version


class ConflictResolver:
    """
    Resolves conflicts in merge requests.
    """
    
    @transaction.atomic
    def resolve_conflict(self, conflict, resolution_strategy, resolved_by, 
                        manual_geometry=None, manual_properties=None):
        """
        Resolve a conflict using the specified strategy.
        
        Args:
            conflict: MergeConflict instance
            resolution_strategy: 'SOURCE', 'TARGET', or 'MANUAL'
            resolved_by: User resolving the conflict
            manual_geometry: Geometry for manual resolution (optional)
            manual_properties: Properties for manual resolution (optional)
        """
        if resolution_strategy == 'SOURCE':
            conflict.resolved_geometry = conflict.source_version.geometry
            conflict.resolved_properties = conflict.source_version.properties
        elif resolution_strategy == 'TARGET':
            conflict.resolved_geometry = conflict.target_version.geometry if conflict.target_version else None
            conflict.resolved_properties = conflict.target_version.properties if conflict.target_version else {}
        elif resolution_strategy == 'MANUAL':
            if manual_geometry is None or manual_properties is None:
                raise ValueError("Manual resolution requires geometry and properties")
            conflict.resolved_geometry = manual_geometry
            conflict.resolved_properties = manual_properties
        else:
            raise ValueError(f"Invalid resolution strategy: {resolution_strategy}")
        
        conflict.resolution_strategy = resolution_strategy
        conflict.resolved = True
        conflict.resolved_by = resolved_by
        conflict.resolved_at = timezone.now()
        conflict.save()
        
        logger.info(f"Resolved conflict {conflict.id} using {resolution_strategy} strategy")
        
        return conflict
