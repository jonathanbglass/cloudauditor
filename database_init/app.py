"""
Database Initialization Lambda Function
Automatically creates database schema when CloudFormation stack is deployed
"""
import json
import os
import boto3
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import urllib3

http = urllib3.PoolManager()

def get_secret(secret_name, region):
    """Retrieve database credentials from Secrets Manager"""
    client = boto3.client('secretsmanager', region_name=region)
    response = client.get_secret_value(SecretId=secret_name)
    return json.loads(response['SecretString'])

def send_response(event, context, response_status, response_data):
    """Send response to CloudFormation"""
    response_body = json.dumps({
        'Status': response_status,
        'Reason': f'See CloudWatch Log Stream: {context.log_stream_name}',
        'PhysicalResourceId': context.log_stream_name,
        'StackId': event['StackId'],
        'RequestId': event['RequestId'],
        'LogicalResourceId': event['LogicalResourceId'],
        'Data': response_data
    })
    
    headers = {'content-type': '', 'content-length': str(len(response_body))}
    
    try:
        http.request('PUT', event['ResponseURL'], body=response_body, headers=headers)
    except Exception as e:
        print(f"Failed to send response: {e}")

def initialize_database(db_host, db_name, db_user, db_password, db_port=5432):
    """Initialize database schema"""
    print(f"Connecting to database: {db_host}:{db_port}/{db_name}")
    
    # Read schema file
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
    properties JSONB NOT NULL,
    discovered_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    last_seen_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    UNIQUE(resource_id, resource_type, region, account_id)
);

CREATE INDEX IF NOT EXISTS idx_resources_type ON public.resources(resource_type);
CREATE INDEX IF NOT EXISTS idx_resources_region ON public.resources(region);
CREATE INDEX IF NOT EXISTS idx_resources_account ON public.resources(account_id);
CREATE INDEX IF NOT EXISTS idx_resources_discovered ON public.resources(discovered_at DESC);
CREATE INDEX IF NOT EXISTS idx_resources_arn ON public.resources(resource_arn);
CREATE INDEX IF NOT EXISTS idx_resources_tags ON public.resources USING GIN (tags);

CREATE TABLE IF NOT EXISTS public.resource_relationships (
    id BIGSERIAL PRIMARY KEY,
    source_resource_id BIGINT NOT NULL REFERENCES public.resources(id) ON DELETE CASCADE,
    target_resource_id BIGINT NOT NULL REFERENCES public.resources(id) ON DELETE CASCADE,
    relationship_type TEXT NOT NULL,
    discovered_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    UNIQUE(source_resource_id, target_resource_id, relationship_type)
);

CREATE INDEX IF NOT EXISTS idx_relationships_source ON public.resource_relationships(source_resource_id);
CREATE INDEX IF NOT EXISTS idx_relationships_target ON public.resource_relationships(target_resource_id);

CREATE TABLE IF NOT EXISTS public.discovery_runs (
    id BIGSERIAL PRIMARY KEY,
    run_id TEXT NOT NULL UNIQUE,
    started_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    status TEXT NOT NULL DEFAULT 'running',
    total_resources INTEGER DEFAULT 0,
    resource_types INTEGER DEFAULT 0,
    errors JSONB,
    duration_seconds DECIMAL(10,2)
);

CREATE INDEX IF NOT EXISTS idx_discovery_runs_started ON public.discovery_runs(started_at DESC);
CREATE INDEX IF NOT EXISTS idx_discovery_runs_status ON public.discovery_runs(status);
"""
    
    try:
        # Connect to database
        conn = psycopg2.connect(
            host=db_host,
            port=db_port,
            database=db_name,
            user=db_user,
            password=db_password,
            connect_timeout=10
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        
        # Execute schema
        cursor = conn.cursor()
        cursor.execute(schema_sql)
        
        # Verify tables were created
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('resources', 'resource_relationships', 'discovery_runs')
        """)
        tables = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        print(f"Schema initialized successfully. Created tables: {tables}")
        return True, f"Created {len(tables)} tables"
        
    except Exception as e:
        print(f"Error initializing database: {e}")
        raise

def lambda_handler(event, context):
    """
    CloudFormation Custom Resource handler for database initialization
    """
    print(f"Event: {json.dumps(event)}")
    
    try:
        request_type = event['RequestType']
        
        # Only initialize on Create, skip on Update/Delete
        if request_type == 'Create':
            # Get database connection info from environment
            secret_arn = os.environ['DB_SECRET_ARN']
            db_host = os.environ['DB_HOST']
            db_name = os.environ['DB_NAME']
            region = os.environ['AWS_REGION']
            
            # Get credentials from Secrets Manager
            secret = get_secret(secret_arn, region)
            db_user = secret['username']
            db_password = secret['password']
            
            # Initialize database
            success, message = initialize_database(db_host, db_name, db_user, db_password)
            
            send_response(event, context, 'SUCCESS', {
                'Message': message,
                'Tables': 'resources, resource_relationships, discovery_runs'
            })
        else:
            # For Update/Delete, just return success
            send_response(event, context, 'SUCCESS', {
                'Message': f'{request_type} - No action needed'
            })
            
    except Exception as e:
        print(f"Error: {e}")
        send_response(event, context, 'FAILED', {
            'Message': str(e)
        })
