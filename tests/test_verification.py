"""
Unit tests for resource_discovery.verification (IAMVerifier)

Tests cross-account role verification logic with mocked STS.
"""
import pytest
from unittest.mock import MagicMock, patch
from botocore.exceptions import ClientError

from resource_discovery.verification import IAMVerifier


def _make_verifier(session=None):
    if session is None:
        session = MagicMock()
    return IAMVerifier(session=session)


class TestVerifyRoleAccess:

    def test_success(self):
        verifier = _make_verifier()
        sts = MagicMock()
        sts.assume_role.return_value = {
            "Credentials": {
                "AccessKeyId": "AKIA...",
                "SecretAccessKey": "secret",
                "SessionToken": "token",
            },
            "ResponseMetadata": {
                "HTTPHeaders": {"date": "Mon, 31 Mar 2026 12:00:00 GMT"}
            },
        }
        verifier.session.client.return_value = sts

        result = verifier.verify_role_access("123456789012")

        assert result["success"] is True
        assert "123456789012" in result["message"]
        assert result["account_id"] == "123456789012"
        assert "verification_time" in result

    def test_access_denied(self):
        verifier = _make_verifier()
        sts = MagicMock()
        sts.assume_role.side_effect = ClientError(
            {"Error": {"Code": "AccessDenied", "Message": "Not authorized"}},
            "AssumeRole",
        )
        verifier.session.client.return_value = sts

        result = verifier.verify_role_access("123456789012")

        assert result["success"] is False
        assert result["error_code"] == "AccessDenied"
        assert len(result["troubleshooting_tips"]) > 0
        # Tips should mention common fixes
        assert any("Hub Account" in tip or "role" in tip.lower() for tip in result["troubleshooting_tips"])

    def test_unexpected_error(self):
        verifier = _make_verifier()
        sts = MagicMock()
        sts.assume_role.side_effect = Exception("Network timeout")
        verifier.session.client.return_value = sts

        result = verifier.verify_role_access("123456789012")

        assert result["success"] is False
        assert result["error_code"] == "UnexpectedError"
        assert "Network timeout" in result["message"]
        assert len(result["troubleshooting_tips"]) > 0

    def test_custom_role_name(self):
        verifier = _make_verifier()
        sts = MagicMock()
        sts.assume_role.return_value = {
            "Credentials": {
                "AccessKeyId": "AKIA...",
                "SecretAccessKey": "secret",
                "SessionToken": "token",
            },
            "ResponseMetadata": {
                "HTTPHeaders": {"date": "Mon, 31 Mar 2026 12:00:00 GMT"}
            },
        }
        verifier.session.client.return_value = sts

        result = verifier.verify_role_access("123456789012", role_name="CustomRole")

        assert result["success"] is True
        # Verify the correct role ARN was used
        call_args = sts.assume_role.call_args
        assert "CustomRole" in call_args.kwargs.get("RoleArn", call_args[1].get("RoleArn", ""))

    def test_role_arn_construction(self):
        """Verify the ARN is built correctly from account_id + role_name."""
        verifier = _make_verifier()
        sts = MagicMock()
        sts.assume_role.return_value = {
            "Credentials": {
                "AccessKeyId": "AKIA...",
                "SecretAccessKey": "secret",
                "SessionToken": "token",
            },
            "ResponseMetadata": {
                "HTTPHeaders": {"date": "Mon, 31 Mar 2026 12:00:00 GMT"}
            },
        }
        verifier.session.client.return_value = sts

        verifier.verify_role_access("999888777666", role_name="MyAuditRole")

        call_args = sts.assume_role.call_args
        role_arn = call_args.kwargs.get("RoleArn") or call_args[1].get("RoleArn")
        assert role_arn == "arn:aws:iam::999888777666:role/MyAuditRole"

    def test_other_client_error(self):
        """Non-AccessDenied ClientErrors should get generic tips."""
        verifier = _make_verifier()
        sts = MagicMock()
        sts.assume_role.side_effect = ClientError(
            {"Error": {"Code": "RegionDisabledException", "Message": "Region disabled"}},
            "AssumeRole",
        )
        verifier.session.client.return_value = sts

        result = verifier.verify_role_access("123456789012")

        assert result["success"] is False
        assert result["error_code"] == "RegionDisabledException"
        assert len(result["troubleshooting_tips"]) > 0

    def test_default_session_used(self):
        """When no session passed, should create a default boto3 session."""
        with patch("resource_discovery.verification.boto3.Session") as mock_session_cls:
            mock_session = MagicMock()
            mock_session_cls.return_value = mock_session
            verifier = IAMVerifier()
            assert verifier.session is mock_session
