"""
P4 — Coverage expansion tests for resource_discovery clients.

Covers pagination, error paths, and API-level methods that were
not exercised in the initial test suite.
"""
import json
import pytest
from unittest.mock import MagicMock, patch, call
from botocore.exceptions import ClientError

from resource_discovery.resource_explorer_client import ResourceExplorerClient
from resource_discovery.config_client import ConfigClient
from resource_discovery.cloud_control_client import CloudControlClient


def _mock_session():
    s = MagicMock()
    s.client.return_value = MagicMock()
    return s


# ===================================================================
# ResourceExplorerClient — Pagination & API paths
# ===================================================================

class TestResourceExplorerPagination:

    def test_list_all_resources_multi_page(self):
        client = ResourceExplorerClient(_mock_session())
        paginator = MagicMock()
        page1 = {"Resources": [
            {"Arn": f"arn:aws:ec2:us-east-1:123:i/i-{i}", "ResourceType": "AWS::EC2::Instance", "Properties": []}
            for i in range(3)
        ]}
        page2 = {"Resources": [
            {"Arn": f"arn:aws:ec2:us-east-1:123:i/i-{i}", "ResourceType": "AWS::EC2::Instance", "Properties": []}
            for i in range(3, 5)
        ]}
        paginator.paginate.return_value = [page1, page2]
        client.client.get_paginator.return_value = paginator

        results = list(client.list_all_resources())
        assert len(results) == 5

    def test_list_all_resources_empty(self):
        client = ResourceExplorerClient(_mock_session())
        paginator = MagicMock()
        paginator.paginate.return_value = [{"Resources": []}]
        client.client.get_paginator.return_value = paginator

        results = list(client.list_all_resources())
        assert results == []

    def test_list_all_resources_unauthorized(self):
        client = ResourceExplorerClient(_mock_session())
        paginator = MagicMock()
        paginator.paginate.side_effect = ClientError(
            {"Error": {"Code": "UnauthorizedException", "Message": "not enabled"}},
            "Search",
        )
        client.client.get_paginator.return_value = paginator

        with pytest.raises(ClientError):
            list(client.list_all_resources())

    def test_list_all_resources_with_filters(self):
        client = ResourceExplorerClient(_mock_session())
        paginator = MagicMock()
        paginator.paginate.return_value = [{"Resources": []}]
        client.client.get_paginator.return_value = paginator

        list(client.list_all_resources(filters={"resource_types": ["AWS::S3::Bucket"]}))

        call_kwargs = paginator.paginate.call_args[1]
        assert "S3" in call_kwargs["QueryString"]


class TestResourceExplorerGetResource:

    def test_get_resource_details_success(self):
        client = ResourceExplorerClient(_mock_session())
        client.client.get_resource.return_value = {
            "Resource": {"Arn": "arn:aws:ec2:us-east-1:123:i/i-001", "Properties": []}
        }

        result = client.get_resource_details("arn:aws:ec2:us-east-1:123:i/i-001")
        assert result is not None
        assert result["Arn"] == "arn:aws:ec2:us-east-1:123:i/i-001"

    def test_get_resource_details_not_found(self):
        client = ResourceExplorerClient(_mock_session())
        client.client.get_resource.side_effect = ClientError(
            {"Error": {"Code": "ResourceNotFoundException", "Message": "not found"}},
            "GetResource",
        )

        result = client.get_resource_details("arn:aws:ec2:us-east-1:123:i/bad")
        assert result is None


class TestResourceExplorerSupportedTypes:

    def test_list_supported_resource_types(self):
        client = ResourceExplorerClient(_mock_session())
        paginator = MagicMock()
        paginator.paginate.return_value = [{
            "Resources": [
                {"Arn": "arn:aws:ec2:us-east-1:123:i/i-1", "ResourceType": "AWS::EC2::Instance", "Properties": []},
                {"Arn": "arn:aws:s3:::b-1", "ResourceType": "AWS::S3::Bucket", "Properties": []},
                {"Arn": "arn:aws:ec2:us-east-1:123:i/i-2", "ResourceType": "AWS::EC2::Instance", "Properties": []},
            ]
        }]
        client.client.get_paginator.return_value = paginator

        types = client.list_supported_resource_types()
        assert "AWS::EC2::Instance" in types
        assert "AWS::S3::Bucket" in types
        # Should be deduplicated
        assert len(types) == 2

    def test_list_supported_types_error(self):
        client = ResourceExplorerClient(_mock_session())
        paginator = MagicMock()
        paginator.paginate.side_effect = Exception("API error")
        client.client.get_paginator.return_value = paginator

        types = client.list_supported_resource_types()
        assert types == []


# ===================================================================
# ConfigClient — API call paths
# ===================================================================

