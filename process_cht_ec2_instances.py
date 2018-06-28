from bs4 import BeautifulSoup
import requests
import json
import boto3
import psycopg2
import os, sys

def process(cur):
    """
        Usage: process_cht_aws_instances.process(DB Cursor)
    """
    url = 'https://chapi.cloudhealthtech.com/api/search.json?api_key=' + os.environ['api_key'] + '&name=AwsInstance&include=account'
    s = requests.get(url)
    instances = json.loads(s.text)
    # if the Prepared Statement exists, ignore the error
    try:
        cur.execute("PREPARE chtinstancesplan AS INSERT INTO cht_instances"
            "(aws_account_id, insert_ts, instance_id,dns, groups, instance_ip, "
            "launch_date, launched_by, instance_name, owner_email, private_dns,"
            "private_ip, instance_tags, updated_at, vpc_id )"
            " VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13,"
            "$14, $15)")
    except psycopg2.ProgrammingError as e:
        pass
    print ("Processing " + str(len(instances)) + " CloudHealth EC2 Instances")
    for z in instances:
        cur.execute("EXECUTE chtinstancesplan (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ",
                    (z['account']['owner_id'], "now()", z['instance_id'], z['dns'],
                    z['groups'], z['ip'], z['launch_date'],
                    z['launched_by'], z['name'], z['owner_email'],
                    z['private_dns'], z['private_ip'], z['tags'], z['updated_at'],
                    z['vpc_id']))
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
