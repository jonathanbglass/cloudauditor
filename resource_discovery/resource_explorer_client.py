"""
AWS Resource Explorer client wrapper
"""
import logging
from typing import Iterator, Dict, List, Optional
from datetime import datetime

import boto3
from botocore.exceptions import ClientError

from .models import Resource, DiscoverySource

logger = logging.getLogger(__name__)


class ResourceExplorerClient:
    """Wrapper for AWS Resource Explorer API"""
    
    def __init__(self, session: boto3.Session, region: str = 'us-east-1'):
        """
        Initialize Resource Explorer client.
        
        Args:
            session: Boto3 session
            region: AWS region (Resource Explorer is regional but searches globally)
        """
        self.client = session.client('resource-explorer-2', region_name=region)
        self.region = region
        logger.info(f"Initialized Resource Explorer client in {region}")
    
    def check_index_exists(self) -> bool:
        """
        Check if Resource Explorer index exists.
        
        Returns:
            True if index exists, False otherwise
        """
        try:
            response = self.client.list_indexes()
            return len(response.get('Indexes', [])) > 0
        except ClientError as e:
            logger.error(f"Error checking Resource Explorer index: {e}")
            return False
    
    def is_aggregator_index(self) -> bool:
        """
        Check if Resource Explorer index is an AGGREGATOR (searches all regions).
        
        Returns:
            True if aggregator index exists, False if LOCAL or no index
        """
        try:
            response = self.client.get_index()
            index_type = response.get('Type', 'LOCAL')
            logger.info(f"Resource Explorer index type: {index_type}")
            return index_type == 'AGGREGATOR'
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'ResourceNotFoundException':
                logger.warning("No Resource Explorer index found in this region")
            else:
                logger.error(f"Error checking index type: {e}")
            return False
    
    def list_all_resources(
        self,
        filters: Optional[Dict] = None,
        max_results: int = 1000
    ) -> Iterator[Dict]:
        """
        List all resources using Resource Explorer ListResources API.
        Handles pagination automatically.
        
        Args:
            filters: Optional filters (tags, resource types, etc.)
            max_results: Maximum results per page (max 1000)
            
        Yields:
            Resource dictionaries
        """
        try:
            paginator = self.client.get_paginator('search')
            
            # Build query string
            query_string = self._build_query_string(filters)
            
            logger.info(f"Searching resources with query: {query_string}")
            
            page_iterator = paginator.paginate(
                QueryString=query_string,
                PaginationConfig={
                    'MaxItems': None,  # Get all results
                    'PageSize': max_results
                }
            )
            
            total_count = 0
            for page in page_iterator:
                resources = page.get('Resources', [])
                total_count += len(resources)
                
                for resource in resources:
                    yield resource
            
            logger.info(f"Found {total_count} total resources")
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'UnauthorizedException':
                logger.error("Resource Explorer not enabled or insufficient permissions")
            else:
                logger.error(f"Error listing resources: {e}")
            raise
    
    def _build_query_string(self, filters: Optional[Dict] = None) -> str:
        """
        Build Resource Explorer query string.
        
        Args:
            filters: Optional filters
            
        Returns:
            Query string
        """
        if not filters:
            return "*"  # Match all resources
        
        query_parts = []
        
        # Resource type filter
        if 'resource_types' in filters:
            types = filters['resource_types']
            if isinstance(types, list):
                type_queries = [f"resourcetype:{t}" for t in types]
                query_parts.append(f"({' OR '.join(type_queries)})")
            else:
                query_parts.append(f"resourcetype:{types}")
        
        # Tag filters
        if 'tags' in filters:
            for key, value in filters['tags'].items():
                query_parts.append(f"tag:{key}={value}")
        
        # Region filter
        if 'regions' in filters:
            regions = filters['regions']
            if isinstance(regions, list):
                region_queries = [f"region:{r}" for r in regions]
                query_parts.append(f"({' OR '.join(region_queries)})")
            else:
                query_parts.append(f"region:{regions}")
        
        return " AND ".join(query_parts) if query_parts else "*"
    
    def get_resource_details(self, arn: str) -> Optional[Dict]:
        """
        Get detailed information about a specific resource.
        
        Args:
            arn: Resource ARN
            
        Returns:
            Resource details or None if not found
        """
        try:
            response = self.client.get_resource(
                ResourceArn=arn
            )
            return response.get('Resource')
        except ClientError as e:
            logger.error(f"Error getting resource details for {arn}: {e}")
            return None
    
    def list_supported_resource_types(self) -> List[str]:
        """
        Get list of supported resource types.
        
        Returns:
            List of resource type strings
        """
        try:
            # Search for all resources and extract unique types
            # Note: There's no direct API to list supported types
            # This is a workaround
            resources = list(self.list_all_resources(max_results=100))
            types = set()
            for resource in resources:
                resource_type = resource.get('ResourceType')
                if resource_type:
                    types.add(resource_type)
            
            return sorted(list(types))
        except Exception as e:
            logger.error(f"Error listing resource types: {e}")
            return []
    
    def convert_to_resource(self, raw_resource: Dict) -> Resource:
        """
        Convert Resource Explorer response to standardized Resource object.
        
        Args:
            raw_resource: Raw resource from Resource Explorer API
            
        Returns:
            Standardized Resource object
        """
        arn = raw_resource.get('Arn', '')
        
        # Parse ARN to extract account and region
        # ARN format: arn:aws:service:region:account-id:resource-type/resource-id
        # Global resources (IAM, S3, CloudFront, etc.) have empty region field
        arn_parts = arn.split(':')
        region = arn_parts[3] if len(arn_parts) > 3 and arn_parts[3] else 'global'
        account_id = arn_parts[4] if len(arn_parts) > 4 else 'unknown'
        
        # Extract properties
        properties = raw_resource.get('Properties', [])
        tags = {}
        configuration = {}
        
        for prop in properties:
            name = prop.get('Name', '')
            data = prop.get('Data')
            
            if name.startswith('tag:'):
                tag_key = name[4:]  # Remove 'tag:' prefix
                tags[tag_key] = data
            else:
                configuration[name] = data
        
        # Get resource name from properties or ARN
        resource_name = None
        for prop in properties:
            if prop.get('Name') in ['Name', 'name', 'ResourceName']:
                resource_name = prop.get('Data')
                break
        
        return Resource(
            arn=arn,
            resource_type=raw_resource.get('ResourceType', 'Unknown'),
            region=region,
            account_id=account_id,
            name=resource_name,
            tags=tags,
            configuration=configuration,
            relationships=[],  # Resource Explorer doesn't provide relationships
            created_at=None,  # Not provided by Resource Explorer
            last_modified=raw_resource.get('LastReportedAt'),
            source=DiscoverySource.RESOURCE_EXPLORER
        )
