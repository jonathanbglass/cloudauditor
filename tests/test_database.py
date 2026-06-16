"""
Unit tests for lib.database (DatabaseClient)

All database interactions are mocked at the psycopg.connect boundary.
"""
import json
import pytest
from unittest.mock import MagicMock, patch, PropertyMock

from lib.database import DatabaseClient


# ===================================================================
# Helpers
# ===================================================================

def _make_db_client(env_vars=None, secret_response=None):
    """
    Build a DatabaseClient with mocked env + Secrets Manager.
    Returns (client, mock_conn, mock_cursor).
    """
    default_env = {
        "DB_HOST": "test-host",
        "DB_NAME": "testdb",
        "DB_USER": "testuser",
        "DB_PORT": "5432",
        "DB_SECRET_ARN": "arn:aws:secretsmanager:us-east-1:123:secret:db-secret",
    }
    if env_vars:
        default_env.update(env_vars)

    default_secret = secret_response or {
        "SecretString": json.dumps({"username": "dbadmin", "password": "s3cret"})
    }

    mock_cursor = MagicMock()
    mock_conn = MagicMock()
    mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
    mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
    mock_conn.closed = False

    with patch.dict("os.environ", default_env, clear=False), \
         patch("lib.database.boto3") as mock_boto3, \
         patch("lib.database.psycopg") as mock_psycopg:

        mock_sm = MagicMock()
        mock_sm.get_secret_value.return_value = default_secret
        # boto3.client('sts') and boto3.client('secretsmanager')
        mock_boto3.client.return_value = mock_sm

        mock_psycopg.connect.return_value = mock_conn

        client = DatabaseClient()
        # Force connection to use our mock
        client._conn = mock_conn

    return client, mock_conn, mock_cursor


# ===================================================================
# _load_config
# ===================================================================

class TestLoadConfig:

    def test_config_from_env_vars(self):
        client, _, _ = _make_db_client()
        assert client._config["host"] == "test-host"
        assert client._config["dbname"] == "testdb"
        assert client._config["port"] == 5432

    def test_password_from_secrets_manager(self):
        client, _, _ = _make_db_client()
        assert client._config["password"] == "s3cret"

    def test_username_override_from_secret(self):
        client, _, _ = _make_db_client()
        assert client._config["user"] == "dbadmin"

    def test_no_secret_arn(self):
        """When DB_SECRET_ARN is not set, password should not be fetched."""
        with patch.dict("os.environ", {
            "DB_HOST": "host",
            "DB_NAME": "db",
            "DB_USER": "user",
            "DB_PORT": "5432",
        }, clear=True), patch("lib.database.boto3"):
            client = DatabaseClient()
            assert client._config.get("password") is None


# ===================================================================
# get_monitored_accounts
# ===================================================================

class TestGetMonitoredAccounts:

    def test_returns_list(self):
        client, mock_conn, mock_cursor = _make_db_client()
        mock_cursor.fetchall.return_value = [
            ("111", "arn:aws:iam::111:role/Audit", "active"),
            ("222", "arn:aws:iam::222:role/Audit", "pending"),
        ]

        accounts = client.get_monitored_accounts()

        assert len(accounts) == 2
        assert accounts[0]["account_id"] == "111"
        assert accounts[0]["role_arn"] == "arn:aws:iam::111:role/Audit"
        assert accounts[0]["status"] == "active"

    def test_empty_result(self):
        client, _, mock_cursor = _make_db_client()
        mock_cursor.fetchall.return_value = []

        accounts = client.get_monitored_accounts()
        assert accounts == []


# ===================================================================
# register_account
# ===================================================================

class TestRegisterAccount:

    def test_insert_called(self):
        client, _, mock_cursor = _make_db_client()

        client.register_account("999", "arn:aws:iam::999:role/Audit", "ProdAccount")

        mock_cursor.execute.assert_called_once()
        sql = mock_cursor.execute.call_args[0][0]
        assert "INSERT INTO monitored_accounts" in sql
        assert "ON CONFLICT" in sql

    def test_auto_discovered_flag(self):
        client, _, mock_cursor = _make_db_client()

        client.register_account("999", "arn:aws:iam::999:role/Audit", auto_discovered=True)

        params = mock_cursor.execute.call_args[0][1]
        # auto_discovered should be True in the params tuple
        assert True in params


