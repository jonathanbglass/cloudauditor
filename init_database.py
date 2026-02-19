#!/usr/bin/env python3
"""
Manually initialize CloudAuditor database schema
"""
import boto3
import json
import psycopg

def main():
    profile = 'cloudAuditor'
    region = 'us-east-1'
    
    session = boto3.Session(profile_name=profile, region_name=region)
    
    # Get database config from CloudFormation outputs
    cfn = session.client('cloudformation')
    response = cfn.describe_stacks(StackName='cloudauditor-dev')
    outputs = {o['OutputKey']: o['OutputValue'] for o in response['Stacks'][0]['Outputs']}
    
    db_endpoint = outputs['DatabaseEndpoint']
    secret_arn = outputs['DatabaseSecretArn']
    
    # Get credentials from Secrets Manager
    sm = session.client('secretsmanager')
    secret_response = sm.get_secret_value(SecretId=secret_arn)
    secret = json.loads(secret_response['SecretString'])
    
    print(f"Connecting to {db_endpoint}...")
    
    # Connect to database
    conn = psycopg.connect(
        host=db_endpoint,
        port=5432,
        dbname=secret.get('dbname', 'cloudauditor'),
        user=secret['username'],
        password=secret['password']
    )
    
    print("Creating database schema...")
    
    schema_sql = """
    -- CloudAuditor Database Schema
    CREATE TABLE IF NOT EXISTS public.resources (
        id BIGSERIAL PRIMARY KEY,
        resource_id TEXT NOT NULL,
        resource_type TEXT NOT NULL,
        resource_arn TEXT,
        region TEXT NOT NULL,
        account_id TEXT NOT NULL,
        name TEXT,
        tags JSONB,
        properties JSONB,
        discovered_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        last_seen_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        UNIQUE (resource_id, resource_type, region, account_id)
    );

    CREATE INDEX IF NOT EXISTS idx_resources_type ON public.resources(resource_type);
    CREATE INDEX IF NOT EXISTS idx_resources_account ON public.resources(account_id);
    CREATE INDEX IF NOT EXISTS idx_resources_region ON public.resources(region);
    CREATE INDEX IF NOT EXISTS idx_resources_discovered ON public.resources(discovered_at);

    CREATE TABLE IF NOT EXISTS public.monitored_accounts (
        account_id TEXT PRIMARY KEY,
        account_name TEXT,
        role_arn TEXT NOT NULL,
        status TEXT DEFAULT 'pending',
        auto_discovered BOOLEAN DEFAULT FALSE,
        last_verification_at TIMESTAMP WITH TIME ZONE,
        last_error_message TEXT,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );

    CREATE INDEX IF NOT EXISTS idx_monitored_accounts_status ON public.monitored_accounts(status);
    """
    
    with conn.cursor() as cur:
        cur.execute(schema_sql)
    
    conn.commit()
    conn.close()
    
    print("✅ Database schema initialized successfully!")
    print("\nTables created:")
    print("  - resources")
    print("  - monitored_accounts")

if __name__ == '__main__':
    main()
