# Database Initialization Guide

## Overview

The `cloudauditor-db-init-dev` Lambda function initializes the CloudAuditor database schema. It supports both CloudFormation custom resource events (automatic during stack deployment) and manual invocations.

## Automatic Initialization

During stack deployment, the database schema is automatically initialized via a CloudFormation custom resource. No manual action is required.

## Manual Initialization

If you need to manually initialize or reset the database schema:

```bash
aws lambda invoke \
  --function-name cloudauditor-db-init-dev \
  --profile cloudAuditor \
  --region us-east-1 \
  output.json

# View results
cat output.json
```

**Expected Response:**
```json
{
  "statusCode": 200,
  "body": "{\"success\": true, \"message\": \"Created 3 tables\", \"tables\": [\"resources\", \"monitored_accounts\"]}"
}
```

## Database Schema

The initialization creates the following tables:

### `resources`
Stores discovered AWS resources.

```sql
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
```

### `monitored_accounts`
Tracks accounts for resource discovery.

```sql
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
```

## How It Works

The Lambda function:

1. **Detects Event Type**: Determines if invoked by CloudFormation or manually
2. **Retrieves Credentials**: Fetches database credentials from Secrets Manager
3. **Connects to Database**: Establishes connection to Aurora cluster
4. **Executes Schema**: Runs CREATE TABLE IF NOT EXISTS statements
5. **Creates Indexes**: Adds performance indexes
6. **Returns Status**: Reports success or failure

## Environment Variables

The Lambda requires these environment variables (automatically set by CloudFormation):

- `DB_SECRET_ARN` - Secrets Manager ARN for database credentials
- `DB_HOST` - Aurora cluster endpoint
- `DB_NAME` - Database name (default: `cloudauditor`)
- `AWS_REGION` - AWS region

## Troubleshooting

### Schema Already Exists

The initialization uses `CREATE TABLE IF NOT EXISTS`, so it's safe to run multiple times. Existing tables and data are preserved.

### Connection Timeout

The Lambda must run in the same VPC as the Aurora cluster. Verify:
- Lambda is in the correct VPC
- Security groups allow PostgreSQL traffic (port 5432)
- Subnets have NAT gateway access for Secrets Manager

### Permission Errors

Ensure the Lambda execution role has:
- `secretsmanager:GetSecretValue` for the database secret
- VPC execution permissions (`ec2:CreateNetworkInterface`, etc.)

## Manual Database Access

**Note:** The Aurora database is in a private VPC and not publicly accessible. You cannot connect directly from your laptop.

To query the database, use the query Lambda:
```bash
aws lambda invoke --function-name cloudauditor-query-dev \
  --payload '{"report_type":"summary"}' \
  --cli-binary-format raw-in-base64-out output.json
```

See [DATABASE_QUERIES.md](DATABASE_QUERIES.md) for more details.
