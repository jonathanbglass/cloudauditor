# Aurora Serverless v2 Database Setup

This document explains the automated database infrastructure created by the SAM template.

## What Gets Created

### Aurora Serverless v2 PostgreSQL Cluster
- **Engine**: PostgreSQL 15.8
- **Scaling**: 0.5 - 2 ACUs (configurable)
- **Encryption**: Enabled (at rest)
- **Backups**: 7-day retention (configurable)
- **IAM Authentication**: Enabled

### Networking
- **VPC**: 10.0.0.0/16 (created if not provided)
- **Private Subnets**: 2 subnets in different AZs for Aurora
- **Public Subnet**: For NAT Gateway
- **NAT Gateway**: Allows Lambda internet access
- **Security Groups**: 
  - Lambda SG: Outbound only
  - Aurora SG: Inbound from Lambda on port 5432

### Credentials Management
- **Secrets Manager**: Stores database credentials
- **IAM Database Authentication**: Enabled for Lambda functions
- **Master Password**: Provided as parameter (stored in GitHub Secrets)

## Configuration Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `DatabaseName` | `cloudauditor` | PostgreSQL database name |
| `DatabaseMasterUsername` | `cloudauditor_admin` | Master username |
| `DatabaseMasterPassword` | *(required)* | Master password (min 8 chars) |
| `AuroraMinCapacity` | `0.5` | Minimum ACUs (0.5-10) |
| `AuroraMaxCapacity` | `2` | Maximum ACUs (0.5-128) |
| `EnableDatabaseBackups` | `true` | Enable automated backups |
| `BackupRetentionDays` | `7` | Backup retention (1-35 days) |

## Using Existing VPC

If you have an existing VPC, provide these parameters:

```bash
sam deploy \
  --parameter-overrides \
    VpcId=vpc-xxxxx \
    PrivateSubnetIds=subnet-xxxxx,subnet-yyyyy
```

## Database Access from Lambda

Lambda functions automatically receive these environment variables:

```python
DB_HOST = os.environ['DB_HOST']  # Aurora endpoint
DB_PORT = os.environ['DB_PORT']  # Usually 5432
DB_NAME = os.environ['DB_NAME']  # Database name
DB_USER = os.environ['DB_USER']  # Master username
```

### Connecting to Database

```python
import psycopg2
import os

def connect_to_db():
    conn = psycopg2.connect(
        host=os.environ['DB_HOST'],
        port=os.environ['DB_PORT'],
        database=os.environ['DB_NAME'],
        user=os.environ['DB_USER'],
        # Password from Secrets Manager or IAM auth
    )
    return conn
```

### Using Secrets Manager (Recommended)

```python
import boto3
import json
import psycopg2

def get_db_credentials():
    """Retrieve credentials from Secrets Manager"""
    client = boto3.client('secretsmanager')
    secret_name = f"cloudauditor-db-credentials-{os.environ['ENVIRONMENT']}"
    
    response = client.get_secret_value(SecretId=secret_name)
    secret = json.loads(response['SecretString'])
    
    return secret

def connect_with_secrets():
    creds = get_db_credentials()
    conn = psycopg2.connect(
        host=creds['host'],
        port=creds['port'],
        database=creds['dbname'],
        user=creds['username'],
        password=creds['password']
    )
    return conn
```

## Cost Optimization

### Aurora Serverless v2 Pricing

**Default Configuration (0.5 - 2 ACUs):**
- Minimum: 0.5 ACU × $0.12/hour = **$0.06/hour** = **~$43/month**
- Maximum: 2 ACU × $0.12/hour = **$0.24/hour** = **~$175/month**
- **Typical usage**: ~$50-80/month (scales based on load)

**Storage:**
- $0.10/GB-month
- $0.20/million I/O requests

**Backups:**
- Free up to 100% of database storage
- $0.021/GB-month beyond that

### Cost Reduction Strategies

1. **Lower Min Capacity** (Dev/Staging):
```yaml
AuroraMinCapacity: 0.5  # Minimum possible
AuroraMaxCapacity: 1    # Lower max for dev
```

2. **Disable Backups** (Dev only):
```yaml
EnableDatabaseBackups: false
```

3. **Use Existing VPC** (Save NAT Gateway costs):
- NAT Gateway: ~$32/month + data transfer
- Provide existing VPC to avoid creating new one

4. **Delete Dev Stacks** when not in use:
```bash
aws cloudformation delete-stack --stack-name cloudauditor-dev
```

## Database Initialization

### Create Tables

After deployment, initialize the database schema:

