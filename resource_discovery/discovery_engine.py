"""
Main resource discovery engine
Orchestrates discovery using Resource Explorer, Config, and Cloud Control API
"""
import logging
import time
from typing import List, Optional, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed

import boto3

from .models import Resource, DiscoveryConfig, DiscoveryResult, DiscoverySource
from .resource_explorer_client import ResourceExplorerClient
from .config_client import ConfigClient
from .cloud_control_client import CloudControlClient

logger = logging.getLogger(__name__)


class ResourceDiscoveryEngine:
    """
    Intelligent resource discovery engine.
    Uses hybrid approach: Resource Explorer -> Config -> Cloud Control API
    """
    
    def __init__(
        self,
        session: Optional[boto3.Session] = None,
        config: Optional[DiscoveryConfig] = None
    ):
        """
        Initialize discovery engine.
        
        Args:
            session: Boto3 session (creates default if None)
            config: Discovery configuration
        """
        self.session = session or boto3.Session()
        self.config = config or DiscoveryConfig()
        
        # Initialize clients based on config
        self.resource_explorer = None
        self.config_client = None
        self.cloud_control = None
        
        if self.config.use_resource_explorer:
            try:
                self.resource_explorer = ResourceExplorerClient(self.session)
                if not self.resource_explorer.check_index_exists():
                    logger.warning("Resource Explorer index not found, disabling")
                    self.resource_explorer = None
            except Exception as e:
                logger.error(f"Failed to initialize Resource Explorer: {e}")
                self.resource_explorer = None
        
        if self.config.use_config:
            try:
                self.config_client = ConfigClient(self.session)
                if not self.config_client.check_config_enabled():
                    logger.warning("AWS Config not enabled, disabling")
                    self.config_client = None
            except Exception as e:
                logger.error(f"Failed to initialize Config client: {e}")
                self.config_client = None
        
        if self.config.use_cloud_control:
            try:
                self.cloud_control = CloudControlClient(self.session)
            except Exception as e:
                logger.error(f"Failed to initialize Cloud Control client: {e}")
                self.cloud_control = None
        
        logger.info(f"Discovery engine initialized with: "
                   f"ResourceExplorer={self.resource_explorer is not None}, "
                   f"Config={self.config_client is not None}, "
                   f"CloudControl={self.cloud_control is not None}")
    
    def discover_all_resources(
        self,
        account_id: Optional[str] = None
    ) -> DiscoveryResult:
        """
        Discover all resources using intelligent hybrid approach.
        
        Args:
            account_id: AWS account ID (optional, auto-detected if None)
            
        Returns:
            DiscoveryResult with all discovered resources
        """
        start_time = time.time()
        
        # Auto-detect account ID if not provided
        if not account_id:
            try:
                sts = self.session.client('sts')
                account_id = sts.get_caller_identity()['Account']
                logger.info(f"Auto-detected account ID: {account_id}")
            except Exception as e:
                logger.error(f"Failed to detect account ID: {e}")
                return DiscoveryResult(
                    resources=[],
                    total_count=0,
                    success=False,
                    errors=[f"Failed to detect account ID: {str(e)}"]
                )
        
        result = DiscoveryResult(
            resources=[],
            total_count=0,
            success=True
        )
        
        # Try Resource Explorer first (fastest and most comprehensive)
        if self.resource_explorer:
            logger.info("Attempting discovery via Resource Explorer...")
            try:
                resources = self._discover_via_resource_explorer(account_id)
                result.resources.extend(resources)
                logger.info(f"Resource Explorer found {len(resources)} resources")
            except Exception as e:
                error_msg = f"Resource Explorer discovery failed: {str(e)}"
                logger.error(error_msg)
                result.add_error(error_msg)
        
        # Fall back to Config if Resource Explorer didn't work or found nothing
        if self.config_client and (not result.resources or len(result.resources) < 10):
            logger.info("Attempting discovery via AWS Config...")
            try:
                resources = self._discover_via_config(account_id)
                # Merge with existing resources (avoid duplicates by ARN)
                existing_arns = {r.arn for r in result.resources}
                new_resources = [r for r in resources if r.arn not in existing_arns]
                result.resources.extend(new_resources)
                logger.info(f"Config found {len(resources)} resources ({len(new_resources)} new)")
            except Exception as e:
                error_msg = f"Config discovery failed: {str(e)}"
                logger.error(error_msg)
                result.add_error(error_msg)
        
        # Use Cloud Control API as last resort for specific types
        if self.cloud_control and self.config.use_cloud_control:
            logger.info("Attempting discovery via Cloud Control API...")
            try:
                resources = self._discover_via_cloud_control(account_id)
                # Merge with existing resources
                existing_arns = {r.arn for r in result.resources}
                new_resources = [r for r in resources if r.arn not in existing_arns]
                result.resources.extend(new_resources)
                logger.info(f"Cloud Control found {len(resources)} resources ({len(new_resources)} new)")
            except Exception as e:
                error_msg = f"Cloud Control discovery failed: {str(e)}"
                logger.error(error_msg)
                result.add_error(error_msg)
        
        # Filter by resource types if configured
        if self.config.include_types or self.config.exclude_types:
            original_count = len(result.resources)
            result.resources = [
                r for r in result.resources
                if self.config.should_include_type(r.resource_type)
            ]
            filtered_count = original_count - len(result.resources)
            if filtered_count > 0:
                logger.info(f"Filtered out {filtered_count} resources based on type filters")
        
        result.total_count = len(result.resources)
        result.duration_seconds = time.time() - start_time
        
        logger.info(f"Discovery complete: {result.total_count} resources in "
                   f"{result.duration_seconds:.2f} seconds")
        
        return result
    
    def _discover_via_resource_explorer(self, account_id: str) -> List[Resource]:
        """Discover resources using Resource Explorer"""
        resources = []
        
        # Build filters
        filters = {}
        if self.config.regions:
            filters['regions'] = self.config.regions
        if self.config.include_types:
            filters['resource_types'] = self.config.include_types
        
        # List all resources
        for raw_resource in self.resource_explorer.list_all_resources(filters):
            try:
                resource = self.resource_explorer.convert_to_resource(raw_resource)
                if resource.account_id == account_id or resource.account_id == 'unknown':
                    resources.append(resource)
            except Exception as e:
                logger.error(f"Failed to convert resource: {e}")
        
        return resources
    
    def _discover_via_config(self, account_id: str) -> List[Resource]:
        """Discover resources using AWS Config"""
        resources = []
        
        # Get supported resource types
        resource_types = self.config_client.list_supported_resource_types()
        
        # Filter by configured types
        if self.config.include_types:
            resource_types = [
                rt for rt in resource_types
                if rt in self.config.include_types
            ]
        
        logger.info(f"Discovering {len(resource_types)} resource types via Config")
        
        # Use thread pool for parallel discovery
        with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
            futures = {
                executor.submit(
                    self._discover_config_resource_type,
                    resource_type,
                    account_id
                ): resource_type
                for resource_type in resource_types
            }
            
            for future in as_completed(futures):
                resource_type = futures[future]
                try:
                    type_resources = future.result()
                    resources.extend(type_resources)
                except Exception as e:
                    logger.error(f"Failed to discover {resource_type}: {e}")
        
        return resources
    
    def _discover_config_resource_type(
        self,
        resource_type: str,
        account_id: str
    ) -> List[Resource]:
        """Discover resources of a specific type using Config"""
        resources = []
        
        # List resource identifiers
        identifiers = self.config_client.list_discovered_resources(resource_type)
        
        # Get detailed config for each (sample only to avoid rate limits)
        sample_size = min(len(identifiers), 100)  # Limit to 100 per type
        
        for identifier in identifiers[:sample_size]:
            try:
                resource_id = identifier.get('resourceId')
                
                # For POC, we'll use basic info without fetching full config
                # to avoid rate limits
                resource = self.config_client.convert_to_resource(identifier)
                resources.append(resource)
                
            except Exception as e:
                logger.error(f"Failed to process {resource_type}/{resource_id}: {e}")
        
        return resources
    
    def _discover_via_cloud_control(self, account_id: str) -> List[Resource]:
        """Discover resources using Cloud Control API"""
        resources = []
        
        # Get supported resource types
        resource_types = self.cloud_control.list_supported_resource_types()
        
        # Filter by configured types
        if self.config.include_types:
            resource_types = [
                rt for rt in resource_types
                if rt in self.config.include_types
            ]
        
        logger.info(f"Discovering {len(resource_types)} resource types via Cloud Control")
        
        for resource_type in resource_types:
            try:
                for raw_resource in self.cloud_control.list_resources(resource_type):
                    try:
                        resource = self.cloud_control.convert_to_resource(
                            raw_resource,
                            resource_type
                        )
                        resources.append(resource)
                    except Exception as e:
                        logger.error(f"Failed to convert {resource_type} resource: {e}")
            except Exception as e:
                logger.error(f"Failed to list {resource_type}: {e}")
        
        return resources
    
    def get_resource_summary(self, result: DiscoveryResult) -> Dict[str, int]:
        """
        Get summary of discovered resources by type.
        
        Args:
            result: Discovery result
            
        Returns:
            Dictionary mapping resource type to count
        """
        summary = {}
        for resource in result.resources:
            resource_type = resource.resource_type
            summary[resource_type] = summary.get(resource_type, 0) + 1
        
        return dict(sorted(summary.items(), key=lambda x: x[1], reverse=True))
