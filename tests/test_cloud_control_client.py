"""
Unit tests for resource_discovery.cloud_control_client

Focuses on convert_to_resource and list_supported_resource_types.
"""
import json
import pytest
from unittest.mock import MagicMock

from resource_discovery.cloud_control_client import CloudControlClient
from resource_discovery.models import DiscoverySource


def _make_client(session=None, region="us-east-1"):
    if session is None:
        session = MagicMock()
        session.client.return_value = MagicMock()
    return CloudControlClient(session, region=region)


# ===================================================================
# convert_to_resource
# ===================================================================

class TestConvertToResource:

    def test_basic_conversion(self, raw_cloud_control_description):
        client = _make_client()
        resource = client.convert_to_resource(
            raw_cloud_control_description, "AWS::EC2::Instance"
        )

        assert resource.resource_type == "AWS::EC2::Instance"
        assert resource.source == DiscoverySource.CLOUD_CONTROL
        assert resource.arn == "arn:aws:ec2:us-east-1:123456789012:instance/i-0abcdef1234567890"
        assert resource.account_id == "123456789012"
        assert resource.region == "us-east-1"

    def test_tags_extracted(self, raw_cloud_control_description):
        client = _make_client()
        resource = client.convert_to_resource(
            raw_cloud_control_description, "AWS::EC2::Instance"
        )
        assert resource.tags == {"Name": "test-instance", "Environment": "dev"}

    def test_arn_synthesized_when_missing(self):
        """If Properties JSON has no Arn/ARN, ARN should be synthesized."""
        client = _make_client(region="eu-west-1")
        raw = {
            "Identifier": "my-topic",
            "Properties": json.dumps({"TopicName": "my-topic"}),
        }
        resource = client.convert_to_resource(raw, "AWS::SNS::Topic")
        assert "sns" in resource.arn
        assert "my-topic" in resource.arn

    def test_invalid_json_properties(self):
        """Malformed JSON in Properties should not crash."""
        client = _make_client()
        raw = {
            "Identifier": "bad-resource",
            "Properties": "NOT JSON {{{",
        }
        resource = client.convert_to_resource(raw, "AWS::EC2::Instance")
        assert resource.configuration == {}
        assert resource.tags == {}

    def test_tags_as_non_list(self):
        """Tags that aren't a list should be handled gracefully."""
        client = _make_client()
        raw = {
            "Identifier": "some-id",
            "Properties": json.dumps({"Tags": "not-a-list"}),
        }
        resource = client.convert_to_resource(raw, "AWS::EC2::Instance")
        assert resource.tags == {}

    def test_name_fallback_chain(self):
        """Name should be extracted from various property keys."""
        client = _make_client()

        # FunctionName
        raw = {
            "Identifier": "my-func",
            "Properties": json.dumps({"FunctionName": "my-lambda-func"}),
        }
        resource = client.convert_to_resource(raw, "AWS::Lambda::Function")
        assert resource.name == "my-lambda-func"

        # DBInstanceIdentifier
        raw = {
            "Identifier": "mydb",
            "Properties": json.dumps({"DBInstanceIdentifier": "prod-db-1"}),
        }
        resource = client.convert_to_resource(raw, "AWS::RDS::DBInstance")
        assert resource.name == "prod-db-1"

    def test_global_resource_region(self):
        """IAM ARN region should map to 'global'."""
        client = _make_client()
        raw = {
            "Identifier": "my-role",
            "Properties": json.dumps({
                "Arn": "arn:aws:iam::123456789012:role/my-role"
            }),
        }
        resource = client.convert_to_resource(raw, "AWS::IAM::Role")
        assert resource.region == "global"


# ===================================================================
# list_supported_resource_types
# ===================================================================

class TestListSupportedResourceTypes:

    def test_returns_curated_list(self):
        client = _make_client()
        types = client.list_supported_resource_types()
        assert isinstance(types, list)
        assert len(types) > 0
        assert "AWS::EC2::Instance" in types
        assert "AWS::S3::Bucket" in types
