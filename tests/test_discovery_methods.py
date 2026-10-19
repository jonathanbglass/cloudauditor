"""
Method-level tests for discovery orchestration that the higher-level
suite stubs out: engine startup, Config, Cloud Control, and Resource
Explorer aggregation.

AWS clients here are MagicMocks. Live boto3 calls are covered in
test_moto_aws.py.
"""
from unittest.mock import MagicMock

from resource_discovery.discovery_engine import ResourceDiscoveryEngine
from resource_discovery.models import DiscoveryConfig
from tests.conftest import make_resource


def _make_engine(config=None, **kwargs):
    """Build an engine without running __init__ (which talks to AWS)."""
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


def _stub_account(engine, account_id="123456789012"):
    sts = MagicMock()
    sts.get_caller_identity.return_value = {"Account": account_id}
    engine.session.client.return_value = sts
    return sts


class TestEngineInitialization:
    """ResourceDiscoveryEngine.__init__ decides which clients stay enabled."""

    def _session(self):
        session = MagicMock()
        session.region_name = "us-east-1"
        session.client.return_value.describe_regions.return_value = {
            "Regions": [{"RegionName": "us-east-1"}, {"RegionName": "eu-west-1"}]
        }
        return session

    def test_disables_resource_explorer_when_index_missing(self, mocker):
        re_client = MagicMock()
        re_client.check_index_exists.return_value = False
        mocker.patch(
            "resource_discovery.discovery_engine.ResourceExplorerClient",
            return_value=re_client,
        )
        config_client = MagicMock()
        config_client.check_config_enabled.return_value = True
        mocker.patch(
            "resource_discovery.discovery_engine.ConfigClient",
            return_value=config_client,
        )

        engine = ResourceDiscoveryEngine(
            session=self._session(),
            config=DiscoveryConfig(use_cloud_control=False),
        )

        assert engine.resource_explorer is None
        assert engine.config_client is config_client
        assert engine.enabled_regions == ["us-east-1", "eu-west-1"]

    def test_aggregator_index_is_recorded(self, mocker):
        re_client = MagicMock()
        re_client.check_index_exists.return_value = True
        re_client.is_aggregator_index.return_value = True
        mocker.patch(
            "resource_discovery.discovery_engine.ResourceExplorerClient",
            return_value=re_client,
        )
        mocker.patch(
            "resource_discovery.discovery_engine.ConfigClient",
            side_effect=RuntimeError("config unavailable"),
        )
        cc_client = MagicMock()
        mocker.patch(
            "resource_discovery.discovery_engine.CloudControlClient",
            return_value=cc_client,
        )

        engine = ResourceDiscoveryEngine(
            session=self._session(),
            config=DiscoveryConfig(use_cloud_control=True),
        )

        assert engine.resource_explorer is re_client
        assert engine.is_aggregator is True
        assert engine.config_client is None
        assert engine.cloud_control is cc_client

    def test_local_index_and_disabled_config(self, mocker):
        re_client = MagicMock()
        re_client.check_index_exists.return_value = True
        re_client.is_aggregator_index.return_value = False
        mocker.patch(
            "resource_discovery.discovery_engine.ResourceExplorerClient",
            return_value=re_client,
        )
        config_client = MagicMock()
        config_client.check_config_enabled.return_value = False
        mocker.patch(
            "resource_discovery.discovery_engine.ConfigClient",
            return_value=config_client,
        )
        mocker.patch(
            "resource_discovery.discovery_engine.CloudControlClient",
            side_effect=RuntimeError("cc unavailable"),
        )

        engine = ResourceDiscoveryEngine(
            session=self._session(),
            config=DiscoveryConfig(use_cloud_control=True),
        )

        assert engine.is_aggregator is False
        assert engine.resource_explorer is re_client
        assert engine.config_client is None
        assert engine.cloud_control is None

    def test_client_constructor_failures_are_disabled(self, mocker):
        mocker.patch(
            "resource_discovery.discovery_engine.ResourceExplorerClient",
            side_effect=RuntimeError("no explorer"),
        )
        engine = ResourceDiscoveryEngine(
            session=self._session(),
            config=DiscoveryConfig(use_config=False, use_cloud_control=False),
        )
        assert engine.resource_explorer is None


