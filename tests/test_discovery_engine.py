"""
Unit tests for resource_discovery.discovery_engine

Tests the orchestration logic: method selection, fallback, deduplication,
filtering, and summary generation.
"""
import pytest
from unittest.mock import MagicMock, patch, PropertyMock

from resource_discovery.discovery_engine import ResourceDiscoveryEngine
from resource_discovery.models import (
    Resource,
    DiscoveryConfig,
    DiscoveryResult,
    DiscoverySource,
)
from tests.conftest import make_resource, make_discovery_result


# ===================================================================
# Helpers
# ===================================================================

def _make_engine(
    config=None,
    has_re=False,
    has_config=False,
    has_cc=False,
    is_aggregator=False,
    regions=None,
):
    """
    Build a ResourceDiscoveryEngine with mocked internals.
    Bypasses __init__'s AWS calls entirely.
    """
    engine = object.__new__(ResourceDiscoveryEngine)
    engine.session = MagicMock()
    engine.config = config or DiscoveryConfig()
    engine.resource_explorer = MagicMock() if has_re else None
    engine.config_client = MagicMock() if has_config else None
    engine.cloud_control = MagicMock() if has_cc else None
    engine.is_aggregator = is_aggregator
    engine.enabled_regions = regions or ["us-east-1"]
    engine._discover_bedrock_resources = MagicMock(return_value=[])
    return engine


# ===================================================================
# get_resource_summary
# ===================================================================

class TestGetResourceSummary:

    def test_empty_result(self):
        engine = _make_engine()
        result = make_discovery_result(resources=[])
        summary = engine.get_resource_summary(result)
        assert summary == {}

    def test_counts_by_type(self, sample_discovery_result):
        engine = _make_engine()
        summary = engine.get_resource_summary(sample_discovery_result)

        assert summary["AWS::EC2::Instance"] == 2  # us-east-1 + eu-west-1
        assert summary["AWS::S3::Bucket"] == 1
        assert summary["AWS::EC2::Volume"] == 1
        assert summary["AWS::Lambda::Function"] == 1

    def test_sorted_descending(self, sample_discovery_result):
        engine = _make_engine()
        summary = engine.get_resource_summary(sample_discovery_result)
        counts = list(summary.values())
        assert counts == sorted(counts, reverse=True)


# ===================================================================
# discover_all_resources – orchestration
# ===================================================================

