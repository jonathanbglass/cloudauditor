"""
AWS Config client wrapper
"""
import logging
from typing import List, Dict, Optional
from datetime import datetime

import boto3
from botocore.exceptions import ClientError

from .models import Resource, DiscoverySource

logger = logging.getLogger(__name__)


class ConfigClient:
    """Wrapper for AWS Config API"""
    
    def __init__(self, session: boto3.Session, region: str = 'us-east-1'):
        """
        Initialize Config client.
        
        Args:
            session: Boto3 session
            region: AWS region
        """
        self.client = session.client('config', region_name=region)
        self.region = region
        logger.info(f"Initialized Config client in {region}")
    
    def check_config_enabled(self) -> bool:
        """
        Check if AWS Config is enabled.
        
        Returns:
            True if Config is enabled, False otherwise
        """
        try:
            response = self.client.describe_configuration_recorders()
            recorders = response.get('ConfigurationRecorders', [])
            
            if not recorders:
                logger.warning("No Config recorders found")
                return False
            
            # Check if recorder is recording
            status_response = self.client.describe_configuration_recorder_status()
            statuses = status_response.get('ConfigurationRecordersStatus', [])
            
            for status in statuses:
                if status.get('recording'):
                    logger.info("Config is enabled and recording")
                    return True
            
            logger.warning("Config recorders exist but not recording")
            return False
            
        except ClientError as e:
            logger.error(f"Error checking Config status: {e}")
            return False
    
    def list_discovered_resources(
        self,
        resource_type: str,
        include_deleted: bool = False
    ) -> List[Dict]:
        """
        List discovered resources of a specific type.
        
        Args:
            resource_type: AWS resource type (e.g., 'AWS::EC2::Instance')
            include_deleted: Include deleted resources
            
        Returns:
            List of resource identifiers
        """
        try:
            resources = []
            paginator = self.client.get_paginator('list_discovered_resources')
            
            page_iterator = paginator.paginate(
                resourceType=resource_type,
                includeDeletedResources=include_deleted
            )
            
            for page in page_iterator:
                resource_identifiers = page.get('resourceIdentifiers', [])
                resources.extend(resource_identifiers)
            
            logger.info(f"Found {len(resources)} resources of type {resource_type}")
            return resources
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'NoSuchConfigurationRecorderException':
                logger.error("AWS Config not enabled")
            else:
                logger.error(f"Error listing resources for {resource_type}: {e}")
            return []
    
    def get_resource_config(
        self,
        resource_type: str,
        resource_id: str
    ) -> Optional[Dict]:
        """
        Get detailed configuration for a specific resource.
        
        Args:
            resource_type: AWS resource type
            resource_id: Resource ID
            
        Returns:
            Resource configuration or None
        """
        try:
            response = self.client.get_resource_config_history(
                resourceType=resource_type,
                resourceId=resource_id,
                limit=1,
                laterTime=datetime.now()
            )
            
            config_items = response.get('configurationItems', [])
            if config_items:
                return config_items[0]
            
            return None
            
        except ClientError as e:
            logger.error(f"Error getting config for {resource_type}/{resource_id}: {e}")
            return None
    
    def list_supported_resource_types(self) -> List[str]:
        """
        Get list of supported resource types.
        
        Returns:
            List of resource type strings
        """
        try:
            # Config has a fixed list of supported types
            # This is a subset of common types
            response = self.client.describe_configuration_recorders()
            recorders = response.get('ConfigurationRecorders', [])
            
            if not recorders:
                return []
            
            # Get recording group
            recorder = recorders[0]
            recording_group = recorder.get('recordingGroup', {})
            
            if recording_group.get('allSupported', False):
                # Return common resource types if all are supported
                return self._get_common_resource_types()
            else:
                # Return specific resource types being recorded
                return recording_group.get('resourceTypes', [])
                
        except ClientError as e:
            logger.error(f"Error listing resource types: {e}")
            return []
    
    def _get_common_resource_types(self) -> List[str]:
        """Get list of common AWS Config resource types"""
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
            'AWS::IAM::User',
            'AWS::IAM::Role',
            'AWS::IAM::Policy',
            'AWS::DynamoDB::Table',
            'AWS::ECS::Cluster',
            'AWS::ECS::Service',
            'AWS::EKS::Cluster',
            'AWS::ElasticLoadBalancingV2::LoadBalancer',
            'AWS::CloudFormation::Stack',
            'AWS::SNS::Topic',
            'AWS::SQS::Queue',
        ]
    
    def convert_to_resource(
        self,
        resource_identifier: Dict,
        config_item: Optional[Dict] = None
    ) -> Resource:
        """
        Convert Config response to standardized Resource object.
        
        Args:
            resource_identifier: Resource identifier from list_discovered_resources
            config_item: Optional configuration item from get_resource_config_history
            
        Returns:
            Standardized Resource object
        """
        resource_type = resource_identifier.get('resourceType', 'Unknown')
        resource_id = resource_identifier.get('resourceId', '')
        resource_name = resource_identifier.get('resourceName')
        
        # Build ARN if not provided
        arn = None
        if config_item:
            arn = config_item.get('arn') or config_item.get('ARN')
            configuration = config_item.get('configuration', {})
            tags_dict = config_item.get('tags', {})
            relationships = [
                rel.get('resourceId', '') 
                for rel in config_item.get('relationships', [])
            ]
            created_time = config_item.get('resourceCreationTime')
            modified_time = config_item.get('configurationItemCaptureTime')
        else:
            configuration = {}
            tags_dict = {}
            relationships = []
            created_time = None
            modified_time = None
        
        # Parse region and account from resource type or ARN
        region = self.region
        account_id = 'unknown'
        
        if arn:
            arn_parts = arn.split(':')
            if len(arn_parts) > 4:
                region = arn_parts[3]
                account_id = arn_parts[4]
        
        return Resource(
            arn=arn or f"arn:aws:{resource_type}:{region}:{account_id}:{resource_id}",
            resource_type=resource_type,
            region=region,
            account_id=account_id,
            name=resource_name,
            tags=tags_dict,
            configuration=configuration,
            relationships=relationships,
            created_at=created_time,
            last_modified=modified_time,
            source=DiscoverySource.CONFIG
        )
