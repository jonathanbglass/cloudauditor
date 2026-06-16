"""
Unit tests for resource_discovery.models

These are pure data-model tests with zero external dependencies.
"""
import pytest
from datetime import datetime

from resource_discovery.models import (
    Resource,
    DiscoveryConfig,
    DiscoveryResult,
    DiscoverySource,
)
from tests.conftest import make_resource, make_discovery_result


# ===================================================================
# Resource
# ===================================================================

class TestResource:
    """Tests for the Resource dataclass."""

    def test_default_values(self):
        """Minimal construction should fill sensible defaults."""
        r = Resource(
            arn="arn:aws:s3:::my-bucket",
            resource_type="AWS::S3::Bucket",
            region="global",
            account_id="123456789012",
        )
        assert r.name is None
        assert r.tags == {}
        assert r.configuration == {}
        assert r.relationships == []
        assert r.created_at is None
        assert r.last_modified is None
        assert r.source == DiscoverySource.RESOURCE_EXPLORER

    def test_to_dict_contains_all_fields(self, sample_resource):
        """to_dict() should return every expected key."""
        d = sample_resource.to_dict()
        expected_keys = {
            "arn", "resource_type", "region", "account_id",
            "name", "tags", "configuration", "relationships",
            "created_at", "last_modified", "discovery_source",
        }
        assert set(d.keys()) == expected_keys

    def test_to_dict_source_uses_value(self):
        """discovery_source should be the enum's .value string, not the enum."""
        r = make_resource(source=DiscoverySource.CONFIG)
        d = r.to_dict()
        assert d["discovery_source"] == "config"

    def test_to_dict_preserves_tags(self):
        """Tags dict should survive the round-trip."""
        tags = {"CostCenter": "12345", "Team": "platform"}
        r = make_resource(tags=tags)
        assert r.to_dict()["tags"] == tags

    def test_to_dict_preserves_configuration(self):
        """Configuration dict should survive the round-trip."""
        config = {"InstanceType": "m5.xlarge", "EbsOptimized": True}
        r = make_resource(configuration=config)
        assert r.to_dict()["configuration"] == config


# ===================================================================
# DiscoveryConfig
# ===================================================================

class TestDiscoveryConfig:
    """Tests for DiscoveryConfig filtering logic."""

    def test_defaults(self):
        cfg = DiscoveryConfig()
        assert cfg.use_resource_explorer is True
        assert cfg.use_config is True
        assert cfg.use_cloud_control is False
        assert cfg.include_types is None
        assert cfg.exclude_types == []
        assert cfg.regions is None
        assert cfg.batch_size == 100
        assert cfg.max_workers == 10
        assert cfg.max_retries == 3

    # -- should_include_type -----------------------------------------------

    def test_include_all_when_no_filters(self, default_config):
        """No include_types + no exclude_types → allow everything."""
        assert default_config.should_include_type("AWS::EC2::Instance") is True
        assert default_config.should_include_type("AWS::Lambda::Function") is True

    def test_include_types_allowlist(self):
        """Only types in the allow-list should pass."""
        cfg = DiscoveryConfig(include_types=["AWS::S3::Bucket", "AWS::EC2::Instance"])
        assert cfg.should_include_type("AWS::S3::Bucket") is True
        assert cfg.should_include_type("AWS::EC2::Instance") is True
        assert cfg.should_include_type("AWS::Lambda::Function") is False

    def test_exclude_types_blocklist(self):
        """Excluded types should be rejected even when include_types is None."""
        cfg = DiscoveryConfig(exclude_types=["AWS::IAM::User"])
        assert cfg.should_include_type("AWS::IAM::User") is False
        assert cfg.should_include_type("AWS::S3::Bucket") is True

    def test_exclude_takes_precedence_over_include(self):
        """If a type is in both include and exclude, exclude wins."""
        cfg = DiscoveryConfig(
            include_types=["AWS::EC2::Instance"],
            exclude_types=["AWS::EC2::Instance"],
        )
        assert cfg.should_include_type("AWS::EC2::Instance") is False


# ===================================================================
# DiscoveryResult
# ===================================================================

class TestDiscoveryResult:
    """Tests for DiscoveryResult aggregation helpers."""

    def test_add_error_flips_success(self):
        """Calling add_error() should set success to False."""
        result = make_discovery_result(success=True)
        assert result.success is True
        result.add_error("something broke")
        assert result.success is False
        assert "something broke" in result.errors

    def test_add_multiple_errors(self):
        result = make_discovery_result()
        result.add_error("err1")
        result.add_error("err2")
        assert len(result.errors) == 2

    def test_empty_result(self):
        result = make_discovery_result()
        assert result.total_count == 0
        assert result.resources == []
        assert result.success is True


# ===================================================================
# DiscoverySource enum
# ===================================================================

class TestDiscoverySource:
    def test_values(self):
        assert DiscoverySource.RESOURCE_EXPLORER.value == "resource_explorer"
        assert DiscoverySource.CONFIG.value == "config"
        assert DiscoverySource.CLOUD_CONTROL.value == "cloud_control"