class TestConfigListDiscoveredResources:

    def test_pagination(self):
        client = ConfigClient(_mock_session())
        paginator = MagicMock()
        paginator.paginate.return_value = [
            {"resourceIdentifiers": [
                {"resourceType": "AWS::EC2::Instance", "resourceId": "i-001"},
            ]},
            {"resourceIdentifiers": [
                {"resourceType": "AWS::EC2::Instance", "resourceId": "i-002"},
            ]},
        ]
        client.client.get_paginator.return_value = paginator

        results = client.list_discovered_resources("AWS::EC2::Instance")
        assert len(results) == 2

    def test_not_enabled_error(self):
        client = ConfigClient(_mock_session())
        paginator = MagicMock()
        paginator.paginate.side_effect = ClientError(
            {"Error": {"Code": "NoSuchConfigurationRecorderException", "Message": "no recorder"}},
            "ListDiscoveredResources",
        )
        client.client.get_paginator.return_value = paginator

        results = client.list_discovered_resources("AWS::EC2::Instance")
        assert results == []


class TestConfigGetResourceConfig:

    def test_success(self):
        client = ConfigClient(_mock_session())
        client.client.get_resource_config_history.return_value = {
            "configurationItems": [
                {"arn": "arn:aws:ec2:us-east-1:123:i/i-001", "configuration": {"type": "t3.micro"}}
            ]
        }

        result = client.get_resource_config("AWS::EC2::Instance", "i-001")
        assert result is not None
        assert result["arn"] == "arn:aws:ec2:us-east-1:123:i/i-001"

    def test_not_found(self):
        client = ConfigClient(_mock_session())
        client.client.get_resource_config_history.return_value = {
            "configurationItems": []
        }

        result = client.get_resource_config("AWS::EC2::Instance", "i-bad")
        assert result is None

    def test_client_error(self):
        client = ConfigClient(_mock_session())
        client.client.get_resource_config_history.side_effect = ClientError(
            {"Error": {"Code": "ResourceNotDiscoveredException", "Message": "not found"}},
            "GetResourceConfigHistory",
        )

        result = client.get_resource_config("AWS::EC2::Instance", "i-bad")
        assert result is None


class TestConfigSupportedTypes:

    def test_all_supported_returns_common(self):
        client = ConfigClient(_mock_session())
        client.client.describe_configuration_recorders.return_value = {
            "ConfigurationRecorders": [{
                "name": "default",
                "recordingGroup": {"allSupported": True}
            }]
        }

        types = client.list_supported_resource_types()
        assert "AWS::EC2::Instance" in types
        assert len(types) > 10

    def test_specific_types(self):
        client = ConfigClient(_mock_session())
        client.client.describe_configuration_recorders.return_value = {
            "ConfigurationRecorders": [{
                "name": "default",
                "recordingGroup": {
                    "allSupported": False,
                    "resourceTypes": ["AWS::S3::Bucket", "AWS::EC2::VPC"]
                }
            }]
        }

        types = client.list_supported_resource_types()
        assert types == ["AWS::S3::Bucket", "AWS::EC2::VPC"]


# ===================================================================
# CloudControlClient — API call paths
# ===================================================================

class TestCloudControlListResources:

    def test_pagination(self):
        client = CloudControlClient(_mock_session())
        paginator = MagicMock()
        paginator.paginate.return_value = [
            {"ResourceDescriptions": [
                {"Identifier": "i-001", "Properties": "{}"},
            ]},
            {"ResourceDescriptions": [
                {"Identifier": "i-002", "Properties": "{}"},
            ]},
        ]
        client.client.get_paginator.return_value = paginator

        results = list(client.list_resources("AWS::EC2::Instance"))
        assert len(results) == 2

    def test_unsupported_action(self):
        client = CloudControlClient(_mock_session())
        paginator = MagicMock()
        paginator.paginate.side_effect = ClientError(
            {"Error": {"Code": "UnsupportedActionException", "Message": "not supported"}},
            "ListResources",
        )
        client.client.get_paginator.return_value = paginator

        results = list(client.list_resources("AWS::Unsupported::Type"))
        assert results == []

    def test_type_not_found(self):
        client = CloudControlClient(_mock_session())
        paginator = MagicMock()
        paginator.paginate.side_effect = ClientError(
            {"Error": {"Code": "TypeNotFoundException", "Message": "type not found"}},
            "ListResources",
        )
        client.client.get_paginator.return_value = paginator

        results = list(client.list_resources("AWS::Nonexistent::Type"))
        assert results == []


class TestCloudControlGetResource:

    def test_success(self):
        client = CloudControlClient(_mock_session())
        client.client.get_resource.return_value = {
            "ResourceDescription": {"Identifier": "i-001", "Properties": "{}"}
        }

        result = client.get_resource("AWS::EC2::Instance", "i-001")
        assert result is not None
        assert result["Identifier"] == "i-001"

    def test_error_returns_none(self):
        client = CloudControlClient(_mock_session())
        client.client.get_resource.side_effect = ClientError(
            {"Error": {"Code": "ResourceNotFoundException", "Message": "not found"}},
            "GetResource",
        )

        result = client.get_resource("AWS::EC2::Instance", "i-bad")
        assert result is None
