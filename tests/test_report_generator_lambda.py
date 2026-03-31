"""
Unit tests for report_generator_lambda

Tests report generation pipeline, S3 upload, and handler logic.
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


@pytest.fixture
def env_vars():
    return {
        "DB_SECRET_ARN": "arn:aws:secretsmanager:us-east-1:123:secret:db",
        "DB_HOST": "test-host",
        "DB_NAME": "testdb",
        "AWS_REGION": "us-east-1",
        "REPORT_BUCKET": "test-bucket",
    }


class TestReportGeneratorLambda:

    @patch("report_generator_lambda.upload_to_s3")
    @patch("report_generator_lambda.generate_excel_report")
    @patch("report_generator_lambda.fetch_resources_from_database")
    @patch("report_generator_lambda.get_secret")
    def test_handler_generates_and_uploads(self, mock_secret, mock_fetch, mock_excel,
                                           mock_upload, env_vars, mock_context):
        with patch.dict("os.environ", env_vars):
            mock_secret.return_value = {"username": "user", "password": "pass"}
            mock_fetch.return_value = [
                {"arn": "arn:aws:ec2:us-east-1:123:i/i-001", "resource_type": "AWS::EC2::Instance",
                 "region": "us-east-1", "account_id": "123", "name": "web",
                 "resource_id": "i-001"},
            ]
            mock_excel.return_value = b"fake-excel-bytes"
            mock_upload.return_value = "https://s3.amazonaws.com/presigned-url"

            from report_generator_lambda import lambda_handler
            response = lambda_handler({}, mock_context)

            assert response["statusCode"] == 200
            body = json.loads(response["body"])
            assert body["success"] is True
            assert body["resource_count"] == 1
            assert "download_url" in body
            mock_upload.assert_called_once()

    @patch("report_generator_lambda.fetch_resources_from_database")
    @patch("report_generator_lambda.get_secret")
    def test_handler_no_resources(self, mock_secret, mock_fetch, env_vars, mock_context):
        with patch.dict("os.environ", env_vars):
            mock_secret.return_value = {"username": "user", "password": "pass"}
            mock_fetch.return_value = []

            from report_generator_lambda import lambda_handler
            response = lambda_handler({}, mock_context)

            assert response["statusCode"] == 200
            body = json.loads(response["body"])
            assert body["resource_count"] == 0

    @patch("report_generator_lambda.get_secret")
    def test_handler_error_response(self, mock_secret, env_vars, mock_context):
        with patch.dict("os.environ", env_vars):
            mock_secret.side_effect = Exception("Secrets Manager unavailable")

            from report_generator_lambda import lambda_handler
            response = lambda_handler({}, mock_context)

            assert response["statusCode"] == 500
            body = json.loads(response["body"])
            assert body["success"] is False


class TestFetchResources:

    @patch("report_generator_lambda.psycopg")
    def test_latest_only_query(self, mock_psycopg):
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
        mock_psycopg.connect.return_value = mock_conn
        mock_cursor.fetchall.return_value = []

        from report_generator_lambda import fetch_resources_from_database
        fetch_resources_from_database("host", "db", "user", "pass", latest_only=True)

        sql = mock_cursor.execute.call_args[0][0]
        assert "latest_date" in sql
        assert "inserted_at" in sql

    @patch("report_generator_lambda.psycopg")
    def test_all_resources_query(self, mock_psycopg):
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
        mock_psycopg.connect.return_value = mock_conn
        mock_cursor.fetchall.return_value = []

        from report_generator_lambda import fetch_resources_from_database
        fetch_resources_from_database("host", "db", "user", "pass", latest_only=False)

        sql = mock_cursor.execute.call_args[0][0]
        assert "latest_date" not in sql

    @patch("report_generator_lambda.psycopg")
    def test_account_ids_filtering(self, mock_psycopg):
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
        mock_psycopg.connect.return_value = mock_conn
        mock_cursor.fetchall.return_value = []

        from report_generator_lambda import fetch_resources_from_database
        fetch_resources_from_database("host", "db", "user", "pass",
                                      account_ids=["111", "222"])

        sql = mock_cursor.execute.call_args[0][0]
        assert "account_id IN" in sql


class TestUploadToS3:

    @patch("report_generator_lambda.boto3")
    def test_presigned_url_generated(self, mock_boto3):
        mock_s3 = MagicMock()
        mock_s3.generate_presigned_url.return_value = "https://presigned.url"
        mock_boto3.client.return_value = mock_s3

        from report_generator_lambda import upload_to_s3
        url = upload_to_s3(b"content", "my-bucket", "reports/test.xlsx")

        assert url == "https://presigned.url"
        mock_s3.put_object.assert_called_once()
        mock_s3.generate_presigned_url.assert_called_once()

        # Verify content disposition for download
        presign_args = mock_s3.generate_presigned_url.call_args
        params = presign_args[1].get("Params") or presign_args[0][1]
        assert "ResponseContentDisposition" in params


class TestGenerateExcelReport:

    def test_empty_resources_returns_none(self):
        from report_generator_lambda import generate_excel_report
        result = generate_excel_report([])
        assert result is None

    def test_returns_bytes(self):
        from report_generator_lambda import generate_excel_report
        resources = [
            {
                "arn": "arn:aws:ec2:us-east-1:123:i/i-001",
                "resource_type": "AWS::EC2::Instance",
                "region": "us-east-1",
                "account_id": "123",
                "name": "web",
                "tags": {},
                "configuration": {},
                "resource_id": "i-001",
                "discovered_at": "2026-03-30T00:00:00Z",
                "last_seen_at": "2026-03-30T00:00:00Z",
                "inserted_at": "2026-03-30T00:00:00Z",
            }
        ]
        result = generate_excel_report(resources)
        assert isinstance(result, bytes)
        assert len(result) > 0