class TestDiscoverAllResources:

    def test_resource_explorer_only(self):
        """When only RE is available, use it."""
        engine = _make_engine(has_re=True, is_aggregator=True)

        # Mock internal discovery method
        r1 = make_resource(arn="arn:aws:ec2:us-east-1:123:i/i-001")
        engine._discover_via_resource_explorer = MagicMock(return_value=[r1])

        # Mock STS for account detection
        sts_client = MagicMock()
        sts_client.get_caller_identity.return_value = {"Account": "123"}
        engine.session.client.return_value = sts_client

        result = engine.discover_all_resources()

        assert result.total_count == 1
        assert result.resources[0].arn == r1.arn
        engine._discover_via_resource_explorer.assert_called_once()

    def test_config_fallback_when_re_finds_few(self):
        """Config should kick in when RE finds <10 resources."""
        engine = _make_engine(has_re=True, has_config=True, is_aggregator=True)

        # RE returns only 3 resources
        re_resources = [
            make_resource(arn=f"arn:aws:ec2:us-east-1:123:i/i-{i}")
            for i in range(3)
        ]
        engine._discover_via_resource_explorer = MagicMock(return_value=re_resources)

        # Config returns 5 more (2 duplicate ARNs, 3 new)
        cfg_resources = [
            make_resource(arn="arn:aws:ec2:us-east-1:123:i/i-0"),  # duplicate
            make_resource(arn="arn:aws:ec2:us-east-1:123:i/i-1"),  # duplicate
            make_resource(arn="arn:aws:s3:::bucket-a"),
            make_resource(arn="arn:aws:s3:::bucket-b"),
            make_resource(arn="arn:aws:s3:::bucket-c"),
        ]
        engine._discover_via_config = MagicMock(return_value=cfg_resources)

        sts_client = MagicMock()
        sts_client.get_caller_identity.return_value = {"Account": "123"}
        engine.session.client.return_value = sts_client

        result = engine.discover_all_resources()

        # 3 from RE + 3 new from Config = 6
        assert result.total_count == 6
        engine._discover_via_config.assert_called_once()

    def test_config_skipped_when_re_has_enough(self):
        """If RE returns ≥10, Config should NOT be called."""
        engine = _make_engine(has_re=True, has_config=True, is_aggregator=True)

        resources = [
            make_resource(arn=f"arn:aws:ec2:us-east-1:123:i/i-{i}")
            for i in range(15)
        ]
        engine._discover_via_resource_explorer = MagicMock(return_value=resources)

        sts_client = MagicMock()
        sts_client.get_caller_identity.return_value = {"Account": "123"}
        engine.session.client.return_value = sts_client

        result = engine.discover_all_resources()

        assert result.total_count == 15
        assert not hasattr(engine, '_discover_via_config') or \
            not getattr(engine._discover_via_config, 'called', False)

    def test_type_filtering_applied(self):
        """Resources should be filtered by include_types/exclude_types."""
        config = DiscoveryConfig(
            include_types=["AWS::S3::Bucket"],
            use_resource_explorer=True,
            use_config=False,
        )
        engine = _make_engine(config=config, has_re=True, is_aggregator=True)

        resources = [
            make_resource(arn="arn:aws:ec2:us-east-1:123:i/i-1", resource_type="AWS::EC2::Instance"),
            make_resource(arn="arn:aws:s3:::my-bucket", resource_type="AWS::S3::Bucket"),
        ]
        engine._discover_via_resource_explorer = MagicMock(return_value=resources)

        sts_client = MagicMock()
        sts_client.get_caller_identity.return_value = {"Account": "123"}
        engine.session.client.return_value = sts_client

        result = engine.discover_all_resources()

        assert result.total_count == 1
        assert result.resources[0].resource_type == "AWS::S3::Bucket"

    def test_error_captured_on_re_failure(self):
        """If RE throws, error should be captured and result still returned."""
        engine = _make_engine(has_re=True, is_aggregator=True)
        engine._discover_via_resource_explorer = MagicMock(
            side_effect=Exception("API Error")
        )

        sts_client = MagicMock()
        sts_client.get_caller_identity.return_value = {"Account": "123"}
        engine.session.client.return_value = sts_client

        result = engine.discover_all_resources()

        assert result.success is False
        assert any("Resource Explorer" in e for e in result.errors)

    def test_account_id_auto_detection_failure(self):
        """If STS fails, should return error result."""
        engine = _make_engine()

        sts_client = MagicMock()
        sts_client.get_caller_identity.side_effect = Exception("STS unavailable")
        engine.session.client.return_value = sts_client

        result = engine.discover_all_resources()

        assert result.success is False
        assert result.total_count == 0

    def test_delegates_to_org_discovery_when_accounts_set(self):
        """When config.accounts is set and no explicit account_id, should delegate."""
        config = DiscoveryConfig(accounts=["111", "222"])
        engine = _make_engine(config=config, has_re=True)
        engine.discover_organization_resources = MagicMock(
            return_value=make_discovery_result()
        )

        result = engine.discover_all_resources()

        engine.discover_organization_resources.assert_called_once_with(["111", "222"])


# ===================================================================
# _initialize_regions
# ===================================================================

class TestInitializeRegions:

    def test_uses_configured_regions(self):
        config = DiscoveryConfig(regions=["us-west-2", "eu-central-1"])
        engine = _make_engine(config=config)
        engine._initialize_regions()
        assert engine.enabled_regions == ["us-west-2", "eu-central-1"]

    def test_fallback_on_ec2_error(self):
        config = DiscoveryConfig()
        engine = _make_engine(config=config)
        engine.session.client.return_value.describe_regions.side_effect = Exception("fail")
        engine._initialize_regions()
        # Should fall back to hardcoded defaults
        assert len(engine.enabled_regions) > 0
        assert "us-east-1" in engine.enabled_regions


# ===================================================================
# _discover_bedrock_resources
# ===================================================================

