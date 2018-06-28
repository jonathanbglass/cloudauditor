#!/usr/bin/python
import boto3
import json
import psycopg2

def process(thisiam, cur, accountid):
    """
        Usage: process_groups.process(IAM Session, DB Cursor, AWS ACcount #)
    """
    groups = thisiam.list_groups()
    thesegroups = groups.get('Groups',[])
    print ("Processing " + str(len(thesegroups)) + " Groups")
    # if the Prepared Statement exists, ignore the error
    try:
        cur.execute("PREPARE groupplan AS INSERT INTO aud_iam_groups "
            "(aws_account_id, group_json, "
            "path, createdate, groupname, groupid, arn) "
            " VALUES ($1, $2, $3, $4, $5, $6, $7)")
    except psycopg2.ProgrammingError as e:
        pass

    for z in thesegroups:
        cur.execute("EXECUTE groupplan (%s, %s, %s, %s, %s, %s, %s) ",
                    (accountid, json.dumps(z, default=str), z['Path'],
                    z['CreateDate'], z['GroupName'], z['GroupId'],
                    z['Arn']))
    return;
