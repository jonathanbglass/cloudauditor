"""
Unit tests for resource_discovery.resource_explorer_client

Focuses on pure-logic methods (ARN parsing, query building, response conversion).
AWS API calls are mocked at the boto3 client level.
"""
import pytest
from unittest.mock import MagicMock, patch
from botocore.exceptions import ClientError

from resource_discovery.resource_explorer_client import ResourceExplorerClient
from resource_discovery.models import DiscoverySource


# ===================================================================
# Helpers
# ===================================================================

def _make_client(session=None, region="us-east-1"):
    """Create a ResourceExplorerClient with a mocked session."""
    if session is None:
        session = MagicMock()
        session.client.return_value = MagicMock()
    return ResourceExplorerClient(session, region=region)


# ===================================================================
# convert_to_resource
# ===================================================================

class TestConvertToResource:
    """Tests for ResourceExplorerClient.convert_to_resource."""

    def test_basic_arn_parsing(self, raw_resource_explorer_response):
        client = _make_client()
        resource = client.convert_to_resource(raw_resource_explorer_response)

        assert resource.arn == "arn:aws:ec2:us-east-1:123456789012:instance/i-0abcdef1234567890"
        assert resource.region == "us-east-1"
        assert resource.account_id == "123456789012"
        assert resource.resource_type == "AWS::EC2::Instance"
        assert resource.source == DiscoverySource.RESOURCE_EXPLORER

    def test_global_resource_region(self):
        """IAM / S3 ARNs have empty region → should map to 'global'."""
        client = _make_client()
        raw = {
            "Arn": "arn:aws:iam::123456789012:user/admin",
            "ResourceType": "AWS::IAM::User",
            "Properties": [],
        }
        resource = client.convert_to_resource(raw)
        assert resource.region == "global"

    def test_tags_extracted(self, raw_resource_explorer_response):
        client = _make_client()
        resource = client.convert_to_resource(raw_resource_explorer_response)
        assert resource.tags == {"Environment": "production"}

    def test_configuration_extracted(self, raw_resource_explorer_response):
        client = _make_client()
        resource = client.convert_to_resource(raw_resource_explorer_response)
        assert resource.configuration["InstanceType"] == "t3.medium"

    def test_name_from_properties(self, raw_resource_explorer_response):
        client = _make_client()
        resource = client.convert_to_resource(raw_resource_explorer_response)
        assert resource.name == "web-server"

    def test_name_missing(self):
        """When no Name property exists, name should be None."""
        client = _make_client()
        raw = {
            "Arn": "arn:aws:ec2:us-east-1:123456789012:sg/sg-001",
            "ResourceType": "AWS::EC2::SecurityGroup",
            "Properties": [{"Name": "GroupId", "Data": "sg-001"}],
        }
        resource = client.convert_to_resource(raw)
        assert resource.name is None

    def test_last_modified_passthrough(self, raw_resource_explorer_response):
        client = _make_client()
        resource = client.convert_to_resource(raw_resource_explorer_response)
        assert resource.last_modified == "2026-03-30T12:00:00Z"

    def test_unknown_account_for_short_arn(self):
        """If ARN has fewer than 5 parts, account_id should be 'unknown'."""
        client = _make_client()
        raw = {
            "Arn": "arn:aws:s3",
            "ResourceType": "AWS::S3::Bucket",
            "Properties": [],
        }
        resource = client.convert_to_resource(raw)
        assert resource.account_id == "unknown"


# ===================================================================
# _build_query_string
# ===================================================================

class TestBuildQueryString:
    """Tests for ResourceExplorerClient._build_query_string."""

    def test_no_filters_returns_wildcard(self):
        client = _make_client()
        assert client._build_query_string(None) == "*"
        assert client._build_query_string({}) == "*"

    def test_single_resource_type(self):
        client = _make_client()
        q = client._build_query_string({"resource_types": "AWS::S3::Bucket"})
        assert q == "resourcetype:AWS::S3::Bucket"

    def test_multiple_resource_types(self):
        client = _make_client()
        q = client._build_query_string({
            "resource_types": ["AWS::EC2::Instance", "AWS::S3::Bucket"]
        })
        assert "resourcetype:AWS::EC2::Instance" in q
        assert "resourcetype:AWS::S3::Bucket" in q
        assert " OR " in q

    def test_tag_filter(self):
        client = _make_client()
        q = client._build_query_string({"tags": {"Environment": "prod"}})
        assert "tag:Environment=prod" in q

    def test_region_filter_single(self):
        client = _make_client()
        q = client._build_query_string({"regions": "us-east-1"})
        assert q == "region:us-east-1"

    def test_region_filter_multiple(self):
        client = _make_client()
        q = client._build_query_string({"regions": ["us-east-1", "eu-west-1"]})
        assert "region:us-east-1" in q
        assert "region:eu-west-1" in q
        assert " OR " in q

    def test_combined_filters(self):
        client = _make_client()
        q = client._build_query_string({
            "resource_types": ["AWS::EC2::Instance"],
            "tags": {"Team": "platform"},
            "regions": "us-east-1",
        })
        assert " AND " in q
        assert "resourcetype:AWS::EC2::Instance" in q
        assert "tag:Team=platform" in q
        assert "region:us-east-1" in q


# ===================================================================
# check_index_exists
# ===================================================================

class TestCheckIndexExists:

    def test_returns_true_when_indexes_present(self):
        client = _make_client()
        client.client.list_indexes.return_value = {
            "Indexes": [{"Type": "LOCAL", "Region": "us-east-1"}]
        }
        assert client.check_index_exists() is True

    def test_returns_false_when_no_indexes(self):
        client = _make_client()
        client.client.list_indexes.return_value = {"Indexes": []}
        assert client.check_index_exists() is False

    def test_returns_false_on_client_error(self):
        client = _make_client()
        client.client.list_indexes.side_effect = ClientError(
            {"Error": {"Code": "AccessDeniedException", "Message": "denied"}},
            "ListIndexes",
        )
        assert client.check_index_exists() is False


# ===================================================================
# is_aggregator_index
# ===================================================================

class TestIsAggregatorIndex:

    def test_aggregator_returns_true(self):
        client = _make_client()
        client.client.get_index.return_value = {"Type": "AGGREGATOR"}
        assert client.is_aggregator_index() is True

    def test_local_returns_false(self):
        client = _make_client()
        client.client.get_index.return_value = {"Type": "LOCAL"}
        assert client.is_aggregator_index() is False

    def test_not_found_returns_false(self):
        client = _make_client()
        client.client.get_index.side_effect = ClientError(
            {"Error": {"Code": "ResourceNotFoundException", "Message": "nope"}},
            "GetIndex",
        )
        assert client.is_aggregator_index() is False
