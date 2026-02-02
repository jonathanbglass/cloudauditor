#!/usr/bin/env python3
"""
Generate Excel report from CloudAuditor Aurora database
"""
import argparse
import logging
import json
import sys
import os
from datetime import datetime
import boto3
import psycopg
from pathlib import Path

from reporting.excel_generator import ExcelGenerator
from resource_discovery.models import Resource, DiscoveryResult

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("CloudAuditor-DB-Report")

def get_database_config(profile: str, region: str, stack_name: str = 'cloudauditor-dev'):
    """Get database configuration from CloudFormation stack outputs"""
    session = boto3.Session(profile_name=profile, region_name=region)
    
    # Get stack outputs
    cfn = session.client('cloudformation')
    response = cfn.describe_stacks(StackName=stack_name)
    outputs = {o['OutputKey']: o['OutputValue'] for o in response['Stacks'][0]['Outputs']}
    
    db_endpoint = outputs['DatabaseEndpoint']
    secret_arn = outputs['DatabaseSecretArn']
    
    # Get credentials from Secrets Manager
    sm = session.client('secretsmanager')
    secret_response = sm.get_secret_value(SecretId=secret_arn)
    secret = json.loads(secret_response['SecretString'])
    
    return {
        'host': db_endpoint,
        'port': 5432,
        'dbname': secret.get('dbname', 'cloudauditor'),
        'user': secret['username'],
        'password': secret['password']
    }

def fetch_resources_from_database(db_config: dict) -> list:
    """Fetch all resources from the database"""
    logger.info(f"Connecting to database: {db_config['host']}")
    
    conn = psycopg.connect(**db_config)
    
    query = """
        SELECT 
            resource_id,
            resource_type,
            resource_arn,
            region,
            account_id,
            name,
            tags,
            properties,
            discovered_at,
            last_seen_at
        FROM resources
        ORDER BY account_id, region, resource_type, resource_id
    """
    
    resources = []
    with conn.cursor() as cur:
        cur.execute(query)
        rows = cur.fetchall()
        
        for row in rows:
            resource_dict = {
                'resource_id': row[0],
                'resource_type': row[1],
                'arn': row[2],
                'region': row[3],
                'account_id': row[4],
                'name': row[5],
                'tags': row[6] if row[6] else {},
                'configuration': row[7] if row[7] else {},
                'discovered_at': row[8].isoformat() if row[8] else None,
                'last_seen_at': row[9].isoformat() if row[9] else None,
            }
            
            # Convert to Resource object
            resource = Resource(
                arn=resource_dict.get('arn', ''),
                resource_type=resource_dict['resource_type'],
                region=resource_dict['region'],
                account_id=resource_dict['account_id'],
                name=resource_dict.get('name'),
                tags=resource_dict.get('tags', {}),
                configuration=resource_dict.get('configuration', {})
            )
            resources.append(resource)
    
    conn.close()
    logger.info(f"Fetched {len(resources)} resources from database")
    return resources

def main():
    parser = argparse.ArgumentParser(
        description="CloudAuditor - Generate Excel Report from Aurora Database"
    )
    
    # AWS Configuration
    parser.add_argument("--profile", default="cloudAuditor", help="AWS profile name")
    parser.add_argument("--region", default="us-east-1", help="AWS region")
    parser.add_argument("--stack-name", default="cloudauditor-dev", help="CloudFormation stack name")
    
    # Output args
    parser.add_argument("--format", choices=["json", "excel", "both"], default="excel", help="Output format")
    parser.add_argument("--output-dir", default="reports", help="Directory for reports")
    parser.add_argument("--filename", help="Custom filename for the report")
    
    args = parser.parse_args()
    
    try:
        # 1. Get database configuration
        logger.info("Retrieving database configuration from CloudFormation...")
        db_config = get_database_config(args.profile, args.region, args.stack_name)
        
        # 2. Fetch resources from database
        logger.info("Fetching resources from Aurora database...")
        resources = fetch_resources_from_database(db_config)
        
        if not resources:
            logger.warning("No resources found in database")
            return
        
        # 3. Create DiscoveryResult object
        result = DiscoveryResult(
            resources=resources,
            total_count=len(resources),
            duration_seconds=0,  # Not applicable for DB query
            errors=[]
        )
        
        # 4. Ensure output directory exists
        Path(args.output_dir).mkdir(parents=True, exist_ok=True)
        
        # 5. Generate Reports
        if args.format in ["json", "both"]:
            json_path = f"{args.output_dir}/{args.filename or 'database_export'}.json"
            with open(json_path, 'w') as f:
                json.dump([r.to_dict() for r in resources], f, indent=2, default=str)
            logger.info(f"✅ JSON report saved to {json_path}")
            
        if args.format in ["excel", "both"]:
            logger.info("Generating Excel Report...")
            generator = ExcelGenerator(output_dir=args.output_dir)
            report_path = generator.generate_report(result, filename=args.filename)
            if report_path:
                logger.info(f"✅ Excel report generated: {report_path}")
            else:
                logger.warning("Excel report generation skipped (no data).")
        
        logger.info(f"\n🎉 Report generation complete! {len(resources)} resources exported.")
        
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
