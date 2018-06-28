from __future__ import print_function
import boto3
import json
import psycopg2
import sys, os

def connect_to_db():
    print ("Connecting to database")
    try:
        connstring = "dbname='" + os.environ['dbname'] + "' user='" + os.environ['dbuser'] + "' host='" + os.environ['dbhost'] + "' password='" + os.environ['dbpass'] + "'"
        conn = psycopg2.connect(connstring)
        cur = conn.cursor()
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
    except psycopg2.DatabaseError, exception:
        print (exception)
        sys.exit(1)
    print ("Database connection successful")
    return cur, conn;

def grab_roles(cur):
    try:
        cur.execute("SELECT aws_account_id, role_arn from aws_cross_account_roles")
    except psycopg2.DatabaseError, exception:
        print (exception)
        sys.exit(1)
    roles = cur.fetchall()
    return roles;

def process_remote(cur, account, arn, session, process_item):
    # need to accept AssumeRole session variable, grab the keys, and run a 
    #   data collection session
    # Update the cross account table and indicate we've used this account now and it's working
    try:
        thisiam = boto3.client('iam',
            aws_access_key_id=session['Credentials']['AccessKeyId'],
            aws_secret_access_key=session['Credentials']['SecretAccessKey'],
            aws_session_token=session['Credentials']['SessionToken'])
    except ClientError as e:
        print (e.response['Error']['Code'])
        try:
            cur.execute("UPDATE aws_cross_account_roles set working = %s, last_used_ts = %s "
                    "where role_arn = %s", (True, "now()", arn))
        except psycopg2.DatabaseError, exception:
            print (exception)
            sys.exit(1)
        sys.exit(1)
    print("Processing AWS Account ID: " + str(account))
    process_aws(thisiam, cur, account, process_item)
    return;

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
    return;

def process_local(cur, process_item):
    try:
        account = boto3.client('sts').get_caller_identity()['Account']
    except ClientError as e:
       print (e.response['Error']['Code'])
       sys.exit(1)
    print("Processing AWS Account ID: " + str(account))
    try:
        thisiam = boto3.client('iam')
    except ClientError as e:
       print (e.response['Error']['Code'])
       sys.exit(1)
    process_aws(thisiam, cur, account, process_item)
    return;

def lambda_handler(event, context):
    # setup -> all function calls will require database access
    cur = ""
    cur, conn = connect_to_db()
    # list of processes
    # create a list of processes: in the future collect this data from a DB
    process_list = [ "process_instances","process_roles","process_users","process_groups", "process_policies"]

    # generate rolearns and put them in the SNS topic
    print ("Process Accounts in Database")
    roles = grab_roles(cur)
    for proc in process_list:
        # now i need to iterate over the roles and place messages on SNS
        for account, rolearn  in roles:
            thislist = {"rolearn": rolearn, "account": account, "process_item": proc}
            # insert into SNS here
            print ("Message: {}".format(json.dumps(thislist)))
            snsclient = boto3.client('sns')
            topicarn = "arn:aws:sns:us-east-1:987569341137:iso-cloud-auditor"
            snsresponse = snsclient.publish(TopicArn=topicarn, Message=json.dumps(thislist))
            print ("Response: {}".format(snsresponse))
    cur.close()
    conn.close()
    return;
