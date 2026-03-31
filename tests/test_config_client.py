"""
Unit tests for resource_discovery.config_client

Focuses on convert_to_resource logic and the common_resource_types list.
"""
import pytest
from unittest.mock import MagicMock
from botocore.exceptions import ClientError

from resource_discovery.config_client import ConfigClient
from resource_discovery.models import DiscoverySource


def _make_client(session=None, region="us-east-1"):
    if session is None:
        session = MagicMock()
        session.client.return_value = MagicMock()
    return ConfigClient(session, region=region)


# ===================================================================
# convert_to_resource
# ===================================================================

class TestConvertToResource:

    def test_basic_identifier_only(self, raw_config_identifier):
        """Conversion with only an identifier (no config_item)."""
        client = _make_client()
        resource = client.convert_to_resource(raw_config_identifier)

        assert resource.resource_type == "AWS::EC2::Instance"
        assert resource.name == "web-server"
        assert resource.source == DiscoverySource.CONFIG
        assert resource.region == "us-east-1"  # Uses client's region
        assert resource.account_id == "unknown"
        # ARN should be synthesized
        assert resource.arn.startswith("arn:aws:")

    def test_with_config_item(self, raw_config_identifier):
        """When config_item is provided, should extract ARN, tags, etc."""
        client = _make_client()
        config_item = {
            "arn": "arn:aws:ec2:us-east-1:123456789012:instance/i-0abcdef1234567890",
            "configuration": {"instanceType": "t3.micro"},
            "tags": {"Name": "web-server"},
            "relationships": [
                {"resourceId": "vpc-12345", "relationshipName": "Is contained in Vpc"}
            ],
            "resourceCreationTime": "2026-01-01T00:00:00Z",
            "configurationItemCaptureTime": "2026-03-30T12:00:00Z",
        }
        resource = client.convert_to_resource(raw_config_identifier, config_item)

        assert resource.arn == "arn:aws:ec2:us-east-1:123456789012:instance/i-0abcdef1234567890"
        assert resource.account_id == "123456789012"
        assert resource.region == "us-east-1"
        assert resource.tags == {"Name": "web-server"}
        assert resource.configuration == {"instanceType": "t3.micro"}
        assert "vpc-12345" in resource.relationships
        assert resource.created_at == "2026-01-01T00:00:00Z"

    def test_global_resource_from_arn(self, raw_config_identifier):
        """IAM ARN with empty region should produce region='global'."""
        client = _make_client()
        config_item = {
            "arn": "arn:aws:iam::123456789012:role/MyRole",
            "configuration": {},
            "tags": {},
            "relationships": [],
        }
        resource = client.convert_to_resource(raw_config_identifier, config_item)
        assert resource.region == "global"


# ===================================================================
# _get_common_resource_types
# ===================================================================

class TestCommonResourceTypes:

    def test_returns_list(self):
        client = _make_client()
        types = client._get_common_resource_types()
        assert isinstance(types, list)
        assert len(types) > 0

    def test_contains_core_services(self):
        client = _make_client()
        types = client._get_common_resource_types()
        assert "AWS::EC2::Instance" in types
        assert "AWS::S3::Bucket" in types
        assert "AWS::Lambda::Function" in types
        assert "AWS::IAM::Role" in types


# ===================================================================
# check_config_enabled
# ===================================================================

class TestCheckConfigEnabled:

    def test_enabled_and_recording(self):
        client = _make_client()
        client.client.describe_configuration_recorders.return_value = {
            "ConfigurationRecorders": [{"name": "default"}]
        }
        client.client.describe_configuration_recorder_status.return_value = {
            "ConfigurationRecordersStatus": [{"recording": True}]
        }
        assert client.check_config_enabled() is True

    def test_no_recorders(self):
        client = _make_client()
        client.client.describe_configuration_recorders.return_value = {
            "ConfigurationRecorders": []
        }
        assert client.check_config_enabled() is False

    def test_recorder_not_recording(self):
        client = _make_client()
        client.client.describe_configuration_recorders.return_value = {
            "ConfigurationRecorders": [{"name": "default"}]
        }
        client.client.describe_configuration_recorder_status.return_value = {
            "ConfigurationRecordersStatus": [{"recording": False}]
        }
        assert client.check_config_enabled() is False

    def test_client_error(self):
        client = _make_client()
        client.client.describe_configuration_recorders.side_effect = ClientError(
            {"Error": {"Code": "AccessDeniedException", "Message": "denied"}},
            "DescribeConfigurationRecorders",
        )
        assert client.check_config_enabled() is False