class TestResourceExplorerDiscovery:

    def test_missing_client_returns_empty(self):
        engine = _make_engine(re_client=None)
        assert engine._discover_via_resource_explorer("123") == []

    def test_aggregator_keeps_matching_accounts_and_skips_bad_rows(self):
        re_client = MagicMock()
        kept = make_resource(account_id="123", arn="arn:keep")
        unknown = make_resource(account_id="unknown", arn="arn:unknown")
        other = make_resource(account_id="999", arn="arn:other")
        re_client.list_all_resources.return_value = iter(
            [{"Arn": "1"}, {"Arn": "2"}, {"Arn": "3"}, {"Arn": "4"}]
        )
        re_client.convert_to_resource.side_effect = [
            kept,
            RuntimeError("bad row"),
            other,
            unknown,
        ]
        config = DiscoveryConfig(include_types=["AWS::EC2::Instance"])
        engine = _make_engine(
            config=config, re_client=re_client, is_aggregator=True
        )

        resources = engine._discover_via_resource_explorer("123")

        assert resources == [kept, unknown]
        filters = re_client.list_all_resources.call_args.kwargs["filters"]
        assert filters["resource_types"] == ["AWS::EC2::Instance"]

    def test_local_index_filters_types_and_survives_region_errors(self, mocker):
        config = DiscoveryConfig(include_types=["AWS::S3::Bucket"])
        engine = _make_engine(
            config=config,
            re_client=MagicMock(),
            is_aggregator=False,
            regions=["us-east-1", "us-west-2"],
        )
        kept = make_resource(account_id="123", arn="arn:keep")
        good_region = MagicMock()
        good_region.check_index_exists.return_value = True
        good_region.list_all_resources.return_value = iter([{"Arn": "1"}, {"Arn": "2"}])
        good_region.convert_to_resource.side_effect = [kept, RuntimeError("bad item")]

        bad_region = MagicMock()
        bad_region.check_index_exists.side_effect = RuntimeError("region down")

        mocker.patch(
            "resource_discovery.discovery_engine.ResourceExplorerClient",
            side_effect=[good_region, bad_region],
        )

        resources = engine._discover_via_resource_explorer("123")

        assert resources == [kept]
        filters = good_region.list_all_resources.call_args.kwargs["filters"]
        assert filters["resource_types"] == ["AWS::S3::Bucket"]


