"""
Unit tests for database_init.app (Database Initialization Lambda)

Tests CloudFormation Custom Resource handling and schema initialization.
"""
import json
import pytest
from unittest.mock import MagicMock, patch, call


@pytest.fixture
def mock_context():
    ctx = MagicMock()
    ctx.log_stream_name = "test-log-stream"
    return ctx


@pytest.fixture
def cfn_create_event():
    return {
        "RequestType": "Create",
        "StackId": "arn:aws:cloudformation:us-east-1:123:stack/test/guid",
        "RequestId": "req-123",
        "LogicalResourceId": "DatabaseInit",
        "ResponseURL": "https://cfn-response.example.com",
    }


@pytest.fixture
def cfn_update_event(cfn_create_event):
    return {**cfn_create_event, "RequestType": "Update"}


@pytest.fixture
def cfn_delete_event(cfn_create_event):
    return {**cfn_create_event, "RequestType": "Delete"}


@pytest.fixture
def env_vars():
    return {
        "DB_SECRET_ARN": "arn:aws:secretsmanager:us-east-1:123:secret:db",
        "DB_HOST": "test-host",
        "DB_NAME": "testdb",
        "AWS_REGION": "us-east-1",
    }


class TestDatabaseInitLambda:

    @patch("database_init.app.send_response")
    @patch("database_init.app.initialize_database")
    @patch("database_init.app.get_secret")
    def test_cfn_create_event(self, mock_secret, mock_init, mock_send,
                              cfn_create_event, env_vars, mock_context):
        with patch.dict("os.environ", env_vars):
            mock_secret.return_value = {"username": "admin", "password": "pass"}
            mock_init.return_value = (True, "Created 3 tables")

            from database_init.app import lambda_handler
            response = lambda_handler(cfn_create_event, mock_context)

            assert response["statusCode"] == 200
            mock_init.assert_called_once()
            mock_send.assert_called_once()
            # Verify send_response was called with SUCCESS
            send_args = mock_send.call_args[0]
            assert send_args[2] == "SUCCESS"

    @patch("database_init.app.send_response")
    @patch("database_init.app.get_secret")
    def test_cfn_update_event(self, mock_secret, mock_send,
                              cfn_update_event, env_vars, mock_context):
        with patch.dict("os.environ", env_vars):
            from database_init.app import lambda_handler
            response = lambda_handler(cfn_update_event, mock_context)

            assert response["statusCode"] == 200
            body = json.loads(response["body"])
            assert "Update" in body["message"]
            mock_send.assert_called_once()

    @patch("database_init.app.send_response")
    @patch("database_init.app.get_secret")
    def test_cfn_delete_event(self, mock_secret, mock_send,
                              cfn_delete_event, env_vars, mock_context):
        with patch.dict("os.environ", env_vars):
            from database_init.app import lambda_handler
            response = lambda_handler(cfn_delete_event, mock_context)

            assert response["statusCode"] == 200
            mock_send.assert_called_once()

    @patch("database_init.app.initialize_database")
    @patch("database_init.app.get_secret")
    def test_manual_invocation(self, mock_secret, mock_init, env_vars, mock_context):
        with patch.dict("os.environ", env_vars):
            mock_secret.return_value = {"username": "admin", "password": "pass"}
            mock_init.return_value = (True, "Created tables")

            from database_init.app import lambda_handler
            # Manual invocation - no CFN fields
            response = lambda_handler({}, mock_context)

            assert response["statusCode"] == 200
            mock_init.assert_called_once()


class TestInitializeDatabase:

    @patch("database_init.app.psycopg")
    def test_schema_execution(self, mock_psycopg):
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_psycopg.connect.return_value = mock_conn
        mock_cursor.fetchall.return_value = [
            ("resources",), ("resource_relationships",), ("discovery_runs",)
        ]

        from database_init.app import initialize_database
        success, message = initialize_database("host", "db", "user", "pass")

        assert success is True
        assert "3" in message
        # Verify cursor.execute was called (schema + migration)
        assert mock_cursor.execute.call_count >= 2

    @patch("database_init.app.psycopg")
    def test_connection_error(self, mock_psycopg):
        mock_psycopg.connect.side_effect = Exception("Connection refused")

        from database_init.app import initialize_database
        with pytest.raises(Exception, match="Connection refused"):
            initialize_database("host", "db", "user", "pass")


class TestSendResponse:

    @patch("database_init.app.http")
    def test_response_format(self, mock_http):
        from database_init.app import send_response
        event = {
            "StackId": "stack-123",
            "RequestId": "req-123",
            "LogicalResourceId": "DbInit",
            "ResponseURL": "https://cfn.example.com/response",
        }
        context = MagicMock()
        context.log_stream_name = "log-stream"

        send_response(event, context, "SUCCESS", {"Message": "OK"})

        mock_http.request.assert_called_once()
        call_args = mock_http.request.call_args
        assert call_args[0][0] == "PUT"
        assert call_args[0][1] == "https://cfn.example.com/response"

        body = json.loads(call_args[1]["body"])
        assert body["Status"] == "SUCCESS"
        assert body["StackId"] == "stack-123"
