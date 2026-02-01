#!/usr/bin/python
import boto3
import json
import psycopg2

def process(thisiam, cur, accountid):
    """
        Usage:
            process_roles.process(IAM_Session, DB_Cursor, AWS_account_id)
    """
    roles = thisiam.list_roles()
    theseroles  = roles.get('Roles',[])
    print ("Processing " + str(len(theseroles)) + " Roles")
    # if the Prepared Statement exists, ignore the error
    try:
        cur.execute("PREPARE roleplan AS INSERT INTO aud_iam_roles "
                "(aws_account_id, role_json, assumerolepolicydocument, "
                "path, createdate, rolename, roleid, arn) "
                " VALUES ($1, $2, $3, $4, $5, $6, $7, $8)")
    except psycopg2.ProgrammingError as e:
       pass 

    for z in theseroles:
        cur.execute("EXECUTE roleplan (%s, %s, %s, %s, %s, %s, %s, %s) ",
                    (accountid, json.dumps(z, default=str), 
                    json.dumps(z['AssumeRolePolicyDocument'],default=str), 
                    z['Path'], z['CreateDate'], z['RoleName'], z['RoleId'], 
                    z['Arn']) )
    return
