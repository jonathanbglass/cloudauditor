#!/usr/bin/python
import boto3
import json
import psycopg2

def process(thisiam, cur, accountid):
    # need a list of regions
    ec2client = boto3.client('ec2', region_name='us-east-1')
    regions = [region['RegionName'] for region in ec2client.describe_regions()['Regions']]
    for k in regions:
        ec2client2 = boto3.client('ec2', region_name=k)
        instances = ec2client2.describe_instances()
        c = len(instances['Reservations'])
        if c > 0:
            print("Processing " + str(c) + " Instances")
            i = instances['Reservations']
            # if prepared statement exists, ignore the error
            try:
                cur.execute("PREPARE instancesplan AS INSERT INTO aud_aws_instances"
                            "(aws_account_id, insert_ts, instance_json, instanceid)  "
                            " VALUES ($1, $2, $3, $4)")
            except psycopg2.ProgrammingError as e:
                pass 

            for j in i:
                for l in j['Instances']:
                    cur.execute("EXECUTE instancesplan (%s, %s, %s, %s)",
                            (accountid, "now()", json.dumps(l, default=str), l['InstanceId']))

        tags = ec2client2.describe_tags()['Tags']
        if len(tags) > 0:
            print("Processing " + str(len(tags)) + " Instance Tags")
            # if prepared statement exists, ignore the error
            try:
                cur.execute("PREPARE tagplan AS INSERT INTO aud_tags"
                            "(aws_account_id, insert_ts, resourcetype, resourceid, tagkey, tagvalue)  "
                            " VALUES ($1, $2, $3, $4, $5, $6)")
            except psycopg2.ProgrammingError as e:
                pass 

            for z in tags:
                try:
                        cur.execute("EXECUTE tagplan (%s, %s, %s, %s, %s, %s)", (accountid, "now()", z['ResourceType'], z['ResourceId'], z['Key'], z['Value']))
                except:
                    print(z)
                    pass
    return;
