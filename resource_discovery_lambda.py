"""
Lambda handler for resource discovery
Triggered by CloudWatch Events (scheduled)
"""
import json
import logging
import os
from typing import Dict, Any

import boto3
from resource_discovery import ResourceDiscoveryEngine, DiscoveryConfig
from lib.database import DatabaseClient
from lib.organizations import OrganizationsClient

# Configure logging
logger = logging.getLogger()
logger.setLevel(os.environ.get('LOG_LEVEL', 'INFO'))


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for scheduled resource discovery.
    
    Args:
        event: CloudWatch Events event
        context: Lambda context
        
    Returns:
        Response with discovery results
    """
    logger.info("Starting resource discovery")
    logger.info(f"Event: {json.dumps(event)}")
    
    try:
        # Initialize clients
        db = DatabaseClient()
        org_client = OrganizationsClient()
        
        # 1. Check if this is an Organization Management account
        try:
            if org_client.is_organization_management_account():
                logger.info("Running in Organization Management account - auto-discovering member accounts...")
                
                # Get all Organization accounts
                org_accounts = org_client.list_organization_accounts()
                logger.info(f"Found {len(org_accounts)} Organization accounts")
                
                # Get existing monitored accounts
                existing_accounts = {a['account_id'] for a in db.get_monitored_accounts()}
                logger.info(f"Currently monitoring {len(existing_accounts)} accounts")
                
                # Auto-register any new accounts
                new_accounts = 0
                for account in org_accounts:
                    if account['account_id'] not in existing_accounts:
                        try:
                            role_arn = f"arn:aws:iam::{account['account_id']}:role/CloudAuditorExecutionRole"
                            db.register_account(
                                account['account_id'],
                                role_arn,
                                account['account_name'],
                                auto_discovered=True
                            )
                            new_accounts += 1
                            logger.info(f"Auto-registered account: {account['account_id']} ({account['account_name']})")
                        except Exception as reg_error:
                            logger.error(f"Failed to register account {account['account_id']}: {str(reg_error)}")
                
                if new_accounts > 0:
                    logger.info(f"Auto-registered {new_accounts} new Organization member accounts.")
                else:
                    logger.info("No new Organization accounts to register.")
        except Exception as org_error:
            logger.error(f"Organizations auto-discovery failed: {str(org_error)}")
            logger.info("Continuing with existing monitored accounts...")
        
        # 2. Fetch all monitored accounts from DB
        try:
            accounts_to_scan = db.get_monitored_accounts()
            account_ids = [a['account_id'] for a in accounts_to_scan]
            logger.info(f"Retrieved {len(account_ids)} monitored accounts from database")
        except Exception as db_error:
            logger.error(f"Failed to fetch monitored accounts from database: {str(db_error)}")
            account_ids = []
        
        if not account_ids:
            logger.info("No monitored accounts found. Checking local account...")
            sts = boto3.client('sts')
            account_ids = [sts.get_caller_identity()['Account']]
            logger.info(f"Using local account: {account_ids[0]}")

        # 3. Configure discovery
        config = DiscoveryConfig(
            accounts=account_ids,
            use_resource_explorer=True,
            use_config=True,
            use_cloud_control=False,
            max_workers=10
        )
        
        # 3. Run discovery
        engine = ResourceDiscoveryEngine(config=config)
        result = engine.discover_all_resources()
        
        # 4. Save results to Database
        resources_to_save = []
        for r in result.resources:
            r_dict = r.to_dict()
            # Map source value for DB
            r_dict['properties'] = r_dict.get('configuration', {})
            resources_to_save.append(r_dict)
            
        if resources_to_save:
            logger.info(f"Saving {len(resources_to_save)} resources to database...")
            db.save_resources(resources_to_save)
            
        # 5. Update account status based on scan
        # (Simplified: if we got here, mark active accounts as active)
        for account_id in account_ids:
            db.update_account_status(account_id, 'active')

        # Log summary
        logger.info(f"Discovery complete: {result.total_count} resources in {result.duration_seconds:.2f}s")
        
        if result.errors:
            logger.warning(f"Errors encountered: {result.errors}")
            # Update specific account if it failed (heuristic: check error string)
            for err in result.errors:
                for account_id in account_ids:
                    if account_id in err:
                        db.update_account_status(account_id, 'error', last_error=err)
        
        summary = engine.get_resource_summary(result)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'success': result.success,
                'total_resources': result.total_count,
                'duration_seconds': result.duration_seconds,
                'resource_types': len(summary),
                'errors': result.errors
            })
        }
        
    except Exception as e:
        logger.exception("Resource discovery failed")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'success': False,
                'error': str(e)
            })
        }