# ===================================================================
# update_account_status
# ===================================================================

class TestUpdateAccountStatus:

    def test_update_called(self):
        client, _, mock_cursor = _make_db_client()

        client.update_account_status("111", "active")

        mock_cursor.execute.assert_called_once()
        sql = mock_cursor.execute.call_args[0][0]
        assert "UPDATE monitored_accounts" in sql

    def test_error_message_passed(self):
        client, _, mock_cursor = _make_db_client()

        client.update_account_status("111", "error", last_error="STS timeout")

        params = mock_cursor.execute.call_args[0][1]
        assert "error" in params
        assert "STS timeout" in params


# ===================================================================
# save_resources
# ===================================================================

class TestSaveResources:

    def test_single_resource(self):
        client, _, mock_cursor = _make_db_client()

        resources = [{
            "id": "i-001",
            "resource_type": "AWS::EC2::Instance",
            "arn": "arn:aws:ec2:us-east-1:123:instance/i-001",
            "region": "us-east-1",
            "account_id": "123",
            "name": "web-1",
            "tags": {"Env": "prod"},
            "properties": {"type": "t3.micro"},
        }]

        client.save_resources(resources)
        mock_cursor.execute.assert_called_once()

    def test_batch_resources(self):
        client, _, mock_cursor = _make_db_client()

        resources = [
            {
                "id": f"i-{i:03d}",
                "resource_type": "AWS::EC2::Instance",
                "arn": f"arn:aws:ec2:us-east-1:123:instance/i-{i:03d}",
                "region": "us-east-1",
                "account_id": "123",
                "name": f"server-{i}",
                "tags": {},
                "properties": {},
            }
            for i in range(5)
        ]

        client.save_resources(resources)
        assert mock_cursor.execute.call_count == 5

    def test_region_normalization(self):
        """Empty/None region should be normalized to 'global'."""
        client, _, mock_cursor = _make_db_client()

        resources = [{
            "id": "my-bucket",
            "resource_type": "AWS::S3::Bucket",
            "arn": "arn:aws:s3:::my-bucket",
            "region": "",  # Empty → should become 'global'
            "account_id": "123",
            "name": "my-bucket",
            "tags": {},
            "properties": {},
        }]

        client.save_resources(resources)
        params = mock_cursor.execute.call_args[0][1]
        # region is the 4th parameter in the SQL
        assert "global" in params

    def test_none_region_normalization(self):
        client, _, mock_cursor = _make_db_client()

        resources = [{
            "id": "my-bucket",
            "resource_type": "AWS::S3::Bucket",
            "region": None,
            "account_id": "123",
            "tags": {},
            "properties": {},
        }]

        client.save_resources(resources)
        params = mock_cursor.execute.call_args[0][1]
        assert "global" in params


# ===================================================================
# Discovery run tracking
# ===================================================================

class TestDiscoveryRuns:

    def test_start_discovery_run(self):
        client, _, mock_cursor = _make_db_client()

        client.start_discovery_run("run-abc-123")

        sql = mock_cursor.execute.call_args[0][0]
        assert "INSERT INTO discovery_runs" in sql
        params = mock_cursor.execute.call_args[0][1]
        assert "run-abc-123" in params

    def test_complete_discovery_run(self):
        client, _, mock_cursor = _make_db_client()

        client.complete_discovery_run(
            "run-abc-123", "completed", 150, 12, 45.5, ["minor error"]
        )

        sql = mock_cursor.execute.call_args[0][0]
        assert "UPDATE discovery_runs" in sql
        params = mock_cursor.execute.call_args[0][1]
        assert "completed" in params
        assert 150 in params
        assert 12 in params


# ===================================================================
# Connection management
# ===================================================================

class TestConnectionManagement:

    def test_reuses_open_connection(self):
        client, mock_conn, _ = _make_db_client()
        mock_conn.closed = False

        conn1 = client._get_connection()
        conn2 = client._get_connection()
        assert conn1 is conn2

    def test_reconnects_when_closed(self):
        client, mock_conn, _ = _make_db_client()

        with patch("lib.database.psycopg") as mock_psycopg:
            new_conn = MagicMock()
            mock_psycopg.connect.return_value = new_conn
            # Mark old connection as closed
            mock_conn.closed = True

            conn = client._get_connection()
            assert conn is new_conn
