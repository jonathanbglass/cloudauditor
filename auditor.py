#!/usr/bin/env python3
"""
AWS Cloud Auditor - Main Script
Audits AWS accounts for IAM users, roles, groups, policies, and EC2 instances.
"""
import argparse
import logging
import os
from typing import Optional, Tuple, List

import boto3
from botocore.exceptions import ClientError
import psycopg2
from psycopg2.extensions import cursor as Cursor

import process_instances
import process_roles
import process_groups
import process_users
import process_policies

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def parse_arguments() -> str:
    """Parse command line arguments for audit scope."""
    parser = argparse.ArgumentParser(
        description='Audit AWS accounts for IAM and EC2 resources'
    )
    parser.add_argument(
        "-a", "--audit",
        choices=['local', 'remote', 'all'],
        default='all',
        help="Audit scope: local (current account), remote (cross-account), or all"
    )
    args = parser.parse_args()
    
    logger.info(f"Audit scope: {args.audit}")
    return args.audit


def connect_to_db() -> Optional[Cursor]:
    """
    Connect to PostgreSQL database.
    
    Returns:
        Database cursor if successful, None otherwise
    """
    db_config = {
        'dbname': os.getenv('DB_NAME', 'isodb'),
        'user': os.getenv('DB_USER', 'isodbadmin'),
        'host': os.getenv('DB_HOST', 'isodb.c20dabuuv4ab.us-east-1.rds.amazonaws.com'),
        'password': os.getenv('DB_PASSWORD', '')
    }
    
    try:
        conn = psycopg2.connect(**db_config)
        cur = conn.cursor()
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
        logger.info("Database connection successful")
        return cur
    except psycopg2.OperationalError as e:
        logger.error(f"Database connection error: {e}")
        return None


def grab_roles(cur: Cursor) -> List[Tuple[str, str]]:
    """
    Retrieve cross-account roles from database.
    
    Args:
        cur: Database cursor
        
    Returns:
        List of (account_id, role_arn) tuples
    """
    cur.execute("SELECT aws_account_id, role_arn FROM aws_cross_account_roles")
    roles = cur.fetchall()
    logger.info(f"Retrieved {len(roles)} cross-account roles")
    return roles


def process_remote(cur: Cursor, account: str, arn: str, session: dict) -> None:
    """
    Process a remote AWS account using assumed role credentials.
    
    Args:
        cur: Database cursor
        account: AWS account ID
        arn: Role ARN to assume
        session: STS session credentials
    """
    # Update the cross account table
    cur.execute(
        "UPDATE aws_cross_account_roles SET working = %s, last_used_ts = %s WHERE role_arn = %s",
        (True, "now()", arn)
    )
    
    thisiam = boto3.client(
        'iam',
        aws_access_key_id=session['Credentials']['AccessKeyId'],
        aws_secret_access_key=session['Credentials']['SecretAccessKey'],
        aws_session_token=session['Credentials']['SessionToken']
    )

    logger.info(f"Processing AWS Account ID: {account}")
    process_instances.process(thisiam, cur, account)
    process_roles.process(thisiam, cur, account)
    process_users.process(thisiam, cur, account)
    process_groups.process(thisiam, cur, account)
    process_policies.process(thisiam, cur, account)


def main() -> None:
    """Main execution function."""
    audit = parse_arguments()

    # Connect to database
    db_config = {
        'dbname': os.getenv('DB_NAME', 'isodb'),
        'user': os.getenv('DB_USER', 'isodbadmin'),
        'host': os.getenv('DB_HOST', 'isodb.c20dabuuv4ab.us-east-1.rds.amazonaws.com'),
        'password': os.getenv('DB_PASSWORD', '')
    }
    
    conn = psycopg2.connect(**db_config)
    cur = connect_to_db()
    
    if cur is None:
        logger.error("Failed to connect to database. Exiting.")
        return

    # Process local account
    if audit in ("local", "all"):
        try:
            accountid = boto3.client('sts').get_caller_identity()['Account']
            logger.info(f"Processing local AWS Account ID: {accountid}")
            thisiam = boto3.client('iam')
            process_instances.process(thisiam, cur, accountid)
            process_roles.process(thisiam, cur, accountid)
            process_users.process(thisiam, cur, accountid)
            process_groups.process(thisiam, cur, accountid)
            process_policies.process(thisiam, cur, accountid)
        except ClientError as e:
            logger.error(f"Error processing local account: {e}")

    # Process remote accounts
    if audit in ("remote", "all"):
        roles = grab_roles(cur)
        for account, arn in roles:
            client = boto3.client('sts')
            try:
                session = client.assume_role(
                    RoleArn=arn,
                    RoleSessionName=f'Session{account}'
                )
                process_remote(cur, account, arn, session)
            except ClientError as e:
                logger.error(f"AssumeRole failure for account {account}, ARN {arn}: {e}")
                sql = f"UPDATE aws_cross_account_roles SET working = false WHERE role_arn = '{arn}'"
                cur.execute(sql)
                continue

    # Clean up
    cur.close()
    conn.close()
    logger.info("Audit complete")


if __name__ == "__main__":
    main()
