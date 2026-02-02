"""
AWS Cloud Control API client wrapper
"""
import logging
from typing import List, Dict, Optional, Iterator
import json

import boto3
from botocore.exceptions import ClientError

from .models import Resource, DiscoverySource

logger = logging.getLogger(__name__)


class CloudControlClient:
    """Wrapper for AWS Cloud Control API"""
    
    def __init__(self, session: boto3.Session, region: str = 'us-east-1'):
        """
        Initialize Cloud Control API client.
        
        Args:
            session: Boto3 session
            region: AWS region
        """
        self.client = session.client('cloudcontrol', region_name=region)
        self.region = region
        logger.info(f"Initialized Cloud Control API client in {region}")
    
    def list_resources(
        self,
        type_name: str,
        max_results: int = 100
    ) -> Iterator[Dict]:
        """
        List resources of a specific type using Cloud Control API.
        
        Args:
            type_name: CloudFormation resource type (e.g., 'AWS::EC2::Instance')
            max_results: Maximum results per page
            
        Yields:
            Resource descriptions
        """
        try:
            paginator = self.client.get_paginator('list_resources')
            
            page_iterator = paginator.paginate(
                TypeName=type_name,
                PaginationConfig={
                    'MaxItems': None,
                    'PageSize': max_results
                }
            )
            
            total_count = 0
            for page in page_iterator:
                resource_descriptions = page.get('ResourceDescriptions', [])
                total_count += len(resource_descriptions)
                
                for resource_desc in resource_descriptions:
                    yield resource_desc
            
            logger.info(f"Found {total_count} resources of type {type_name}")
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'UnsupportedActionException':
                logger.warning(f"Resource type {type_name} not supported by Cloud Control API")
            elif error_code == 'TypeNotFoundException':
                logger.warning(f"Resource type {type_name} not found")
            else:
                logger.error(f"Error listing resources for {type_name}: {e}")
    
    def get_resource(
        self,
        type_name: str,
        identifier: str
    ) -> Optional[Dict]:
        """
        Get detailed information about a specific resource.
        
        Args:
            type_name: CloudFormation resource type
            identifier: Resource identifier
            
        Returns:
            Resource description or None
        """
        try:
            response = self.client.get_resource(
                TypeName=type_name,
                Identifier=identifier
            )
            
            return response.get('ResourceDescription')
            
        except ClientError as e:
            logger.error(f"Error getting resource {type_name}/{identifier}: {e}")
            return None
    
    def list_supported_resource_types(self) -> List[str]:
        """
        Get list of supported resource types.
        Note: Cloud Control API doesn't provide a direct way to list all types.
        This returns a curated list of commonly used types.
        
        Returns:
            List of resource type strings
        """
        # Common CloudFormation resource types supported by Cloud Control API
        return [
            'AWS::EC2::Instance',
            'AWS::EC2::Volume',
            'AWS::EC2::SecurityGroup',
            'AWS::EC2::VPC',
            'AWS::EC2::Subnet',
            'AWS::RDS::DBInstance',
            'AWS::RDS::DBCluster',
            'AWS::S3::Bucket',
            'AWS::Lambda::Function',
            'AWS::DynamoDB::Table',
            'AWS::ECS::Cluster',
            'AWS::ECS::Service',
            'AWS::EKS::Cluster',
            'AWS::ElasticLoadBalancingV2::LoadBalancer',
            'AWS::SNS::Topic',
            'AWS::SQS::Queue',
            'AWS::CloudFormation::Stack',
            'AWS::ApiGateway::RestApi',
            'AWS::CloudWatch::Alarm',
            'AWS::Events::Rule',
        ]
    
    def convert_to_resource(
        self,
        resource_desc: Dict,
        type_name: str
    ) -> Resource:
        """
        Convert Cloud Control API response to standardized Resource object.
        
        Args:
            resource_desc: Resource description from Cloud Control API
            type_name: CloudFormation resource type
            
        Returns:
            Standardized Resource object
        """
        identifier = resource_desc.get('Identifier', '')
        
        # Parse properties (JSON string)
        properties_str = resource_desc.get('Properties', '{}')
        try:
            properties = json.loads(properties_str)
        except json.JSONDecodeError:
            logger.error(f"Failed to parse properties for {identifier}")
            properties = {}
        
        # Extract common fields
        tags_list = properties.get('Tags', [])
        tags_dict = {}
        if isinstance(tags_list, list):
            for tag in tags_list:
                if isinstance(tag, dict):
                    key = tag.get('Key')
                    value = tag.get('Value')
                    if key:
                        tags_dict[key] = value
        
        # Try to get ARN from properties
        arn = properties.get('Arn') or properties.get('ARN')
        
        # Build ARN if not in properties
        if not arn:
            # Parse type name: AWS::Service::Resource
            parts = type_name.split('::')
            if len(parts) >= 3:
                service = parts[1].lower()
                resource_type_short = parts[2].lower()
                arn = f"arn:aws:{service}:{self.region}:unknown:{resource_type_short}/{identifier}"
        
        # Extract region and account from ARN
        region = self.region
        account_id = 'unknown'
        
        if arn:
            arn_parts = arn.split(':')
            if len(arn_parts) > 4:
                # Global resources have empty region field
                region = arn_parts[3] if arn_parts[3] else 'global'
                account_id = arn_parts[4]
        
        # Get resource name
        resource_name = (
            properties.get('Name') or
            properties.get('ResourceName') or
            properties.get('FunctionName') or
            properties.get('DBInstanceIdentifier') or
            properties.get('ClusterName') or
            identifier
        )
        
        return Resource(
            arn=arn,
            resource_type=type_name,
            region=region,
            account_id=account_id,
            name=resource_name,
            tags=tags_dict,
            configuration=properties,
            relationships=[],  # Cloud Control API doesn't provide relationships
            created_at=None,  # Not provided by Cloud Control API
            last_modified=None,
            source=DiscoverySource.CLOUD_CONTROL
        )
