"""
Unit tests for lib.organizations (OrganizationsClient)

Tests Organization detection, account enumeration, and StackSet detection.
"""
import pytest
from unittest.mock import MagicMock, patch, call
from botocore.exceptions import ClientError

from lib.organizations import OrganizationsClient


def _make_client(session=None):
    if session is None:
        session = MagicMock()
    return OrganizationsClient(session=session)


# ===================================================================
# is_organization_management_account
# ===================================================================

class TestIsOrganizationManagementAccount:

    def test_is_management_account(self):
        client = _make_client()
        client.org_client.describe_organization.return_value = {
            "Organization": {
                "Id": "o-abc123",
                "Arn": "arn:aws:organizations::111111111111:organization/o-abc123",
                "MasterAccountId": "111111111111",
            }
        }
        sts = MagicMock()
        sts.get_caller_identity.return_value = {"Account": "111111111111"}
        client.session.client.return_value = sts

        assert client.is_organization_management_account() is True

    def test_is_not_management_account(self):
        client = _make_client()
        client.org_client.describe_organization.return_value = {
            "Organization": {
                "Id": "o-abc123",
                "MasterAccountId": "111111111111",
            }
        }
        sts = MagicMock()
        sts.get_caller_identity.return_value = {"Account": "222222222222"}
        client.session.client.return_value = sts

        assert client.is_organization_management_account() is False

    def test_not_in_organization(self):
        client = _make_client()
        client.org_client.describe_organization.side_effect = ClientError(
            {"Error": {"Code": "AWSOrganizationsNotInUseException", "Message": "Not in org"}},
            "DescribeOrganization",
        )

        assert client.is_organization_management_account() is False

    def test_access_denied(self):
        client = _make_client()
        client.org_client.describe_organization.side_effect = ClientError(
            {"Error": {"Code": "AccessDeniedException", "Message": "denied"}},
            "DescribeOrganization",
        )

        assert client.is_organization_management_account() is False

    def test_other_client_error(self):
        client = _make_client()
        client.org_client.describe_organization.side_effect = ClientError(
            {"Error": {"Code": "ServiceException", "Message": "service error"}},
            "DescribeOrganization",
        )

        assert client.is_organization_management_account() is False


# ===================================================================
# list_organization_accounts
# ===================================================================

class TestListOrganizationAccounts:

    def test_returns_active_accounts(self):
        client = _make_client()
        paginator = MagicMock()
        paginator.paginate.return_value = [
            {
                "Accounts": [
                    {"Id": "111", "Name": "Mgmt", "Email": "mgmt@co.com", "Status": "ACTIVE"},
                    {"Id": "222", "Name": "Dev", "Email": "dev@co.com", "Status": "ACTIVE"},
                    {"Id": "333", "Name": "Old", "Email": "old@co.com", "Status": "SUSPENDED"},
                ]
            }
        ]
        client.org_client.get_paginator.return_value = paginator

        accounts = client.list_organization_accounts()

        assert len(accounts) == 2
        ids = [a["account_id"] for a in accounts]
        assert "111" in ids
        assert "222" in ids
        assert "333" not in ids

    def test_filters_out_suspended(self):
        client = _make_client()
        paginator = MagicMock()
        paginator.paginate.return_value = [
            {
                "Accounts": [
                    {"Id": "111", "Name": "Suspended", "Status": "SUSPENDED"},
                ]
            }
        ]
        client.org_client.get_paginator.return_value = paginator

        accounts = client.list_organization_accounts()
        assert len(accounts) == 0

    def test_account_dict_structure(self):
        client = _make_client()
        paginator = MagicMock()
        paginator.paginate.return_value = [
            {
                "Accounts": [
                    {"Id": "111", "Name": "Prod", "Email": "prod@co.com", "Status": "ACTIVE"},
                ]
            }
        ]
        client.org_client.get_paginator.return_value = paginator

        accounts = client.list_organization_accounts()
        acct = accounts[0]
        assert acct["account_id"] == "111"
        assert acct["account_name"] == "Prod"
        assert acct["email"] == "prod@co.com"
        assert acct["status"] == "ACTIVE"

    def test_multi_page_pagination(self):
        client = _make_client()
        paginator = MagicMock()
        paginator.paginate.return_value = [
            {"Accounts": [{"Id": "111", "Name": "A1", "Status": "ACTIVE"}]},
            {"Accounts": [{"Id": "222", "Name": "A2", "Status": "ACTIVE"}]},
        ]
        client.org_client.get_paginator.return_value = paginator

        accounts = client.list_organization_accounts()
        assert len(accounts) == 2

    def test_client_error_returns_empty(self):
        client = _make_client()
        client.org_client.get_paginator.side_effect = ClientError(
            {"Error": {"Code": "AccessDeniedException", "Message": "denied"}},
            "ListAccounts",
        )

        accounts = client.list_organization_accounts()
        assert accounts == []

    def test_missing_name_defaults_to_unknown(self):
        client = _make_client()
        paginator = MagicMock()
        paginator.paginate.return_value = [
            {"Accounts": [{"Id": "111", "Status": "ACTIVE"}]},
        ]
        client.org_client.get_paginator.return_value = paginator

        accounts = client.list_organization_accounts()
        assert accounts[0]["account_name"] == "Unknown"


# ===================================================================
# detect_cloudauditor_stackset
# ===================================================================

class TestDetectCloudAuditorStackSet:

    def test_stackset_found(self):
        client = _make_client()
        client.cfn_client.list_stack_sets.return_value = {
            "Summaries": [
                {"StackSetName": "CloudAuditor-SpokeRoles"},
                {"StackSetName": "OtherStackSet"},
            ]
        }

        result = client.detect_cloudauditor_stackset()
        assert result == "CloudAuditor-SpokeRoles"

    def test_stackset_not_found(self):
        client = _make_client()
        client.cfn_client.list_stack_sets.return_value = {
            "Summaries": [
                {"StackSetName": "UnrelatedStack"},
            ]
        }

        result = client.detect_cloudauditor_stackset()
        assert result is None

    def test_case_insensitive_match(self):
        client = _make_client()
        client.cfn_client.list_stack_sets.return_value = {
            "Summaries": [
                {"StackSetName": "CLOUDAUDITOR-production"},
            ]
        }

        result = client.detect_cloudauditor_stackset()
        assert result == "CLOUDAUDITOR-production"

    def test_empty_summaries(self):
        client = _make_client()
        client.cfn_client.list_stack_sets.return_value = {"Summaries": []}

        result = client.detect_cloudauditor_stackset()
        assert result is None

    def test_client_error_returns_none(self):
        client = _make_client()
        client.cfn_client.list_stack_sets.side_effect = ClientError(
            {"Error": {"Code": "AccessDeniedException", "Message": "denied"}},
            "ListStackSets",
        )

        result = client.detect_cloudauditor_stackset()
        assert result is None
