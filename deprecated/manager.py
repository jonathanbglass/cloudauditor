"""
AWS Lambda Manager Function
Generates SNS messages for each account and process type to trigger auditing.
"""
import json
import logging
import os
import sys
from typing import Tuple, List, Optional

import boto3
from botocore.exceptions import ClientError
import psycopg2
from psycopg2.extensions import cursor as Cursor, connection as Connection

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def connect_to_db() -> Tuple[Optional[Cursor], Optional[Connection]]:
    """
    Connect to PostgreSQL database using environment variables.
    
    Returns:
        Tuple of (cursor, connection) or (None, None) on failure
    """
    logger.info("Connecting to database")
    try:
        connstring = (
            f"dbname='{os.environ['dbname']}' "
            f"user='{os.environ['dbuser']}' "
            f"host='{os.environ['dbhost']}' "
            f"password='{os.environ['dbpass']}'"
        )
        conn = psycopg2.connect(connstring)
        cur = conn.cursor()
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
        logger.info("Database connection successful")
        return cur, conn
    except psycopg2.DatabaseError as exception:
        logger.error(f"Database error: {exception}")
        sys.exit(1)


def grab_roles(cur: Cursor) -> List[Tuple[str, str]]:
    """
    Retrieve cross-account roles from database.
    
    Args:
        cur: Database cursor
        
    Returns:
        List of (account_id, role_arn) tuples
    """
    try:
        cur.execute("SELECT aws_account_id, role_arn FROM aws_cross_account_roles")
        roles = cur.fetchall()
        logger.info(f"Retrieved {len(roles)} cross-account roles")
        return roles
    except psycopg2.DatabaseError as exception:
        logger.error(f"Database error: {exception}")
        sys.exit(1)


def process_remote(cur: Cursor, account: str, arn: str, session: dict, process_item: str) -> None:
    """
    Process a remote AWS account using assumed role credentials.
    
    Args:
        cur: Database cursor
        account: AWS account ID
        arn: Role ARN to assume
        session: STS session credentials
        process_item: Type of resource to process
    """
    try:
        thisiam = boto3.client(
            'iam',
            aws_access_key_id=session['Credentials']['AccessKeyId'],
            aws_secret_access_key=session['Credentials']['SecretAccessKey'],
            aws_session_token=session['Credentials']['SessionToken']
        )
    except ClientError as e:
        logger.error(f"IAM client error: {e.response['Error']['Code']}")
        try:
            cur.execute(
                "UPDATE aws_cross_account_roles SET working = %s, last_used_ts = %s WHERE role_arn = %s",
                (True, "now()", arn)
            )
        except psycopg2.DatabaseError as exception:
            logger.error(f"Database error: {exception}")
            sys.exit(1)
        sys.exit(1)
    
    logger.info(f"Processing AWS Account ID: {account}")
    process_aws(thisiam, cur, account, process_item)


def process_aws(thisiam, cur: Cursor, account: str, process_item: str) -> None:
    """
    Process AWS resources based on process_item type.
    
    Args:
        thisiam: IAM client
        cur: Database cursor
        account: AWS account ID
        process_item: Type of resource to process
    """
    # Import process modules dynamically to avoid circular dependencies
    if process_item == "process_instances":
        import process_instances
        process_instances.process(thisiam, cur, account)
    elif process_item == "process_roles":
        import process_roles
        process_roles.process(thisiam, cur, account)
    elif process_item == "process_users":
        import process_users
        process_users.process(thisiam, cur, account)
    elif process_item == "process_groups":
        import process_groups
        process_groups.process(thisiam, cur, account)
    elif process_item == "process_policies":
        import process_policies
        process_policies.process(thisiam, cur, account)


def process_local(cur: Cursor, process_item: str) -> None:
    """
    Process local AWS account resources.
    
    Args:
        cur: Database cursor
        process_item: Type of resource to process
    """
    try:
        account = boto3.client('sts').get_caller_identity()['Account']
        logger.info(f"Processing local AWS Account ID: {account}")
    except ClientError as e:
        logger.error(f"STS error: {e.response['Error']['Code']}")
        sys.exit(1)
    
    try:
        thisiam = boto3.client('iam')
    except ClientError as e:
        logger.error(f"IAM client error: {e.response['Error']['Code']}")
        sys.exit(1)
    
    process_aws(thisiam, cur, account, process_item)


def lambda_handler(event: dict, context) -> None:
    """
    Lambda handler function to generate SNS messages for account auditing.
    
    Args:
        event: Lambda event data
        context: Lambda context object
    """
    # Setup - connect to database
    cur, conn = connect_to_db()
    
    # List of processes
    process_list = [
        "process_instances",
        "process_roles",
        "process_users",
        "process_groups",
        "process_policies"
    ]

    # Generate role ARNs and put them in the SNS topic
    logger.info("Processing accounts in database")
    roles = grab_roles(cur)
    
    sns_topic_arn = os.getenv(
        'SNS_TOPIC_ARN',
        'arn:aws:sns:us-east-1:987569341137:iso-cloud-auditor'
    )
    
    for proc in process_list:
        # Iterate over roles and place messages on SNS
        for account, rolearn in roles:
            message = {
                "rolearn": rolearn,
                "account": account,
                "process_item": proc
            }
            
            logger.info(f"Publishing message: {json.dumps(message)}")
            
            try:
                snsclient = boto3.client('sns')
                snsresponse = snsclient.publish(
                    TopicArn=sns_topic_arn,
                    Message=json.dumps(message)
                )
                logger.info(f"SNS Response: {snsresponse}")
            except ClientError as e:
                logger.error(f"SNS publish error: {e}")
    
    cur.close()
    conn.close()
    logger.info("Manager function complete")
