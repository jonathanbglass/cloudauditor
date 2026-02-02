import logging
import boto3
from botocore.exceptions import ClientError
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class OrganizationsClient:
    """
    Client for interacting with AWS Organizations.
    Detects Organization Management accounts and enumerates member accounts.
    """
    
    def __init__(self, session: Optional[boto3.Session] = None):
        self.session = session or boto3.Session()
        self.org_client = self.session.client('organizations')
        self.cfn_client = self.session.client('cloudformation')
        
    def is_organization_management_account(self) -> bool:
        """
        Check if the current account is an Organization Management account.
        
        Returns:
            True if this is a Management account, False otherwise.
        """
        try:
            response = self.org_client.describe_organization()
            org = response.get('Organization', {})
            
            # Get current account ID
            sts = self.session.client('sts')
            current_account = sts.get_caller_identity()['Account']
            
            # Check if current account is the management account
            is_mgmt = org.get('MasterAccountId') == current_account
            
            if is_mgmt:
                logger.info(f"Detected Organization Management Account: {current_account}")
                logger.info(f"Organization ID: {org.get('Id')}, ARN: {org.get('Arn')}")
            
            return is_mgmt
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'AWSOrganizationsNotInUseException':
                logger.info("This account is not part of an AWS Organization.")
                return False
            elif error_code == 'AccessDeniedException':
                logger.warning("No permissions to check Organizations. Assuming standalone account.")
                return False
            else:
                logger.error(f"Error checking Organization status: {e}")
                return False
    
    def list_organization_accounts(self) -> List[Dict[str, Any]]:
        """
        List all accounts in the Organization.
        
        Returns:
            List of account dictionaries with 'Id', 'Name', 'Status', 'Email'.
        """
        try:
            accounts = []
            paginator = self.org_client.get_paginator('list_accounts')
            
            for page in paginator.paginate():
                for account in page.get('Accounts', []):
                    # Only include ACTIVE accounts
                    if account.get('Status') == 'ACTIVE':
                        accounts.append({
                            'account_id': account['Id'],
                            'account_name': account.get('Name', 'Unknown'),
                            'email': account.get('Email'),
                            'status': account.get('Status')
                        })
            
            logger.info(f"Found {len(accounts)} active accounts in the Organization.")
            return accounts
            
        except ClientError as e:
            logger.error(f"Error listing Organization accounts: {e}")
            return []
    
    def detect_cloudauditor_stackset(self) -> Optional[str]:
        """
        Detect if there's a StackSet with 'CloudAuditor' in the name.
        
        Returns:
            StackSet name if found, None otherwise.
        """
        try:
            response = self.cfn_client.list_stack_sets()
            
            for summary in response.get('Summaries', []):
                stack_name = summary.get('StackSetName', '')
                if 'cloudauditor' in stack_name.lower():
                    logger.info(f"Detected CloudAuditor StackSet: {stack_name}")
                    return stack_name
            
            logger.info("No CloudAuditor StackSet detected.")
            return None
            
        except ClientError as e:
            logger.warning(f"Unable to check for StackSets: {e}")
            return None
