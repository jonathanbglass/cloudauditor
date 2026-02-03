# Database Query Guide

## Overview

CloudAuditor provides a Lambda function (`cloudauditor-query-dev`) that runs in the VPC and can be invoked remotely to query the Aurora database. This allows you to access discovery data from your laptop without needing direct VPC access.

## Quick Start

```powershell
# Summary report
aws lambda invoke \
  --function-name cloudauditor-query-dev \
  --profile cloudAuditor \
  --region us-east-1 \
  --payload '{"report_type":"summary"}' \
  --cli-binary-format raw-in-base64-out \
  output.json

# View results
cat output.json | jq '.body | fromjson'
```

## Available Report Types

### 1. Summary (`summary`)
Returns database statistics:
- Total resources
- Unique resource types
- Accounts with resources
- Monitored accounts
- Latest scan timestamp

**Example:**
```bash
aws lambda invoke --function-name cloudauditor-query-dev \
  --payload '{"report_type":"summary"}' \
  --cli-binary-format raw-in-base64-out output.json
```

### 2. Monitored Accounts (`accounts`)
Lists all monitored accounts with status, auto-discovery flag, and error messages.

**Example:**
```bash
aws lambda invoke --function-name cloudauditor-query-dev \
  --payload '{"report_type":"accounts"}' \
  --cli-binary-format raw-in-base64-out output.json
```

### 3. Resources by Type (`by_type`)
Groups resources by type with counts.

**Example:**
```bash
aws lambda invoke --function-name cloudauditor-query-dev \
  --payload '{"report_type":"by_type","limit":50}' \
  --cli-binary-format raw-in-base64-out output.json
```

### 4. Resources by Account (`by_account`)
Groups resources by account with counts and unique types.

**Example:**
```bash
aws lambda invoke --function-name cloudauditor-query-dev \
  --payload '{"report_type":"by_account"}' \
  --cli-binary-format raw-in-base64-out output.json
```

### 5. Resource List (`resources`)
Lists individual resources with details.

**Example:**
```bash
aws lambda invoke --function-name cloudauditor-query-dev \
  --payload '{"report_type":"resources","limit":100}' \
  --cli-binary-format raw-in-base64-out output.json
```

## Custom SQL Queries

You can execute custom SQL queries against the database:

```bash
aws lambda invoke --function-name cloudauditor-query-dev \
  --payload '{"query":"SELECT COUNT(*) FROM resources WHERE region='\''us-east-1'\''"}' \
  --cli-binary-format raw-in-base64-out output.json
```

**⚠️ Warning:** Use custom queries with caution. Only SELECT queries are recommended.

## Database Schema

### `resources` Table
- `id` - Auto-incrementing primary key
- `resource_id` - AWS resource identifier
- `resource_type` - Type (e.g., `ec2:instance`)
- `resource_arn` - AWS ARN
- `region` - AWS region
- `account_id` - AWS account ID
- `name` - Resource name
- `tags` - JSONB tags
- `properties` - JSONB configuration
- `discovered_at` - First discovery timestamp
- `last_seen_at` - Last seen timestamp

### `monitored_accounts` Table
- `account_id` - AWS account ID (primary key)
- `account_name` - Account name
- `role_arn` - Cross-account role ARN
- `status` - Status (`pending`, `active`, `error`, `disabled`)
- `auto_discovered` - Auto-discovered from Organizations
- `last_verification_at` - Last scan timestamp
- `last_error_message` - Error details
- `created_at` - Registration timestamp

## Response Format

All responses follow this format:

```json
{
  "statusCode": 200,
  "body": "{\"success\": true, \"report_type\": \"summary\", \"results\": {...}}"
}
```

The `body` field contains a JSON string that needs to be parsed.

## Error Handling

If the Lambda encounters an error, it returns:

```json
{
  "statusCode": 500,
  "body": "{\"success\": false, \"error\": \"error message\"}"
}
```

## Why Use Lambda for Queries?

The Aurora database is deployed in a private VPC and is not publicly accessible. The query Lambda:
- ✅ Runs in the same VPC as the database
- ✅ Can be invoked remotely via AWS CLI
- ✅ Requires only IAM permissions (no VPN/bastion needed)
- ✅ Provides secure, audited access

## Alternative: Local Discovery

For ad-hoc discovery without the database, use `main.py`:

```powershell
python main.py --accounts 123456789012 --format excel --output-dir ./reports
```

This discovers resources directly and saves to local JSON/Excel files.
