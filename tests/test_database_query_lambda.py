"""
Unit tests for database_query_lambda.lambda_handler

Tests each report_type path with mocked DatabaseClient.
"""
import json
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime


@pytest.fixture
def mock_context():
    ctx = MagicMock()
    ctx.log_stream_name = "test-log-stream"
    return ctx


def _import_handler():
    from database_query_lambda import lambda_handler
    return lambda_handler


class TestDatabaseQueryLambda:

    @patch("database_query_lambda.DatabaseClient")
    def test_summary_report(self, mock_db_cls, mock_context):
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

        # Each fetchone call returns a single value
        mock_cursor.fetchone.side_effect = [
            (150,),   # total_resources
            (12,),    # unique_types
            (3,),     # unique_accounts
            (3,),     # monitored_accounts
            (datetime(2026, 3, 30),),  # latest_scan
        ]

        mock_db = MagicMock()
        mock_db._get_connection.return_value = mock_conn
        mock_db_cls.return_value = mock_db

        handler = _import_handler()
        response = handler({"report_type": "summary"}, mock_context)

        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["success"] is True
        assert body["results"]["total_resources"] == 150

    @patch("database_query_lambda.DatabaseClient")
    def test_accounts_report(self, mock_db_cls, mock_context):
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

        mock_cursor.fetchall.return_value = [
            ("111", "Prod", "active", False, datetime(2026, 3, 30), None),
            ("222", "Dev", "pending", True, None, None),
        ]

        mock_db = MagicMock()
        mock_db._get_connection.return_value = mock_conn
        mock_db_cls.return_value = mock_db

        handler = _import_handler()
        response = handler({"report_type": "accounts"}, mock_context)

        body = json.loads(response["body"])
        assert body["results"]["count"] == 2
        assert body["results"]["accounts"][0]["account_id"] == "111"

    @patch("database_query_lambda.DatabaseClient")
    def test_by_type_report(self, mock_db_cls, mock_context):
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

        mock_cursor.fetchall.return_value = [
            ("AWS::EC2::Instance", 50),
            ("AWS::S3::Bucket", 30),
        ]

        mock_db = MagicMock()
        mock_db._get_connection.return_value = mock_conn
        mock_db_cls.return_value = mock_db

        handler = _import_handler()
        response = handler({"report_type": "by_type"}, mock_context)

        body = json.loads(response["body"])
        assert body["results"]["count"] == 2
        assert body["results"]["resource_types"][0]["resource_type"] == "AWS::EC2::Instance"

    @patch("database_query_lambda.DatabaseClient")
    def test_by_account_report(self, mock_db_cls, mock_context):
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

        mock_cursor.fetchall.return_value = [
            ("111", 80, 10),
            ("222", 40, 5),
        ]

        mock_db = MagicMock()
        mock_db._get_connection.return_value = mock_conn
        mock_db_cls.return_value = mock_db

        handler = _import_handler()
        response = handler({"report_type": "by_account"}, mock_context)

        body = json.loads(response["body"])
        assert body["results"]["accounts"][0]["resource_count"] == 80

    @patch("database_query_lambda.DatabaseClient")
    def test_resources_report_with_limit(self, mock_db_cls, mock_context):
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

        mock_cursor.fetchall.return_value = [
            ("111", "us-east-1", "AWS::EC2::Instance", "i-001", "web", datetime(2026, 3, 30)),
        ]

        mock_db = MagicMock()
        mock_db._get_connection.return_value = mock_conn
        mock_db_cls.return_value = mock_db

        handler = _import_handler()
        response = handler({"report_type": "resources", "limit": 10}, mock_context)

        body = json.loads(response["body"])
        assert body["results"]["count"] == 1

    @patch("database_query_lambda.DatabaseClient")
    def test_custom_query(self, mock_db_cls, mock_context):
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

        mock_cursor.fetchall.return_value = [(42,)]

        mock_db = MagicMock()
        mock_db._get_connection.return_value = mock_conn
        mock_db_cls.return_value = mock_db

        handler = _import_handler()
        response = handler({"query": "SELECT COUNT(*) FROM resources"}, mock_context)

        body = json.loads(response["body"])
        assert body["results"]["row_count"] == 1
        assert body["results"]["rows"] == [[42]]

    @patch("database_query_lambda.DatabaseClient")
    def test_unknown_report_type(self, mock_db_cls, mock_context):
        mock_db = MagicMock()
        mock_conn = MagicMock()
        mock_db._get_connection.return_value = mock_conn
        mock_db_cls.return_value = mock_db

        handler = _import_handler()
        response = handler({"report_type": "invalid_type"}, mock_context)

        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert "error" in body

    @patch("database_query_lambda.DatabaseClient")
    def test_exception_returns_500(self, mock_db_cls, mock_context):
        mock_db_cls.side_effect = Exception("Connection failed")

        handler = _import_handler()
        response = handler({"report_type": "summary"}, mock_context)

        assert response["statusCode"] == 500
        body = json.loads(response["body"])
        assert body["success"] is False

    @patch("database_query_lambda.DatabaseClient")
    def test_account_ids_filtering(self, mock_db_cls, mock_context):
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

        mock_cursor.fetchone.side_effect = [(50,), (5,), (1,), (1,), (datetime(2026, 3, 30),)]

        mock_db = MagicMock()
        mock_db._get_connection.return_value = mock_conn
        mock_db_cls.return_value = mock_db

        handler = _import_handler()
        response = handler({
            "report_type": "summary",
            "account_ids": ["111", "222"],
        }, mock_context)

        assert response["statusCode"] == 200
        # Verify SQL was parameterized with account IDs
        execute_calls = mock_cursor.execute.call_args_list
        sql_calls = [c[0][0] for c in execute_calls]
        # At least one query should contain the IN clause
        assert any("IN" in sql for sql in sql_calls)
