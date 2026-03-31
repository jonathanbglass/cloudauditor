"""
Shared test fixtures and configuration for CloudAuditor tests.
"""
import pytest
from datetime import datetime
from unittest.mock import MagicMock

from resource_discovery.models import (
    Resource,
    DiscoveryConfig,
    DiscoveryResult,
    DiscoverySource,
)


# ---------------------------------------------------------------------------
# Factory helpers – call these to create test data with sensible defaults
# ---------------------------------------------------------------------------

def make_resource(**overrides) -> Resource:
    """Create a Resource with sensible defaults. Override any field via kwargs."""
    defaults = dict(
        arn="arn:aws:ec2:us-east-1:123456789012:instance/i-0abcdef1234567890",
        resource_type="AWS::EC2::Instance",
        region="us-east-1",
        account_id="123456789012",
        name="test-instance",
        tags={"Environment": "test"},
        configuration={"InstanceType": "t3.micro"},
        relationships=[],
        created_at=None,
        last_modified=None,
        source=DiscoverySource.RESOURCE_EXPLORER,
    )
    defaults.update(overrides)
    return Resource(**defaults)


def make_discovery_result(**overrides) -> DiscoveryResult:
    """Create a DiscoveryResult with sensible defaults."""
    defaults = dict(
        resources=[],
        total_count=0,
        success=True,
        errors=[],
        duration_seconds=1.5,
    )
    defaults.update(overrides)
    return DiscoveryResult(**defaults)


# ---------------------------------------------------------------------------
# Pytest fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_resource():
    """Single Resource fixture."""
    return make_resource()


@pytest.fixture
def sample_resources():
    """List of diverse Resource fixtures covering multiple types/regions."""
    return [
        make_resource(
            arn="arn:aws:ec2:us-east-1:123456789012:instance/i-001",
            resource_type="AWS::EC2::Instance",
            region="us-east-1",
            name="web-server-1",
        ),
        make_resource(
            arn="arn:aws:s3:::my-bucket",
            resource_type="AWS::S3::Bucket",
            region="global",
            name="my-bucket",
            source=DiscoverySource.CONFIG,
        ),
        make_resource(
            arn="arn:aws:ec2:us-west-2:123456789012:volume/vol-001",
            resource_type="AWS::EC2::Volume",
            region="us-west-2",
            name="data-volume",
        ),
        make_resource(
            arn="arn:aws:lambda:us-east-1:123456789012:function:my-func",
            resource_type="AWS::Lambda::Function",
            region="us-east-1",
            name="my-func",
            source=DiscoverySource.CONFIG,
        ),
        make_resource(
            arn="arn:aws:ec2:eu-west-1:987654321098:instance/i-002",
            resource_type="AWS::EC2::Instance",
            region="eu-west-1",
            account_id="987654321098",
            name="eu-server",
        ),
    ]


@pytest.fixture
def sample_discovery_result(sample_resources):
    """DiscoveryResult populated with sample_resources."""
    return make_discovery_result(
        resources=sample_resources,
        total_count=len(sample_resources),
    )


@pytest.fixture
def default_config():
    """Default DiscoveryConfig fixture."""
    return DiscoveryConfig()


@pytest.fixture
def mock_boto3_session():
    """A MagicMock standing in for a boto3.Session."""
    session = MagicMock()
    # Pre-wire common client factory
    session.client.return_value = MagicMock()
    session.region_name = "us-east-1"
    return session


# ---------------------------------------------------------------------------
# Raw API response fixtures (used by client unit tests)
# ---------------------------------------------------------------------------

@pytest.fixture
def raw_resource_explorer_response():
    """Mimics a single item from Resource Explorer search API."""
    return {
        "Arn": "arn:aws:ec2:us-east-1:123456789012:instance/i-0abcdef1234567890",
        "ResourceType": "AWS::EC2::Instance",
        "LastReportedAt": "2026-03-30T12:00:00Z",
        "Properties": [
            {"Name": "tag:Environment", "Data": "production"},
            {"Name": "Name", "Data": "web-server"},
            {"Name": "InstanceType", "Data": "t3.medium"},
        ],
    }


@pytest.fixture
def raw_config_identifier():
    """Mimics a resource identifier from AWS Config list_discovered_resources."""
    return {
        "resourceType": "AWS::EC2::Instance",
        "resourceId": "i-0abcdef1234567890",
        "resourceName": "web-server",
    }


@pytest.fixture
def raw_cloud_control_description():
    """Mimics a resource description from Cloud Control API."""
    import json
    return {
        "Identifier": "i-0abcdef1234567890",
        "Properties": json.dumps({
            "Arn": "arn:aws:ec2:us-east-1:123456789012:instance/i-0abcdef1234567890",
            "InstanceType": "t3.micro",
            "Tags": [
                {"Key": "Name", "Value": "test-instance"},
                {"Key": "Environment", "Value": "dev"},
            ],
        }),
    }
