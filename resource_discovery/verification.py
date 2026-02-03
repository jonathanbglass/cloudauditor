import logging
import boto3
from botocore.exceptions import ClientError
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class IAMVerifier:
    """
    Verifies IAM trust and permissions for cross-account discovery.
    Provides detailed feedback for common failure modes.
    """
    
    def __init__(self, session: Optional[boto3.Session] = None):
        self.session = session or boto3.Session()

    def verify_role_access(self, account_id: str, role_name: str = "CloudAuditorExecutionRole") -> Dict[str, Any]:
        """
        Attempt to assume the target role and verify basic access.
        
        Returns:
            Dict containing success status, message, and troubleshooting tips if failed.
        """
        role_arn = f"arn:aws:iam::{account_id}:role/{role_name}"
        sts = self.session.client('sts')
        
        try:
            logger.info(f"Attempting to verify access to {role_arn}...")
            response = sts.assume_role(
                RoleArn=role_arn,
                RoleSessionName=f"CloudAuditorVerify-{account_id}"
            )
            
            # If we reached here, assume_role succeeded
            return {
                "success": True,
                "message": f"Successfully assumed role {role_arn}",
                "account_id": account_id,
                "verification_time": response['ResponseMetadata']['HTTPHeaders']['date']
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            logger.error(f"Verification failed: {error_code} - {error_message}")
            
            tips = []
            if error_code == 'AccessDenied':
                tips = [
                    "Verify that the Hub Account ID in your spoke-role.yaml is correct.",
                    f"Check that the role '{role_name}' exists in account {account_id}.",
                    "Ensure the Hub Lambda role has 'sts:AssumeRole' permission in template.yaml."
                ]
            elif error_code == 'NoAlternateRoleArnFound': # Custom or rare error
                tips = ["Check for typos in the Account ID or Role Name."]
            else:
                tips = ["Check AWS Service Health or IAM Policy limits."]
                
            return {
                "success": False,
                "error_code": error_code,
                "message": error_message,
                "troubleshooting_tips": tips
            }
        except Exception as e:
            logger.error(f"Unexpected error during verification: {str(e)}")
            return {
                "success": False,
                "error_code": "UnexpectedError",
                "message": str(e),
                "troubleshooting_tips": ["Check network connectivity and IAM session duration."]
            }