```bash
# Connect to database
psql -h <endpoint> -U cloudauditor_admin -d cloudauditor

# Create tables
CREATE TABLE IF NOT EXISTS audits (
    id SERIAL PRIMARY KEY,
    account_id VARCHAR(12),
    audit_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    findings JSONB
);

CREATE TABLE IF NOT EXISTS resources (
    id SERIAL PRIMARY KEY,
    resource_arn VARCHAR(512) UNIQUE,
    resource_type VARCHAR(128),
    account_id VARCHAR(12),
    region VARCHAR(32),
    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

CREATE INDEX idx_resources_type ON resources(resource_type);
CREATE INDEX idx_resources_account ON resources(account_id);
```

### Using Lambda for Initialization

Create a one-time Lambda function or add to existing:

```python
def initialize_database():
    """Initialize database schema"""
    conn = connect_to_db()
    cur = conn.cursor()
    
    # Create tables
    cur.execute("""
        CREATE TABLE IF NOT EXISTS audits (
            id SERIAL PRIMARY KEY,
            account_id VARCHAR(12),
            audit_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            findings JSONB
        )
    """)
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS resources (
            id SERIAL PRIMARY KEY,
            resource_arn VARCHAR(512) UNIQUE,
            resource_type VARCHAR(128),
            account_id VARCHAR(12),
            region VARCHAR(32),
            discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            metadata JSONB
        )
    """)
    
    conn.commit()
    cur.close()
    conn.close()
```

## Monitoring

### CloudWatch Metrics

Monitor Aurora in CloudWatch:
- **DatabaseConnections**: Active connections
- **CPUUtilization**: CPU usage
- **ServerlessDatabaseCapacity**: Current ACUs
- **FreeableMemory**: Available memory

### Set Up Alarms

```bash
aws cloudwatch put-metric-alarm \
  --alarm-name cloudauditor-db-high-cpu \
  --alarm-description "Alert when DB CPU > 80%" \
  --metric-name CPUUtilization \
  --namespace AWS/RDS \
  --statistic Average \
  --period 300 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2
```

## Troubleshooting

### Lambda Can't Connect to Database

1. **Check Security Groups**:
```bash
aws ec2 describe-security-groups \
  --filters "Name=tag:Name,Values=cloudauditor-aurora-sg-*"
```

2. **Verify VPC Configuration**:
```bash
aws lambda get-function-configuration \
  --function-name cloudauditor-manager-dev \
  --query 'VpcConfig'
```

3. **Test from Lambda**:
```python
import socket

def test_connection():
    host = os.environ['DB_HOST']
    port = int(os.environ['DB_PORT'])
    
    try:
        socket.create_connection((host, port), timeout=5)
        print(f"✅ Can reach {host}:{port}")
    except Exception as e:
        print(f"❌ Cannot reach {host}:{port}: {e}")
```

### High Costs

1. **Check Current Capacity**:
```bash
aws rds describe-db-clusters \
  --db-cluster-identifier <cluster-id> \
  --query 'DBClusters[0].ServerlessV2ScalingConfiguration'
```

2. **Lower Max Capacity**:
```bash
sam deploy --parameter-overrides AuroraMaxCapacity=1
```

3. **Review CloudWatch Metrics** to see actual usage patterns

## Security Best Practices

1. ✅ **Use Secrets Manager** for credentials (already configured)
2. ✅ **Enable IAM Database Authentication** (already enabled)
3. ✅ **Encrypt at rest** (already enabled)
4. ✅ **Private subnets only** (already configured)
5. ✅ **Security group restrictions** (already configured)
6. ⚠️ **Rotate credentials regularly** (manual)
7. ⚠️ **Enable Enhanced Monitoring** (optional, costs extra)

## Backup and Recovery

### Manual Snapshot

```bash
aws rds create-db-cluster-snapshot \
  --db-cluster-identifier cloudauditor-aurora-cluster-dev \
  --db-cluster-snapshot-identifier cloudauditor-manual-snapshot-$(date +%Y%m%d)
```

### Restore from Snapshot

```bash
aws rds restore-db-cluster-from-snapshot \
  --db-cluster-identifier cloudauditor-restored \
  --snapshot-identifier cloudauditor-manual-snapshot-20260131 \
  --engine aurora-postgresql
```

### Point-in-Time Recovery

Aurora automatically supports PITR within the backup retention window:

```bash
aws rds restore-db-cluster-to-point-in-time \
  --source-db-cluster-identifier cloudauditor-aurora-cluster-prod \
  --db-cluster-identifier cloudauditor-restored \
  --restore-to-time 2026-01-31T12:00:00Z
```

## Migration from Existing Database

If you have an existing PostgreSQL database:

1. **Export data**:
```bash
pg_dump -h old-host -U old-user -d old-db > backup.sql
```

2. **Import to Aurora**:
```bash
psql -h <aurora-endpoint> -U cloudauditor_admin -d cloudauditor < backup.sql
```

3. **Or use AWS DMS** for live migration

---

**Next Steps:**
1. Deploy the stack
2. Initialize database schema
3. Update Lambda functions to use database
4. Set up monitoring and alarms
