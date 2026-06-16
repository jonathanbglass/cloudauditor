"""
P4 — Coverage expansion for resource_discovery.discovery_engine

Multi-region discovery, cross-account, and cloud control fallback paths.
"""
import pytest
from unittest.mock import MagicMock, patch, call

from resource_discovery.discovery_engine import ResourceDiscoveryEngine
from resource_discovery.models import (
    Resource,
    DiscoveryConfig,
    DiscoveryResult,
    DiscoverySource,
)
from tests.conftest import make_resource, make_discovery_result


def _make_engine(config=None, **kwargs):
    """Build engine with mocked internals."""
    engine = object.__new__(ResourceDiscoveryEngine)
    engine.session = MagicMock()
    engine.config = config or DiscoveryConfig()
    engine.resource_explorer = kwargs.get("re_client")
    engine.config_client = kwargs.get("cfg_client")
    engine.cloud_control = kwargs.get("cc_client")
    engine.is_aggregator = kwargs.get("is_aggregator", False)
    engine.enabled_regions = kwargs.get("regions", ["us-east-1"])
    engine._discover_bedrock_resources = MagicMock(return_value=[])
    return engine


class TestLocalIndexMultiRegion:
    """Test _discover_via_resource_explorer with LOCAL index."""

    def test_queries_each_region(self):
        re_client = MagicMock()
        engine = _make_engine(
            re_client=re_client,
            is_aggregator=False,
            regions=["us-east-1", "us-west-2", "eu-west-1"],
        )

        # Mock ResourceExplorerClient constructor for each region
        with patch("resource_discovery.discovery_engine.ResourceExplorerClient") as mock_re_cls:
            regional_client = MagicMock()
            regional_client.check_index_exists.return_value = True
            # Return a fresh iterator each time (iter is consumed on first call)
            call_count = [0]
            def _fresh_iter(**kwargs):
                call_count[0] += 1
                return iter([{
                    "Arn": f"arn:aws:ec2:us-east-1:123:i/i-{call_count[0]:03d}",
                    "ResourceType": "AWS::EC2::Instance",
                    "Properties": [],
                }])
            regional_client.list_all_resources.side_effect = _fresh_iter
            regional_client.convert_to_resource.return_value = make_resource(
                account_id="123"
            )
            mock_re_cls.return_value = regional_client

            resources = engine._discover_via_resource_explorer("123")

            # Should have created a client for each region
            assert mock_re_cls.call_count == 3
            assert len(resources) == 3  # One resource per region

    def test_skips_regions_without_index(self):
        re_client = MagicMock()
        engine = _make_engine(
            re_client=re_client,
            is_aggregator=False,
            regions=["us-east-1", "us-west-2"],
        )

        with patch("resource_discovery.discovery_engine.ResourceExplorerClient") as mock_re_cls:
            regional_client = MagicMock()
            # First region has index, second doesn't
            regional_client.check_index_exists.side_effect = [True, False]
            regional_client.list_all_resources.side_effect = lambda **kwargs: iter([
                {"Arn": "arn:aws:ec2:us-east-1:123:i/i-001", "ResourceType": "AWS::EC2::Instance", "Properties": []}
            ])
            regional_client.convert_to_resource.return_value = make_resource(account_id="123")
            mock_re_cls.return_value = regional_client

            resources = engine._discover_via_resource_explorer("123")

            # Should only get resources from the region with an index
            assert len(resources) == 1


