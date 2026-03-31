"""
Unit tests for resource_discovery_lambda.lambda_handler

Tests the Lambda handler orchestration with all collaborators mocked.
"""
import json
import pytest
from unittest.mock import MagicMock, patch, PropertyMock

from resource_discovery.models import DiscoveryResult, DiscoverySource
from tests.conftest import make_resource, make_discovery_result


# ===================================================================
# Helpers
# ===================================================================

def _import_handler():
    """Import the handler deferred so patches can take effect."""
    from resource_discovery_lambda import lambda_handler
    return lambda_handler


@pytest.fixture
def mock_context():
    ctx = MagicMock()
    ctx.log_stream_name = "test-log-stream"
    return ctx


@pytest.fixture
def scheduled_event():
    return {"source": "aws.events", "detail-type": "Scheduled Event"}


# ===================================================================
# Tests
# ===================================================================

class TestResourceDiscoveryLambda:

    @patch("resource_discovery_lambda.OrganizationsClient")
    @patch("resource_discovery_lambda.DatabaseClient")
    @patch("resource_discovery_lambda.ResourceDiscoveryEngine")
    @patch("resource_discovery_lambda.boto3")
    def test_basic_discovery(self, mock_boto3, mock_engine_cls, mock_db_cls, mock_org_cls,
                             scheduled_event, mock_context):
        # Setup mocks
        mock_db = MagicMock()
        mock_db.get_monitored_accounts.return_value = [
            {"account_id": "123", "role_arn": "arn:aws:iam::123:role/Audit", "status": "active"}
        ]
        mock_db_cls.return_value = mock_db

        mock_org = MagicMock()
        mock_org.is_organization_management_account.return_value = False
        mock_org_cls.return_value = mock_org

        resources = [make_resource(arn=f"arn:aws:ec2:us-east-1:123:i/i-{i}") for i in range(5)]
        mock_result = make_discovery_result(resources=resources, total_count=5)
        mock_engine = MagicMock()
        mock_engine.discover_all_resources.return_value = mock_result
        mock_engine.get_resource_summary.return_value = {"AWS::EC2::Instance": 5}
        mock_engine_cls.return_value = mock_engine

        handler = _import_handler()
        response = handler(scheduled_event, mock_context)

        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["success"] is True
        assert body["total_resources"] == 5

    @patch("resource_discovery_lambda.OrganizationsClient")
    @patch("resource_discovery_lambda.DatabaseClient")
    @patch("resource_discovery_lambda.ResourceDiscoveryEngine")
    @patch("resource_discovery_lambda.boto3")
    def test_org_auto_discovery(self, mock_boto3, mock_engine_cls, mock_db_cls, mock_org_cls,
                                scheduled_event, mock_context):
        mock_db = MagicMock()
        mock_db.get_monitored_accounts.return_value = [
            {"account_id": "111", "role_arn": "arn", "status": "active"}
        ]
        mock_db_cls.return_value = mock_db

        mock_org = MagicMock()
        mock_org.is_organization_management_account.return_value = True
        mock_org.list_organization_accounts.return_value = [
            {"account_id": "111", "account_name": "Existing"},
            {"account_id": "222", "account_name": "NewAccount"},
        ]
        mock_org_cls.return_value = mock_org

        mock_engine = MagicMock()
        mock_engine.discover_all_resources.return_value = make_discovery_result()
        mock_engine.get_resource_summary.return_value = {}
        mock_engine_cls.return_value = mock_engine

        handler = _import_handler()
        response = handler(scheduled_event, mock_context)

        # Should have attempted to register the new account
        assert mock_db.register_account.called
        # Verify it registered account 222 (the new one)
        register_calls = mock_db.register_account.call_args_list
        registered_ids = [call[0][0] for call in register_calls]
        assert "222" in registered_ids

    @patch("resource_discovery_lambda.OrganizationsClient")
    @patch("resource_discovery_lambda.DatabaseClient")
    @patch("resource_discovery_lambda.ResourceDiscoveryEngine")
    @patch("resource_discovery_lambda.boto3")
    def test_no_monitored_accounts_fallback(self, mock_boto3, mock_engine_cls, mock_db_cls,
                                            mock_org_cls, scheduled_event, mock_context):
        mock_db = MagicMock()
        mock_db.get_monitored_accounts.return_value = []  # No accounts
        mock_db_cls.return_value = mock_db

        mock_org = MagicMock()
        mock_org.is_organization_management_account.return_value = False
        mock_org_cls.return_value = mock_org

        # Mock STS for local account fallback
        mock_sts = MagicMock()
        mock_sts.get_caller_identity.return_value = {"Account": "999"}
        mock_boto3.client.return_value = mock_sts

        mock_engine = MagicMock()
        mock_engine.discover_all_resources.return_value = make_discovery_result()
        mock_engine.get_resource_summary.return_value = {}
        mock_engine_cls.return_value = mock_engine

        handler = _import_handler()
        response = handler(scheduled_event, mock_context)

        assert response["statusCode"] == 200

    @patch("resource_discovery_lambda.OrganizationsClient")
    @patch("resource_discovery_lambda.DatabaseClient")
    @patch("resource_discovery_lambda.ResourceDiscoveryEngine")
    @patch("resource_discovery_lambda.boto3")
    def test_error_tracking(self, mock_boto3, mock_engine_cls, mock_db_cls, mock_org_cls,
                            scheduled_event, mock_context):
        mock_db = MagicMock()
        mock_db.get_monitored_accounts.return_value = [
            {"account_id": "123", "role_arn": "arn", "status": "active"}
        ]
        mock_db_cls.return_value = mock_db

        mock_org = MagicMock()
        mock_org.is_organization_management_account.return_value = False
        mock_org_cls.return_value = mock_org

        # Discovery returns with errors containing account ID
        result = make_discovery_result(
            success=False,
            errors=["Failed to discover account 123: timeout"],
        )
        mock_engine = MagicMock()
        mock_engine.discover_all_resources.return_value = result
        mock_engine.get_resource_summary.return_value = {}
        mock_engine_cls.return_value = mock_engine

        handler = _import_handler()
        response = handler(scheduled_event, mock_context)

        # Should have called update_account_status with 'error'
        update_calls = mock_db.update_account_status.call_args_list
        error_calls = [c for c in update_calls if c[0][1] == "error"]
        assert len(error_calls) > 0

    @patch("resource_discovery_lambda.OrganizationsClient")
    @patch("resource_discovery_lambda.DatabaseClient")
    @patch("resource_discovery_lambda.ResourceDiscoveryEngine")
    @patch("resource_discovery_lambda.boto3")
    def test_run_recording(self, mock_boto3, mock_engine_cls, mock_db_cls, mock_org_cls,
                           scheduled_event, mock_context):
        mock_db = MagicMock()
        mock_db.get_monitored_accounts.return_value = [
            {"account_id": "123", "role_arn": "arn", "status": "active"}
        ]
        mock_db_cls.return_value = mock_db

        mock_org = MagicMock()
        mock_org.is_organization_management_account.return_value = False
        mock_org_cls.return_value = mock_org

        mock_engine = MagicMock()
        mock_engine.discover_all_resources.return_value = make_discovery_result()
        mock_engine.get_resource_summary.return_value = {}
        mock_engine_cls.return_value = mock_engine

        handler = _import_handler()
        handler(scheduled_event, mock_context)

        mock_db.start_discovery_run.assert_called_once()
        mock_db.complete_discovery_run.assert_called_once()

    @patch("resource_discovery_lambda.OrganizationsClient")
    @patch("resource_discovery_lambda.DatabaseClient")
    @patch("resource_discovery_lambda.boto3")
    def test_handler_exception_returns_500(self, mock_boto3, mock_db_cls, mock_org_cls,
                                          scheduled_event, mock_context):
        mock_db = MagicMock()
        mock_db_cls.return_value = mock_db
        mock_db.start_discovery_run.side_effect = Exception("DB connection failed")
        # OrganizationsClient init also needs to work
        mock_org_cls.return_value = MagicMock()

        handler = _import_handler()
        response = handler(scheduled_event, mock_context)

        assert response["statusCode"] == 500
        body = json.loads(response["body"])
        assert body["success"] is False