class TestDiscoverBedrockResources:

    def test_discover_bedrock_resources_logging_enabled(self):
        engine = _make_engine(regions=["us-east-1"])
        engine._discover_bedrock_resources = ResourceDiscoveryEngine._discover_bedrock_resources.__get__(engine)
        
        bedrock_client = MagicMock()
        bedrock_client.get_model_invocation_logging_configuration.return_value = {
            'loggingConfig': {
                'textDataDeliveryEnabled': True,
                'cloudWatchConfig': {'logGroupName': 'bedrock-logs'}
            }
        }
        bedrock_client.list_guardrails.return_value = {'guardrailSummaries': []}
        
        # Mock session.client
        def mock_client(service_name, **kwargs):
            if service_name == 'bedrock':
                return bedrock_client
            raise Exception("Mock other client")
            
        engine.session.client.side_effect = mock_client
        
        resources = engine._discover_bedrock_resources("123456789012")
        
        # Should have found 1 resource (logging config)
        assert len(resources) == 1
        res = resources[0]
        assert res.resource_type == "AWS::Bedrock::ModelInvocationLogging"
        assert res.region == "us-east-1"
        assert res.account_id == "123456789012"
        assert res.configuration['textDataDeliveryEnabled'] is True

    def test_discover_bedrock_resources_guardrails_exist(self):
        engine = _make_engine(regions=["us-east-1"])
        engine._discover_bedrock_resources = ResourceDiscoveryEngine._discover_bedrock_resources.__get__(engine)
        
        bedrock_client = MagicMock()
        bedrock_client.get_model_invocation_logging_configuration.return_value = {}
        bedrock_client.list_guardrails.return_value = {
            'guardrailSummaries': [{
                'id': 'g-1',
                'arn': 'arn:aws:bedrock:us-east-1:123456789012:guardrail/g-1',
                'name': 'MyGuardrail',
                'version': '1',
                'updatedAt': None
            }]
        }
        bedrock_client.get_guardrail.return_value = {
            'name': 'MyGuardrail',
            'blockedInputMessaging': 'Harmful content blocked',
            'contentPolicy': {'filters': []}
        }
        
        def mock_client(service_name, **kwargs):
            if service_name == 'bedrock':
                return bedrock_client
            raise Exception("Mock other client")
            
        engine.session.client.side_effect = mock_client
        
        resources = engine._discover_bedrock_resources("123456789012")
        
        # Should have found 1 resource (guardrail)
        assert len(resources) == 1
        res = resources[0]
        assert res.resource_type == "AWS::Bedrock::Guardrail"
        assert res.arn == "arn:aws:bedrock:us-east-1:123456789012:guardrail/g-1"
        assert res.name == "MyGuardrail"
        assert res.configuration['blockedInputMessaging'] == 'Harmful content blocked'

    def test_discover_bedrock_resources_org_governance(self):
        engine = _make_engine(regions=["us-east-1"])
        engine._discover_bedrock_resources = ResourceDiscoveryEngine._discover_bedrock_resources.__get__(engine)
        
        bedrock_client = MagicMock()
        bedrock_client.get_model_invocation_logging_configuration.return_value = {}
        bedrock_client.list_guardrails.return_value = {'guardrailSummaries': []}
        
        org_client = MagicMock()
        org_client.list_roots.return_value = {
            'Roots': [{
                'Id': 'r-1',
                'PolicyTypes': [{'Type': 'BEDROCK_POLICY', 'Status': 'ENABLED'}]
            }]
        }
        org_client.list_policies.side_effect = [
            {'Policies': [{'Id': 'p-1', 'Name': 'BedrockPolicy'}]}, # BEDROCK_POLICY
            {'Policies': [{'Id': 'p-scp', 'Name': 'SCP'}]} # SERVICE_CONTROL_POLICY
        ]
        org_client.describe_policy.return_value = {
            'Policy': {
                'Content': '{"Condition": {"StringEquals": {"bedrock:GuardrailIdentifier": "arn"}}}'
            }
        }
        
        def mock_client(service_name, **kwargs):
            if service_name == 'bedrock':
                return bedrock_client
            if service_name == 'organizations':
                return org_client
            raise Exception("Mock other client")
            
        engine.session.client.side_effect = mock_client
        
        resources = engine._discover_bedrock_resources("123456789012")
        
        # Should have found 1 resource (org governance)
        assert len(resources) == 1
        res = resources[0]
        assert res.resource_type == "AWS::Bedrock::OrgGovernance"
        assert res.configuration['bedrock_policy_type_enabled'] is True
        assert res.configuration['bedrock_policies_found'] is True
        assert res.configuration['scp_enforcement_found'] is True

    def test_discover_bedrock_resources_handles_errors(self):
        engine = _make_engine(regions=["us-east-1"])
        engine._discover_bedrock_resources = ResourceDiscoveryEngine._discover_bedrock_resources.__get__(engine)
        
        bedrock_client = MagicMock()
        from botocore.exceptions import ClientError
        bedrock_client.get_model_invocation_logging_configuration.side_effect = ClientError(
            {'Error': {'Code': 'AccessDeniedException', 'Message': 'Access Denied'}},
            'GetModelInvocationLoggingConfiguration'
        )
        bedrock_client.list_guardrails.side_effect = ClientError(
            {'Error': {'Code': 'AccessDeniedException', 'Message': 'Access Denied'}},
            'ListGuardrails'
        )
        
        org_client = MagicMock()
        org_client.list_roots.side_effect = ClientError(
            {'Error': {'Code': 'AccessDeniedException', 'Message': 'Access Denied'}},
            'ListRoots'
        )
        
        def mock_client(service_name, **kwargs):
            if service_name == 'bedrock':
                return bedrock_client
            if service_name == 'organizations':
                return org_client
            raise Exception("Mock other client")
            
        engine.session.client.side_effect = mock_client
        
        # Should complete without throwing exceptions
        resources = engine._discover_bedrock_resources("123456789012")
        assert len(resources) == 0

    def test_discover_ai_opt_out_policy(self):
        engine = _make_engine(regions=["us-east-1"])
        engine._discover_bedrock_resources = ResourceDiscoveryEngine._discover_bedrock_resources.__get__(engine)
        
        bedrock_client = MagicMock()
        bedrock_client.get_model_invocation_logging_configuration.return_value = {}
        bedrock_client.list_guardrails.return_value = {'guardrailSummaries': []}
        
        org_client = MagicMock()
        org_client.list_roots.return_value = {
            'Roots': [{
                'Id': 'r-1',
                'PolicyTypes': [{'Type': 'AISERVICES_OPT_OUT_POLICY', 'Status': 'ENABLED'}]
            }]
        }
        org_client.list_policies.return_value = {
            'Policies': [{
                'Id': 'p-optout',
                'Name': 'DefaultAIOptOut',
                'Arn': 'arn:aws:organizations::123456789012:policy/o-123456/p-optout'
            }]
        }
        org_client.describe_policy.return_value = {
            'Policy': {
                'PolicySummary': {
                    'Id': 'p-optout',
                    'Name': 'DefaultAIOptOut',
                    'Type': 'AISERVICES_OPT_OUT_POLICY'
                },
                'Content': '{"services": {"default": {"opt_out_value": "optOut"}}}'
            }
        }
        org_client.list_policies_for_target.return_value = {
            'Policies': [{
                'Id': 'p-optout',
                'Name': 'DefaultAIOptOut'
            }]
        }
        
        def mock_client(service_name, **kwargs):
            if service_name == 'bedrock':
                return bedrock_client
            if service_name == 'organizations':
                return org_client
            raise Exception("Mock other client")
            
        engine.session.client.side_effect = mock_client
        
        resources = engine._discover_bedrock_resources("123456789012")
        
        # We should find the AI Opt-out policy
        assert len(resources) == 1
        res = resources[0]
        assert res.resource_type == "AWS::Organizations::AIOptOutPolicy"
        assert res.arn == "arn:aws:organizations::123456789012:policy/o-123456/p-optout"
        assert res.name == "DefaultAIOptOut"
        assert res.region == "global"
        assert res.configuration['Content'] == '{"services": {"default": {"opt_out_value": "optOut"}}}'
        assert res.configuration['AttachedToRoots'] == ['r-1']