class TestConfigDiscovery:

    def test_queries_only_included_types(self):
        cfg = MagicMock()
        cfg.list_supported_resource_types.return_value = [
            "AWS::EC2::Instance",
            "AWS::S3::Bucket",
        ]
        instance = make_resource(resource_type="AWS::EC2::Instance", arn="arn:i")
        cfg.list_discovered_resources.return_value = [{"resourceId": "i-1"}]
        cfg.convert_to_resource.return_value = instance
        config = DiscoveryConfig(include_types=["AWS::EC2::Instance"], max_workers=2)
        engine = _make_engine(config=config, cfg_client=cfg)

        resources = engine._discover_via_config("123")

        assert resources == [instance]
        cfg.list_discovered_resources.assert_called_once_with("AWS::EC2::Instance")

    def test_skips_identifiers_that_fail_conversion(self):
        cfg = MagicMock()
        good = make_resource(arn="arn:good")
        cfg.convert_to_resource.side_effect = [RuntimeError("bad"), good]
        cfg.list_discovered_resources.return_value = [
            {"resourceId": "i-bad"},
            {"resourceId": "i-good"},
        ]
        engine = _make_engine(cfg_client=cfg)

        resources = engine._discover_config_resource_type("AWS::EC2::Instance", "123")

        assert resources == [good]

    def test_samples_at_most_100_identifiers_per_type(self):
        cfg = MagicMock()
        cfg.list_discovered_resources.return_value = [
            {"resourceId": f"i-{i}"} for i in range(150)
        ]
        cfg.convert_to_resource.side_effect = lambda ident: make_resource(
            arn=f"arn:{ident['resourceId']}"
        )
        engine = _make_engine(cfg_client=cfg)

        resources = engine._discover_config_resource_type("AWS::EC2::Instance", "123")

        assert len(resources) == 100
        assert cfg.convert_to_resource.call_count == 100

    def test_type_failure_does_not_abort_other_types(self):
        cfg = MagicMock()
        cfg.list_supported_resource_types.return_value = [
            "AWS::EC2::Instance",
            "AWS::S3::Bucket",
        ]

        def list_discovered(resource_type):
            if resource_type == "AWS::EC2::Instance":
                raise RuntimeError("config throttled")
            return [{"resourceId": "bucket"}]

        cfg.list_discovered_resources.side_effect = list_discovered
        bucket = make_resource(arn="arn:bucket", resource_type="AWS::S3::Bucket")
        cfg.convert_to_resource.return_value = bucket
        engine = _make_engine(
            config=DiscoveryConfig(max_workers=2),
            cfg_client=cfg,
        )

        resources = engine._discover_via_config("123")

        assert resources == [bucket]


class TestCloudControlDiscovery:

    def test_merges_listed_resources_and_skips_failures(self):
        cc = MagicMock()
        cc.list_supported_resource_types.return_value = [
            "AWS::EC2::Instance",
            "AWS::S3::Bucket",
            "AWS::Lambda::Function",
        ]
        good = make_resource(arn="arn:bucket", resource_type="AWS::S3::Bucket")

        def list_resources(resource_type):
            if resource_type == "AWS::EC2::Instance":
                raise RuntimeError("unsupported")
            if resource_type == "AWS::S3::Bucket":
                return [{"Identifier": "1"}, {"Identifier": "2"}]
            return []

        cc.list_resources.side_effect = list_resources
        cc.convert_to_resource.side_effect = [good, RuntimeError("bad payload")]
        config = DiscoveryConfig(
            include_types=["AWS::EC2::Instance", "AWS::S3::Bucket"],
            use_cloud_control=True,
        )
        engine = _make_engine(config=config, cc_client=cc)

        resources = engine._discover_via_cloud_control("123")

        assert resources == [good]
        listed = [call.args[0] for call in cc.list_resources.call_args_list]
        assert listed == ["AWS::EC2::Instance", "AWS::S3::Bucket"]


class TestDiscoveryErrorCapture:

    def test_config_exception_is_recorded(self):
        engine = _make_engine(cfg_client=MagicMock())
        engine._discover_via_config = MagicMock(side_effect=RuntimeError("config down"))
        _stub_account(engine)

        result = engine.discover_all_resources()

        assert result.success is False
        assert any("Config discovery failed" in err for err in result.errors)

    def test_cloud_control_exception_is_recorded(self):
        config = DiscoveryConfig(
            use_resource_explorer=False,
            use_config=False,
            use_cloud_control=True,
        )
        engine = _make_engine(config=config, cc_client=MagicMock())
        engine._discover_via_cloud_control = MagicMock(side_effect=RuntimeError("cc down"))
        _stub_account(engine)

        result = engine.discover_all_resources()

        assert result.success is False
        assert any("Cloud Control discovery failed" in err for err in result.errors)

    def test_bedrock_exception_is_recorded(self):
        engine = _make_engine()
        engine._discover_bedrock_resources.side_effect = RuntimeError("bedrock down")
        _stub_account(engine)

        result = engine.discover_all_resources()

        assert result.success is False
        assert any("Custom Bedrock discovery failed" in err for err in result.errors)
