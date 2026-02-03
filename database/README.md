# CloudAuditor Database

This directory contains database schema and utility scripts for CloudAuditor.

## Schema Files

### Modern Schema (Current)

- **[schema.sql](schema.sql)** - Current database schema for resource discovery
  - `resources` table - Stores all discovered AWS resources
  - `resource_relationships` table - Tracks resource dependencies
  - `discovery_runs` table - Execution history and metrics
  - Optimized indexes for fast queries

### Legacy Schema (Archive)

- **[legacy_schema.sql](legacy_schema.sql)** - Original Python 2 schema (archived)
  - IAM-specific tables (users, roles, policies, groups)
  - EC2 instances and tags
  - Not compatible with modern resource discovery engine

## Utility Scripts

- **[check_roles.sql](check_roles.sql)** - Verify database roles and permissions
- **[db_purge.sql](db_purge.sql)** - Clean up old data
- **[legacy_backup.sql](legacy_backup.sql)** - Legacy database backup structure

## Quick Start

### 1. Initialize Database

Run the schema using RDS Query Editor or psql:

```sql
-- Copy and paste contents of schema.sql into RDS Query Editor
-- OR use psql:
psql -h <db-endpoint> -U cloudauditor_admin -d cloudauditor -f database/schema.sql
```

### 2. Verify Tables

```sql
-- List all tables
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public';

-- Check resources table
SELECT COUNT(*) FROM resources;
```

### 3. Query Discovered Resources

```sql
-- View all resource types
SELECT resource_type, COUNT(*) as count
FROM resources
GROUP BY resource_type
ORDER BY count DESC;

-- View recent discoveries
SELECT resource_type, name, region, discovered_at
FROM resources
ORDER BY discovered_at DESC
LIMIT 20;

-- Search by tags
SELECT resource_type, name, tags
FROM resources
WHERE tags @> '{"Environment": "production"}';
```

## Database Connection

### Get Database Endpoint

```powershell
aws --profile cloudAuditor cloudformation describe-stacks `
  --stack-name cloudauditor-dev `
  --region us-east-1 `
  --query 'Stacks[0].Outputs[?OutputKey==`DatabaseEndpoint`].OutputValue' `
  --output text
```

### Get Database Credentials

Credentials are stored in AWS Secrets Manager:

```powershell
aws --profile cloudAuditor secretsmanager get-secret-value `
  --secret-id cloudauditor-dev-db-secret `
  --region us-east-1 `
  --query 'SecretString' `
  --output text
```

### Connect with psql

```bash
psql -h <endpoint> -U cloudauditor_admin -d cloudauditor
```

### Connect with RDS Query Editor

1. Go to **RDS Console** → **Query Editor**
2. Select your Aurora cluster
3. Choose **Database username and password**
4. Enter credentials from Secrets Manager
5. Database name: `cloudauditor`

## Schema Evolution

When updating the schema:

1. Create a new migration file: `database/migrations/YYYYMMDD_description.sql`
2. Test on dev environment first
3. Apply to staging, then production
4. Update this README with changes

## Backup and Restore

Aurora Serverless v2 automatically creates snapshots based on the backup retention period (configured in CloudFormation template).

### Manual Snapshot

```powershell
aws --profile cloudAuditor rds create-db-cluster-snapshot `
  --db-cluster-snapshot-identifier cloudauditor-manual-snapshot `
  --db-cluster-identifier <cluster-id> `
  --region us-east-1
```

### Restore from Snapshot

```powershell
aws --profile cloudAuditor rds restore-db-cluster-from-snapshot `
  --db-cluster-identifier cloudauditor-restored `
  --snapshot-identifier <snapshot-id> `
  --engine aurora-postgresql `
  --region us-east-1
```
