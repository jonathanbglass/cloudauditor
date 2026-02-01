#!/usr/bin/python
import boto3
import json
import psycopg2

def process(thisiam, cur, accountid):
    policies  = thisiam.list_policies(OnlyAttached=True)
    thesepols = policies.get('Policies',[])
    print ("Processing " + str(len(thesepols)) + " Policies")
    # if prepared statement exists, ignore the error
    try:
        cur.execute("PREPARE policyplan AS INSERT INTO aud_iam_policies "
           "(aws_account_id, policy_json, defaultversionid, isattachable, "
           "attachmentcount, updatedate, path, createdate, "
           "policyname, policyid, arn, policy_document, "
           "policygroups, policyusers, policyroles) "
           " VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15)")
    except psycopg2.ProgrammingError as e:
        pass

    for z in thesepols:
        # get policy document
        policyversion = thisiam.get_policy_version(PolicyArn=z['Arn'], VersionId=z['DefaultVersionId'])
        # get attached entities
        ae = thisiam.list_entities_for_policy(PolicyArn=z['Arn'])
        # insert policy metadata into database
        cur.execute("EXECUTE policyplan "
                    "(%s, %s, %s, %s, %s, %s, %s, %s, "
                    "%s, %s, %s, %s, %s, %s, %s)",
                    (accountid, json.dumps(z, default=str),
                    z['DefaultVersionId'], z['IsAttachable'],
                    z['AttachmentCount'], z['UpdateDate'],
                    z['Path'], z['CreateDate'],
                    z['PolicyName'], z['PolicyId'],
                    z['Arn'],
                    json.dumps(policyversion['PolicyVersion']['Document'], default=str),
                    json.dumps(ae['PolicyGroups'], default=str),
                    json.dumps(ae['PolicyUsers'], default=str),
                    json.dumps(ae['PolicyRoles'], default=str)))
    return
