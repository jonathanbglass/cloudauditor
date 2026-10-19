"""
AWS-boundary tests backed by moto.

These exercise the real boto3 client code paths (Organizations, CloudFormation
StackSets, Secrets Manager, STS, EC2) against moto's in-process backends.
Nothing in this module is allowed to use live credentials or the network.
"""
import json

import boto3
import pytest
from moto import mock_aws
from unittest.mock import MagicMock

from lib.database import DatabaseClient
from lib.organizations import OrganizationsClient
from resource_discovery.discovery_engine import ResourceDiscoveryEngine
from resource_discovery.models import DiscoveryConfig
from resource_discovery.verification import IAMVerifier


pytestmark = pytest.mark.integration


def _session():
    return boto3.Session(region_name="us-east-1")


class TestOrganizationsClientMoto:

    def test_standalone_account_is_not_a_management_account(self):
        with mock_aws():
            client = OrganizationsClient(session=_session())

            assert client.is_organization_management_account() is False
            assert client.list_organization_accounts() == []
            assert client.detect_cloudauditor_stackset() is None

    def test_management_account_lists_only_active_accounts(self):
        with mock_aws():
            org = boto3.client("organizations", region_name="us-east-1")
            org.create_organization(FeatureSet="ALL")
            created = org.create_account(
                Email="spoke@example.com", AccountName="Spoke"
            )
            spoke_id = created["CreateAccountStatus"]["AccountId"]
            org.close_account(AccountId=spoke_id)

            client = OrganizationsClient(session=_session())

            assert client.is_organization_management_account() is True
            accounts = client.list_organization_accounts()
            assert accounts
            assert {row["status"] for row in accounts} == {"ACTIVE"}
            assert spoke_id not in {row["account_id"] for row in accounts}
            assert any(row["account_id"] == "123456789012" for row in accounts)
            master = next(row for row in accounts if row["account_id"] == "123456789012")
            assert master["account_name"] == "master"

    def test_detects_cloudauditor_stackset_by_name(self):
        with mock_aws():
            cfn = boto3.client("cloudformation", region_name="us-east-1")
            template = '{"AWSTemplateFormatVersion": "2010-09-09"}'
            cfn.create_stack_set(StackSetName="OtherStack", TemplateBody=template)
            cfn.create_stack_set(
                StackSetName="CloudAuditorSpoke", TemplateBody=template
            )

            client = OrganizationsClient(session=_session())

            assert client.detect_cloudauditor_stackset() == "CloudAuditorSpoke"


class TestSecretsManagerMoto:

    def test_database_init_get_secret(self):
        with mock_aws():
            sm = boto3.client("secretsmanager", region_name="us-east-1")
            sm.create_secret(
                Name="db-creds",
                SecretString=json.dumps({"username": "admin", "password": "pw"}),
            )

            from database_init.app import get_secret

            assert get_secret("db-creds", "us-east-1") == {
                "username": "admin",
                "password": "pw",
            }

    def test_create_event_uses_secret_credentials(self, mocker):
        with mock_aws():
            sm = boto3.client("secretsmanager", region_name="us-east-1")
            secret = sm.create_secret(
                Name="db-creds",
                SecretString=json.dumps({"username": "admin", "password": "pw"}),
            )
            mocker.patch.dict(
                "os.environ",
                {
                    "DB_SECRET_ARN": secret["ARN"],
                    "DB_HOST": "db.example.internal",
                    "DB_NAME": "cloudauditor",
                    "AWS_REGION": "us-east-1",
                },
            )
            init = mocker.patch(
                "database_init.app.initialize_database",
                return_value=(True, "Initialized 4 tables"),
            )
            mocker.patch("database_init.app.send_response")

            from database_init.app import lambda_handler

            event = {
                "RequestType": "Create",
                "StackId": "arn:aws:cloudformation:us-east-1:123:stack/test/guid",
                "RequestId": "req-123",
                "LogicalResourceId": "DatabaseInit",
                "ResponseURL": "https://cfn-response.example.com",
            }
            context = MagicMock()
            context.log_stream_name = "stream"

            response = lambda_handler(event, context)

            assert response["statusCode"] == 200
            assert init.call_args.args[:4] == (
                "db.example.internal",
                "cloudauditor",
                "admin",
                "pw",
            )

    def test_database_client_loads_password_from_secret(self, mocker):
        with mock_aws():
            sm = boto3.client("secretsmanager", region_name="us-east-1")
            secret = sm.create_secret(
                Name="db-creds",
                SecretString=json.dumps({"username": "admin", "password": "pw"}),
            )
            mocker.patch.dict(
                "os.environ",
                {
                    "DB_HOST": "test-host",
                    "DB_NAME": "testdb",
                    "DB_USER": "env-user",
                    "DB_PORT": "5432",
                    "DB_SECRET_ARN": secret["ARN"],
                },
            )
            mocker.patch("lib.database.psycopg")

            client = DatabaseClient()

            assert client._config["password"] == "pw"
            assert client._config["user"] == "admin"
            assert client._config["port"] == 5432

    def test_database_client_survives_missing_secret(self, mocker):
        with mock_aws():
            mocker.patch.dict(
                "os.environ",
                {
                    "DB_HOST": "test-host",
                    "DB_NAME": "testdb",
                    "DB_USER": "env-user",
                    "DB_PORT": "5432",
                    "DB_SECRET_ARN": "arn:aws:secretsmanager:us-east-1:123456789012:secret:missing",
                },
            )
            mocker.patch("lib.database.psycopg")

            client = DatabaseClient()

            assert "password" not in client._config
            assert client._config["user"] == "env-user"


class TestStsAndRegionMoto:

    def test_verify_role_access_reads_sts_response(self):
        with mock_aws():
            result = IAMVerifier(session=_session()).verify_role_access("123456789012")

            assert result["success"] is True
            assert result["account_id"] == "123456789012"
            assert (
                "arn:aws:iam::123456789012:role/CloudAuditorExecutionRole"
                in result["message"]
            )
            assert result["verification_time"]

    def test_assumed_role_session_carries_temporary_credentials(self):
        with mock_aws():
            engine = ResourceDiscoveryEngine(
                session=_session(),
                config=DiscoveryConfig(
                    use_resource_explorer=False,
                    use_config=False,
                    use_cloud_control=False,
                ),
            )

            assumed = engine._get_assumed_role_session(
                "222222222222", role_name="CloudAuditorExecutionRole"
            )
            creds = assumed.get_credentials()

            assert creds.access_key
            assert creds.secret_key
            assert creds.token
            assert assumed.region_name == "us-east-1"

    def test_engine_loads_enabled_regions_from_ec2(self):
        with mock_aws():
            engine = ResourceDiscoveryEngine(
                session=_session(),
                config=DiscoveryConfig(
                    use_resource_explorer=False,
                    use_config=False,
                    use_cloud_control=False,
                ),
            )

            assert "us-east-1" in engine.enabled_regions
            assert "eu-west-1" in engine.enabled_regions
            assert engine.resource_explorer is None
            assert engine.config_client is None
            assert engine.cloud_control is None
