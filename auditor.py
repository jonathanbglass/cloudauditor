#!/usr/bin/python
import argparse
import boto3
import process_instances
import process_roles
import process_groups
import process_users
import process_policies
import psycopg2


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--audit",
                        help="audit [all (default), local, remote] Account(s)")
    args = parser.parse_args()
    if args.audit == "local":
        print("Auditing local")
        audit = "local"
    elif args.audit == "remote":
        print("Auditing remote, skipping local")
        audit = "remote"
    else:
        print("Auditing all")
        audit = "all"
    return audit


def connect_to_db():
    try:
        conn = psycopg2.connect("dbname='isodb' user='isodbadmin' "
                    "host='isodb.c20dabuuv4ab.us-east-1.rds.amazonaws.com'")
        cur = conn.cursor()
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
    except psycopg2.OperationalError as e:
        print('Database Connection error\n{0}').format(e)
    return cur


def grab_roles(cur):
    cur.execute("SELECT aws_account_id, role_arn from aws_cross_account_roles")
    roles = cur.fetchall()
    return roles


def process_remote(cur, account, arn, session):
    # need to accept AssumeRole session variable, grab the keys, and run a
    #   data collection session
    # Update the cross account table and indicate we've used this account now and it's working
    cur.execute("UPDATE aws_cross_account_roles set working = %s, "
                "last_used_ts = %s "
                "where role_arn = %s", (True, "now()", arn))
    thisiam = boto3.client('iam',
        aws_access_key_id=session['Credentials']['AccessKeyId'],
        aws_secret_access_key=session['Credentials']['SecretAccessKey'],
        aws_session_token=session['Credentials']['SessionToken'])

    print("Processing AWS Account ID: " + str(account))
    process_instances.process(thisiam, cur, account)
    process_roles.process(thisiam, cur, account)
    process_users.process(thisiam, cur, account)
    process_groups.process(thisiam, cur, account)
    process_policies.process(thisiam, cur, account)
    return


def main():
    # main code execution
    audit = parse_arguments()

    # Connect to database
    # conn is a global variable and will get used all over the place
    conn = psycopg2.connect("dbname='isodb' user='isodbadmin' host='isodb.c20dabuuv4ab.us-east-1.rds.amazonaws.com'")
    cur = connect_to_db()

    if ((audit == "local") or (audit == "all")):
        # start with the local / default account
        accountid = boto3.client('sts').get_caller_identity()['Account']
        print("Processing AWS Account ID: " + str(accountid))
        thisiam = boto3.client('iam')
        process_instances.process(thisiam, cur, accountid)
        process_roles.process(thisiam, cur, accountid)
        process_users.process(thisiam, cur, accountid)
        process_groups.process(thisiam, cur, accountid)
        process_policies.process(thisiam, cur, accountid)

    if ((audit == "remote") or (audit == "all")):
        # process accounts in database
        roles = grab_roles(cur)
        for account, arn  in roles:
            client = boto3.client('sts')
            try:
                session = client.assume_role(RoleArn=arn, RoleSessionName='Session' + str(account))
            except:
                print("Failure ", account, arn)
                sql = "UPDATE aws_cross_account_roles set working = false where role_arn = '" + arn + "';"
                cur.execute(sql)
                continue
            process_remote(cur, account, arn, session)

    # clean up
    cur.close()
    conn.close()


main()
