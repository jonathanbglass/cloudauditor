#!/usr/bin/python
import boto3
import json
import psycopg2

def process(thisiam, cur, accountid):
    """
        Usage: process_users.process(IAM Session, DB Cursor, AWS Account #)
    """
    users = thisiam.list_users()
    theseusers =  users.get('Users',[])
    print ("Processing " + str(len(theseusers)) + " Users")
    # if the prepared statement exists, ignore the error
    try:
        cur.execute("PREPARE userplan AS INSERT INTO aud_iam_users "
            "(aws_account_id, user_json, passwordlastused, "
            "path, createdate, username, userid, arn) "
            " VALUES ($1, $2, $3, $4, $5, $6, $7, $8)")
    except psycopg2.ProgrammingError as e:
        pass 

    for z in theseusers:
        if len(z) == 6:
            PasswordLastUsedTS = z['PasswordLastUsed']
        else:
            PasswordLastUsedTS = None
        cur.execute("EXECUTE userplan (%s, %s, %s, %s, %s, %s, %s, %s)",
                    (accountid, json.dumps(z, default=str), PasswordLastUsedTS,
                    z['Path'], z['CreateDate'], z['UserName'], z['UserId'],
                    z['Arn']))
    return;
