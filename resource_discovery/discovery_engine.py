"""
Main resource discovery engine
Orchestrates discovery using Resource Explorer, Config, and Cloud Control API
"""
import logging
import time
from typing import List, Optional, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed

import boto3
from botocore.exceptions import ClientError

from .models import Resource, DiscoveryConfig, DiscoveryResult, DiscoverySource
from .resource_explorer_client import ResourceExplorerClient
from .config_client import ConfigClient
from .cloud_control_client import CloudControlClient

logger = logging.getLogger(__name__)


class ResourceDiscoveryEngine:
    """
    Intelligent resource discovery engine.
    Uses hybrid approach: Resource Explorer -> Config -> Cloud Control API
    Automatically handles multi-region discovery when needed.
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
        self.is_aggregator = False
        self.enabled_regions = []
        
        if self.config.use_resource_explorer:
            try:
                self.resource_explorer = ResourceExplorerClient(self.session)
                if not self.resource_explorer.check_index_exists():
                    logger.warning("Resource Explorer index not found, disabling")
                    self.resource_explorer = None
                else:
                    # Check if it's an aggregator index
                    self.is_aggregator = self.resource_explorer.is_aggregator_index()
                    if self.is_aggregator:
                        logger.info("Resource Explorer AGGREGATOR detected - will search all regions")
                    else:
                        logger.info("Resource Explorer LOCAL index detected - will query regions individually")
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
        
        # Get list of enabled regions for multi-region discovery
        self._initialize_regions()
        
        logger.info(f"Discovery engine initialized with: "
                   f"ResourceExplorer={self.resource_explorer is not None}, "
                   f"Config={self.config_client is not None}, "
                   f"CloudControl={self.cloud_control is not None}, "
                   f"Aggregator={self.is_aggregator}, "
                   f"Regions={len(self.enabled_regions)}")
    
    def _initialize_regions(self):
        """Get list of enabled AWS regions for multi-region discovery"""
        try:
            if self.config.regions:
                # Use user-specified regions
                self.enabled_regions = self.config.regions
                logger.info(f"Using {len(self.enabled_regions)} user-specified regions")
            else:
                # Get all enabled regions from EC2
                ec2 = self.session.client('ec2')
                response = ec2.describe_regions(AllRegions=False)
                self.enabled_regions = [r['RegionName'] for r in response['Regions']]
                logger.info(f"Discovered {len(self.enabled_regions)} enabled regions")
        except Exception as e:
            logger.warning(f"Failed to enumerate regions, using default: {e}")
            # Fallback to common regions
            self.enabled_regions = [
                'us-east-1', 'us-east-2', 'us-west-1', 'us-west-2',
                'eu-west-1', 'eu-central-1', 'ap-southeast-1', 'ap-northeast-1'
            ]
    
    def _get_assumed_role_session(
        self, 
        account_id: str, 
        role_name: str = "CloudAuditorExecutionRole"
    ) -> boto3.Session:
        """
        Get a boto3 session by assuming a role in another account.
        
        Args:
            account_id: Target AWS account ID
            role_name: Name of the role to assume
            
        Returns:
            Boto3 session with assumed role credentials
        """
        role_arn = f"arn:aws:iam::{account_id}:role/{role_name}"
        sts = self.session.client('sts')
        
        logger.info(f"Assuming role {role_arn}...")
        response = sts.assume_role(
            RoleArn=role_arn,
            RoleSessionName=f"CloudAuditorDiscovery-{account_id}"
        )
        
        credentials = response['Credentials']
        return boto3.Session(
            aws_access_key_id=credentials['AccessKeyId'],
            aws_secret_access_key=credentials['SecretAccessKey'],
            aws_session_token=credentials['SessionToken'],
            region_name=self.session.region_name
        )

    def discover_organization_resources(self, accounts: List[str]) -> DiscoveryResult:
        """
        Discover resources across multiple accounts.
        
        Args:
            accounts: List of AWS Account IDs
            
        Returns:
            Aggregate DiscoveryResult
        """
        total_result = DiscoveryResult(resources=[], total_count=0, success=True)
        start_time = time.time()
        
        for account_id in accounts:
            try:
                logger.info(f"--- Starting discovery for account: {account_id} ---")
                
                # If target is local account, use current session
                sts = self.session.client('sts')
                local_account = sts.get_caller_identity()['Account']
                
                if account_id == local_account:
                    engine = self
                else:
                    target_session = self._get_assumed_role_session(account_id)
                    engine = ResourceDiscoveryEngine(session=target_session, config=self.config)
                
                result = engine.discover_all_resources(account_id=account_id)
                total_result.resources.extend(result.resources)
                total_result.errors.extend(result.errors)
                
            except Exception as e:
                error_msg = f"Failed to discover account {account_id}: {str(e)}"
                logger.error(error_msg)
                total_result.add_error(error_msg)
        
        total_result.total_count = len(total_result.resources)
        total_result.duration_seconds = time.time() - start_time
        total_result.success = len(total_result.errors) == 0
        
        return total_result

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
        # If config specifies multiple accounts and we are in the hub, delegate
        if self.config.accounts and not account_id:
            return self.discover_organization_resources(self.config.accounts)

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
        
        # Always attempt custom Bedrock detection to enrich resources
        try:
            logger.info("Attempting custom Bedrock discovery...")
            bedrock_resources = self._discover_bedrock_resources(account_id)
            existing_arns = {r.arn for r in result.resources}
            new_bedrock_resources = [r for r in bedrock_resources if r.arn not in existing_arns]
            result.resources.extend(new_bedrock_resources)
            logger.info(f"Custom Bedrock discovery found {len(bedrock_resources)} resources ({len(new_bedrock_resources)} new)")
        except Exception as e:
            logger.error(f"Failed to run custom Bedrock discovery: {e}")
            result.add_error(f"Custom Bedrock discovery failed: {str(e)}")

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
        """
        Discover resources using Resource Explorer.
        Automatically handles multi-region discovery if LOCAL index detected.
        
        Args:
            account_id: AWS account ID
            
        Returns:
            List of discovered resources
        """
        if not self.resource_explorer:
            return []
        
        # If aggregator index, query once and get all regions
        if self.is_aggregator:
            logger.info("Using AGGREGATOR index for global discovery")
            resources = []
            
            # Build filters
            filters = {}
            if self.config.include_types:
                filters['resource_types'] = self.config.include_types
            
            # Query Resource Explorer
            for raw_resource in self.resource_explorer.list_all_resources(filters=filters):
                try:
                    resource = self.resource_explorer.convert_to_resource(raw_resource)
                    if resource.account_id == account_id or resource.account_id == 'unknown':
                        resources.append(resource)
                except Exception as e:
                    logger.warning(f"Failed to convert resource: {e}")
                    continue
            
            return resources
        
        # If LOCAL index, query each region individually
        logger.info(f"Using LOCAL index - querying {len(self.enabled_regions)} regions individually")
        all_resources = []
        
        for region in self.enabled_regions:
            try:
                logger.info(f"Discovering resources in {region}...")
                # Create region-specific Resource Explorer client
                regional_client = ResourceExplorerClient(self.session, region=region)
                
                # Check if index exists in this region
                if not regional_client.check_index_exists():
                    logger.debug(f"No Resource Explorer index in {region}, skipping")
                    continue
                
                # Build filters
                filters = {}
                if self.config.include_types:
                    filters['resource_types'] = self.config.include_types
                
                # Query Resource Explorer for this region
                for raw_resource in regional_client.list_all_resources(filters=filters):
                    try:
                        resource = regional_client.convert_to_resource(raw_resource)
                        if resource.account_id == account_id or resource.account_id == 'unknown':
                            all_resources.append(resource)
                    except Exception as e:
                        logger.warning(f"Failed to convert resource in {region}: {e}")
                        continue
                
                logger.info(f"Found {len(all_resources) - len([r for r in all_resources if r.region != region])} resources in {region}")
                
            except Exception as e:
                logger.warning(f"Failed to discover resources in {region}: {e}")
                continue
        
        logger.info(f"Multi-region discovery complete: {len(all_resources)} total resources")
        return all_resources
    
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

    def _discover_bedrock_resources(self, account_id: str) -> List[Resource]:
        """Discover Amazon Bedrock resources and custom compliance configurations"""
        resources = []
        
        session_region = self.session.region_name
        if not isinstance(session_region, str):
            session_region = 'us-east-1'
        regions_to_check = self.config.regions or [session_region]
        
        for region in regions_to_check:
            try:
                bedrock_client = self.session.client('bedrock', region_name=region)
                
                # 1. Model Invocation Logging Configuration
                try:
                    log_resp = bedrock_client.get_model_invocation_logging_configuration()
                    log_config = log_resp.get('loggingConfig')
                    if log_config:
                        resources.append(Resource(
                            arn=f"arn:aws:bedrock:{region}:{account_id}:logging-configuration/default",
                            resource_type="AWS::Bedrock::ModelInvocationLogging",
                            region=region,
                            account_id=account_id,
                            name="BedrockModelInvocationLogging",
                            tags={},
                            configuration=log_config,
                            source=DiscoverySource.CLOUD_CONTROL,
                            relationships=[]
                        ))
                except ClientError as e:
                    code = e.response['Error']['Code']
                    if code != 'AccessDeniedException':
                        logger.warning(f"Error fetching Bedrock logging configuration in {region}: {e}")
                
                # 2. Guardrails
                try:
                    guardrails_resp = bedrock_client.list_guardrails()
                    for g_summary in guardrails_resp.get('guardrailSummaries', []):
                        g_id = g_summary['id']
                        g_arn = g_summary['arn']
                        
                        try:
                            g_detail = bedrock_client.get_guardrail(
                                guardrailIdentifier=g_id,
                                guardrailVersion=g_summary.get('version', 'DRAFT')
                            )
                            config_data = {k: v for k, v in g_detail.items() if k not in ('ResponseMetadata',)}
                        except Exception as detail_err:
                            logger.warning(f"Could not get details for guardrail {g_id}: {detail_err}")
                            config_data = g_summary
                        
                        resources.append(Resource(
                            arn=g_arn,
                            resource_type="AWS::Bedrock::Guardrail",
                            region=region,
                            account_id=account_id,
                            name=g_summary.get('name'),
                            tags={},
                            configuration=config_data,
                            source=DiscoverySource.CLOUD_CONTROL,
                            relationships=[],
                            last_modified=g_summary.get('updatedAt')
                        ))
                except ClientError as e:
                    code = e.response['Error']['Code']
                    if code != 'AccessDeniedException':
                        logger.warning(f"Error listing Bedrock guardrails in {region}: {e}")
                        
            except Exception as e:
                logger.warning(f"Could not initialize Bedrock client for region {region}: {e}")

        # 3. AWS Organizations Governance (BEDROCK_POLICY / SCPs)
        try:
            org_client = self.session.client('organizations')
            roots = org_client.list_roots().get('Roots', [])
            
            bedrock_policy_enabled = False
            for root in roots:
                for p_type in root.get('PolicyTypes', []):
                    if p_type.get('Type') == 'BEDROCK_POLICY' and p_type.get('Status') == 'ENABLED':
                        bedrock_policy_enabled = True
                        break
            
            has_bedrock_policy = False
            policies_list = []
            if bedrock_policy_enabled:
                policies_list = org_client.list_policies(Filter='BEDROCK_POLICY').get('Policies', [])
                if policies_list:
                    has_bedrock_policy = True
            
            has_scp_enforcement = False
            scps = org_client.list_policies(Filter='SERVICE_CONTROL_POLICY').get('Policies', [])
            for scp in scps:
                policy_desc = org_client.describe_policy(PolicyId=scp['Id']).get('Policy', {})
                content_str = policy_desc.get('Content', '').lower()
                if 'bedrock:guardrailidentifier' in content_str:
                    has_scp_enforcement = True
                    policies_list.append(scp)
            
            if has_bedrock_policy or has_scp_enforcement:
                resources.append(Resource(
                    arn=f"arn:aws:organizations::{account_id}:governance/bedrock-org-policies",
                    resource_type="AWS::Bedrock::OrgGovernance",
                    region="global",
                    account_id=account_id,
                    name="BedrockOrganizationGovernance",
                    tags={},
                    configuration={
                        "bedrock_policy_type_enabled": bedrock_policy_enabled,
                        "bedrock_policies_found": has_bedrock_policy,
                        "scp_enforcement_found": has_scp_enforcement,
                        "policies": policies_list
                    },
                    source=DiscoverySource.CLOUD_CONTROL,
                    relationships=[]
                ))
        except ClientError as e:
            code = e.response['Error']['Code']
            if code not in ('AWSOrganizationsNotInUseException', 'AccessDeniedException'):
                logger.warning(f"Error checking Organizations policies: {e}")
        except Exception as e:
            logger.warning(f"Error checking Organizations governance: {e}")

        return resources

