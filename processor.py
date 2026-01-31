from __future__ import print_function
import boto3
from botocore.exceptions import ClientError
import json
import process_instances
import process_roles
import process_groups
import process_users
import process_policies
import psycopg2
import sys, os

def connect_to_db():
    print ("Connecting to database")
    try:
        connstring = "dbname='" + os.environ['dbname'] + "' user='" + os.environ['dbuser'] + "' host='" + os.environ['dbhost'] + "' password='" + os.environ['dbpass'] + "'"
        conn = psycopg2.connect(connstring)
        cur = conn.cursor()
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
    except psycopg2.DatabaseError as exception:
        print (exception)
        sys.exit(1)
    print ("Database connection successful")
    return cur, conn

def process_remote(cur, account, arn, session, process_item):
    # need to accept AssumeRole session variable, grab the keys, and run a 
    #   data collection session
    # Update the cross account table and indicate we've used this account now and it's working
    try:
        cur.execute("UPDATE aws_cross_account_roles set working = %s, last_used_ts = %s "
                "where role_arn = %s", (True, "now()", arn))
    except psycopg2.DatabaseError as exception:
        print (exception)
        sys.exit(1)
    try:
        thisiam = boto3.client('iam',
            aws_access_key_id=session['Credentials']['AccessKeyId'],
            aws_secret_access_key=session['Credentials']['SecretAccessKey'],
            aws_session_token=session['Credentials']['SessionToken'])
    except ClientError as e:
       print (e.response['Error']['Code'])
       sys.exit(1)
    print("Processing AWS Account ID: " + str(account))
    process_aws(thisiam, cur, account, process_item)
    return

def process_aws(thisiam, cur, account, process_item):
    if (process_item == "process_instances"):
        process_instances.process(thisiam, cur, account)
    if (process_item == "process_roles"):
        process_roles.process(thisiam, cur, account)
    if (process_item == "process_users"):
        process_users.process(thisiam, cur, account)
    if (process_item == "process_groups"):
        process_groups.process(thisiam, cur, account)
    if (process_item == "process_policies"):
        process_policies.process(thisiam, cur, account)
    return

def process_local(cur, process_item):
    try:
        account = boto3.client('sts').get_caller_identity()['Account']
    except ClientError as e:
       print (e.response['Error']['Code'])
       sys.exit(1)
    print("Processing local AWS Account ID: " + str(account))
    try:
        thisiam = boto3.client('iam')
    except ClientError as e:
       print (e.response['Error']['Code'])
       sys.exit(1)
    process_aws(thisiam, cur, account, process_item)
    return

def lambda_handler(event, context):
    # setup -> all function calls will require database access
    cur = ""
    cur, conn = connect_to_db()
    # list of processes
    # create a list of processes: in the future collect this data from a DB
    process_list = [ "process_instances","process_roles","process_users","process_groups", "process_policies"]
    # event received -> process it like normal
    # { 'rolearn': arn,
    #   'account': account,
    #   'process_item': item_to_process
    # }
    #print("Received event: " + json.dumps(event, indent=2))
    # "Message" : "
    #   {
    #       "rolearn": "arn:aws:iam::835625390401:role/GTO-ISO-Audit", 
    #       "process_item": "process_users", 
    #       "account": 835625390401}",
    message = json.loads(event['Records'][0]['Sns']['Message'])
    account = message['account']
    arn = message['rolearn']
    process_item = message['process_item']
    localaccount = boto3.client('sts').get_caller_identity()['Account']
    print ("Debug: Local -> " + str(localaccount) + ", Passed -> " + str(account))
    if (arn == "local"):
        process_local(cur, account, arn, session, process_item)
    else:
        client = boto3.client('sts')
        try:
            session = client.assume_role(RoleArn=arn, RoleSessionName='Session' + str(account))
        except ClientError as e:
            print("AssumeRole Failure:", account, arn, str(e))
            # update the cross-account-roles table and mark this role as broken
            try:
                cur.execute("UPDATE aws_cross_account_roles set working = %s "
                                        "where role_arn = %s", (False, arn))
            except psycopg2.DatabaseError as exception:
                print (exception)
            # return failure?
            sys.exit(1) 
        process_remote(cur, account, arn, session, process_item)
    cur.close()
    conn.close()
    return
