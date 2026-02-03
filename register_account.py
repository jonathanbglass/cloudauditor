import argparse
import logging
import sys
from typing import Optional

from resource_discovery.verification import IAMVerifier
from resource_discovery.discovery_engine import ResourceDiscoveryEngine
from resource_discovery.models import DiscoveryConfig
from reporting.excel_generator import ExcelGenerator
from lib.database import DatabaseClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("AccountRegistration")

def register_account(account_id: str, account_name: Optional[str] = None):
    """
    Register a new account, verify access, and trigger initial discovery.
    """
    logger.info(f"--- Registering Account: {account_id} ---")
    
    # 1. IAM Pre-flight Check
    verifier = IAMVerifier()
    verification = verifier.verify_role_access(account_id)
    
    if not verification['success']:
        logger.error(f"❌ Verification Failed: {verification['message']}")
        print("\n💡 Troubleshooting Tips:")
        for tip in verification.get('troubleshooting_tips', []):
            print(f"  - {tip}")
        sys.exit(1)
        
    logger.info(f"✅ Verification Successful: {verification['message']}")
    
    # 2. Add to Monitored Accounts
    logger.info(f"Registering {account_id} in Monitored Accounts database...")
    db = DatabaseClient()
    role_arn = f"arn:aws:iam::{account_id}:role/CloudAuditorExecutionRole"
    db.register_account(account_id, role_arn, account_name)
    
    # 3. Trigger Initial Discovery
    logger.info("🚀 Kicking off initial inventory scan...")
    config = DiscoveryConfig(accounts=[account_id])
    engine = ResourceDiscoveryEngine(config=config)
    
    result = engine.discover_all_resources()
    
    if result.success:
        logger.info(f"✨ Initial discovery complete! Found {result.total_count} resources.")
        db.update_account_status(account_id, 'active')
        
        # Save resources to DB
        resources_to_save = []
        for r in result.resources:
            r_dict = r.to_dict()
            r_dict['properties'] = r_dict.get('configuration', {})
            resources_to_save.append(r_dict)
        db.save_resources(resources_to_save)
        
        # 4. Generate Initial Report (Optional but nice)
        generator = ExcelGenerator()
        report_path = generator.generate_report(result, filename=f"Initial_Scan_{account_id}.xlsx")
        logger.info(f"📊 Initial report generated: {report_path}")
    else:
        logger.error(f"⚠️ Discovery finished with errors: {result.errors}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Register and verify a new AWS account for CloudAuditor.")
    parser.add_argument("account_id", help="The 12-digit AWS Account ID to register.")
    parser.add_argument("--name", help="A friendly name for the account.")
    
    args = parser.parse_args()
    
    if len(args.account_id) != 12 or not args.account_id.isdigit():
        logger.error("Invalid Account ID. Must be a 12-digit number.")
        sys.exit(1)
        
    register_account(args.account_id, args.name)
