from bs4 import BeautifulSoup
import requests
import json
import boto3
import psycopg2
import os, sys

def process(cur):
    """
        Usage: process_cht_aws_users.process(DB Cursor)
    """
    url = 'https://chapi.cloudhealthtech.com/api/search.json?api_key=' + os.environ['api_key'] + '&name=AwsUser&include=account'
    s = requests.get(url)
    users = json.loads(s.text)
    # if the Prepared Statement exists, ignore the error
    try:
        cur.execute("PREPARE chtusersplan AS INSERT INTO cht_aws_users"
            "(aws_account_id, cht_user_json, insert_ts, "
            "arn, path, username, user_id, created_date, created_at, updated_at, mfa_status)"
            " VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)")
    except psycopg2.ProgrammingError as e:
        pass
    # {"user_id":"AIDAJGEFI66BYGSUTG2AI","name":"2359media","path":"/","arn":"arn:aws:iam::122997217079:user/2359media","created_date":"2016-01-26T07:52:33Z","created_at":"2016-01-26T08:08:22Z","updated_at":"2016-10-26T12:59:49Z","mfa_status":"Not Enabled"}
    print ("Processing " + str(len(users)) + " CloudHealth AWS Users")
    for z in users:
        if (z['mfa_status'] == "Not Enabled"):
            mfa_status = "false"
        if (z['mfa_status'] == "Unknown"):
            mfa_status = "false"
        if (z['mfa_status'] == "Enabled"):
            mfa_status = "true"
        cur.execute("EXECUTE chtusersplan (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ",
                    (z['account']['owner_id'],json.dumps(z, default=str), "now()", 
                    z['arn'], z['path'], z['name'], z['user_id'], z['created_date'],
                    z['created_at'], z['updated_at'], mfa_status))
    return;

def connect_to_db():
    try:
        conn = psycopg2.connect("dbname='isodb' user='isodbadmin' "
            "host='isodb.c20dabuuv4ab.us-east-1.rds.amazonaws.com'")
        cur = conn.cursor()
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
    except psycopg2.OperationalError as e:
        print ('Database Connection error\n{0}').format(e)
    return cur;

cur = connect_to_db()
process(cur)
