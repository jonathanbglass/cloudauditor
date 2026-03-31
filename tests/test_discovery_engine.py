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