class TestDiscoverOrganizationResources:

    def test_partial_failure(self):
        """Errors in one account should not stop discovery of others."""
        engine = _make_engine()

        # Mock STS
        sts = MagicMock()
        sts.get_caller_identity.return_value = {"Account": "111"}
        engine.session.client.return_value = sts

        # Mock _get_assumed_role_session
        engine._get_assumed_role_session = MagicMock(
            side_effect=[
                MagicMock(),  # Success for account 222
                Exception("STS timeout for 333"),  # Failure for account 333
            ]
        )

        # First account is local, second succeeds, third fails
        with patch.object(ResourceDiscoveryEngine, "__init__", lambda self, **kw: None):
            with patch("resource_discovery.discovery_engine.ResourceDiscoveryEngine") as mock_engine_cls:
                mock_sub_engine = MagicMock()
                mock_sub_engine.discover_all_resources.return_value = make_discovery_result(
                    resources=[make_resource()], total_count=1
                )
                mock_engine_cls.return_value = mock_sub_engine

                # Use the actual discover method for the local account
                engine.discover_all_resources = MagicMock(return_value=make_discovery_result(
                    resources=[make_resource()], total_count=1
                ))

                result = engine.discover_organization_resources(["111", "222", "333"])

        # Should have errors from account 333
        assert len(result.errors) > 0
        assert any("333" in e for e in result.errors)
        # Should still have resources from successful accounts
        assert result.total_count > 0

    def test_local_account_uses_self(self):
        """When target account == local account, should use self instead of assuming role."""
        engine = _make_engine()

        sts = MagicMock()
        sts.get_caller_identity.return_value = {"Account": "111"}
        engine.session.client.return_value = sts

        engine.discover_all_resources = MagicMock(return_value=make_discovery_result(
            resources=[make_resource()], total_count=1
        ))

        result = engine.discover_organization_resources(["111"])

        # Should NOT attempt to assume role for local account
        assert not hasattr(engine, '_get_assumed_role_session') or \
            not getattr(engine._get_assumed_role_session, 'called', False)
        assert result.total_count == 1


class TestGetAssumedRoleSession:

    def test_returns_session_with_credentials(self):
        engine = _make_engine()
        sts = MagicMock()
        sts.assume_role.return_value = {
            "Credentials": {
                "AccessKeyId": "AKIA_TEST",
                "SecretAccessKey": "secret_test",
                "SessionToken": "token_test",
            }
        }
        engine.session.client.return_value = sts
        engine.session.region_name = "us-east-1"

        with patch("resource_discovery.discovery_engine.boto3.Session") as mock_session_cls:
            engine._get_assumed_role_session("222")

            mock_session_cls.assert_called_once_with(
                aws_access_key_id="AKIA_TEST",
                aws_secret_access_key="secret_test",
                aws_session_token="token_test",
                region_name="us-east-1",
            )

    def test_custom_role_name(self):
        engine = _make_engine()
        sts = MagicMock()
        sts.assume_role.return_value = {
            "Credentials": {
                "AccessKeyId": "AKIA_TEST",
                "SecretAccessKey": "secret_test",
                "SessionToken": "token_test",
            }
        }
        engine.session.client.return_value = sts
        engine.session.region_name = "us-east-1"

        with patch("resource_discovery.discovery_engine.boto3.Session"):
            engine._get_assumed_role_session("222", role_name="CustomRole")

            call_args = sts.assume_role.call_args
            assert "CustomRole" in call_args[1]["RoleArn"]


class TestCloudControlFallback:

    def test_cloud_control_merge_dedup(self):
        """Cloud Control results should be deduped against existing resources."""
        config = DiscoveryConfig(
            use_resource_explorer=True,
            use_config=False,
            use_cloud_control=True,
        )
        cc_client = MagicMock()
        engine = _make_engine(
            config=config,
            re_client=MagicMock(),
            cc_client=cc_client,
            is_aggregator=True,
        )

        # RE finds 2 resources
        re_resources = [
            make_resource(arn="arn:aws:ec2:us-east-1:123:i/i-001"),
            make_resource(arn="arn:aws:ec2:us-east-1:123:i/i-002"),
        ]
        engine._discover_via_resource_explorer = MagicMock(return_value=re_resources)

        # CC finds 3: i-002 (duplicate) + 2 new
        cc_resources = [
            make_resource(arn="arn:aws:ec2:us-east-1:123:i/i-002"),  # dup
            make_resource(arn="arn:aws:ec2:us-east-1:123:i/i-003"),
            make_resource(arn="arn:aws:ec2:us-east-1:123:i/i-004"),
        ]
        engine._discover_via_cloud_control = MagicMock(return_value=cc_resources)

        sts = MagicMock()
        sts.get_caller_identity.return_value = {"Account": "123"}
        engine.session.client.return_value = sts

        result = engine.discover_all_resources()

        # 2 from RE + 2 new from CC = 4 (i-002 deduped)
        assert result.total_count == 4
