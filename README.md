# 🚀 CloudAuditor: The Future of AWS Resource Discovery

**CloudAuditor** has evolved! We've transformed from a legacy IAM auditing tool into a high-performance, **Universal AWS Resource Discovery Engine**. It is now the ultimate Swiss Army knife for AWS enthusiasts, developers, and security professionals who want absolute visibility into their global cloud footprint.

## 🌟 What's New?

### 🔎 Universal Discovery Engine (Enhanced)
Our revolutionary discovery process provides **100% visibility** using an intelligent multi-layer fallback strategy:
1.  **🚀 AWS Resource Explorer 2**: Lightning-fast indexed search for rapid discovery.
2.  **📋 AWS Config**: Deep inspection for compliant and non-compliant resources.
3.  **🌩️ AWS Cloud Control API**: The ultimate fallback for the latest AWS resource types.

### 🌎 Global Footprint Scanning
- **Multi-Region Excellence**: Automatically scans all active regions in your account in parallel.
- **200+ Resource Types**: From Lambda and S3 to modern VPC Lattice and AppRunner resources.
- **Zero Configuration**: Just deploy and watch it discover.

### 🛠️ Modernized Architecture
- **Python 3.13 Ready**: Optimized for the latest AWS Lambda runtimes.
- **Aurora Serverless v2**: High-performance PostgreSQL 15.8 with automated schema management.
- **One-Click Deployment**: Fully automated via GitHub Actions and AWS SAM.
- **Zero Manual DB Ops**: The schema auto-initializes the moment the stack is ready.

### 📊 Advanced Reporting & Analytics
- **Excel Report Generation**: Lambda-based report generator with S3 delivery
  - Executive Summary with discovery metrics
  - All Resources with full details and timestamps
  - Resource breakdowns by Type, Account, and Region
- **Timestamp Tracking**: Track when resources are first discovered
  - `inserted_at` column for historical analysis
  - Date-based filtering for "latest only" reports
  - Support for multiple discovery runs per day
- **Multi-Account Support**: Automatic discovery across AWS Organizations
  - Hub-and-spoke IAM pattern with cross-account roles
  - StackSet deployment for spoke accounts
  - Centralized reporting across all accounts

### 🔧 Data Quality & Consistency
- **Global Resource Normalization**: Consistent handling of global AWS resources
  - Empty regions automatically normalized to 'global'
  - DatabaseClient safety net prevents duplicate entries
  - Clean data for IAM, S3, CloudFront, Route53, etc.
- **Deduplication**: Automatic cleanup of duplicate resources
- **Data Integrity**: Robust error handling and validation

## Quick Start

### 🚀 5-Minute Deployment

See **[QUICKSTART.md](QUICKSTART.md)** for step-by-step deployment guide.

**TL;DR:**
1. Create S3 bucket: `aws s3 mb s3://cloudauditor-artifacts-2026`
2. Set GitHub Secrets: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `DB_PASSWORD`
3. Push to `develop` branch → Auto-deploys to AWS!

### Local Testing

```bash
# Test resource discovery
python test_discovery.py

# Use in code
from resource_discovery import ResourceDiscoveryEngine
engine = ResourceDiscoveryEngine()
result = engine.discover_all_resources()
print(f"Found {result.total_count} resources")
```

## Project Structure

```
cloudauditor/
├── .github/workflows/         # GitHub Actions CI/CD
│   └── deploy.yml            # Automated deployment pipeline
├── database/                  # Database schemas and utilities
│   ├── schema.sql            # Modern resource discovery schema
│   ├── legacy_schema.sql     # Archived IAM-only schema
│   └── README.md             # Database documentation
├── database_init/             # Automated schema initialization
│   ├── app.py                # Lambda function for DB init
│   └── requirements.txt      # Dependencies
├── resource_discovery/        # Resource discovery engine
│   ├── __init__.py
│   ├── models.py             # Data models
│   ├── discovery_engine.py   # Main discovery logic
│   ├── resource_explorer_client.py
│   ├── config_client.py
│   ├── cloud_control_client.py
│   └── README.md             # API documentation
├── deprecated/                # Legacy Python 2 scripts (archived)
│   ├── auditor.py            # Old main script
│   ├── manager.py            # Old Lambda manager
│   ├── processor.py          # Old Lambda processor
│   ├── process_*.py          # IAM processing modules
│   └── README.md             # Migration notes
├── docs/                      # Documentation
│   ├── python_upgrade/       # Python 3.14 upgrade docs
│   └── resource_discovery/   # Resource discovery docs
├── resource_discovery_lambda.py  # Lambda handler
├── test_discovery.py          # Discovery test script
├── template.yaml              # AWS SAM template
├── samconfig.toml             # SAM configuration
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

## Documentation

### Getting Started
- **[QUICKSTART.md](QUICKSTART.md)** - 5-minute deployment guide
- **[database/README.md](database/README.md)** - Database schema and queries
- **[resource_discovery/README.md](resource_discovery/README.md)** - API documentation

### Technical Details
- **[Python 3.14 Upgrade](docs/python_upgrade/)** - Modernization journey
- **[Resource Discovery](docs/resource_discovery/)** - Implementation details
- **[Deprecated Code](deprecated/README.md)** - Legacy scripts reference

## Deployed Infrastructure

### Compute & Events
- ✅ **4 Core Lambda Functions**
  - `cloudauditor-discovery-dev` - Universal Resource Discovery Engine
  - `cloudauditor-db-init-dev` - Automated Database Initialization
  - `cloudauditor-query-dev` - Database Query Interface
  - `cloudauditor-report-generator-dev` - Excel Report Generation with S3 Delivery
- ✅ **EventBridge Rules** for scheduled daily execution

### Database
- ✅ **Aurora Serverless v2** PostgreSQL 15.8
- ✅ **Automatic schema creation** via custom resource
- ✅ **Secrets Manager** for credentials
- ✅ **Data API enabled** for RDS Query Editor access

### Networking
- ✅ **VPC** with public/private subnets
- ✅ **NAT Gateway** for Lambda internet access
- ✅ **Security Groups** with least-privilege rules

### Security
- ✅ **IAM Roles** with minimal permissions
- ✅ **VPC isolation** for database
- ✅ **Encryption at rest** for Aurora
- ✅ **CloudWatch Logs** with 30-day retention

## Database Schema

The modern schema supports flexible resource storage:

```sql
-- Main resources table
CREATE TABLE resources (
    id BIGSERIAL PRIMARY KEY,
    resource_id TEXT NOT NULL,
    resource_type TEXT NOT NULL,
    resource_arn TEXT,
    region TEXT NOT NULL,
    account_id TEXT NOT NULL,
    name TEXT,
    tags JSONB,
    properties JSONB NOT NULL,
    discovered_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_seen_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    inserted_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Query examples
SELECT resource_type, COUNT(*) FROM resources GROUP BY resource_type;
SELECT * FROM resources WHERE tags @> '{"Environment": "production"}';
SELECT * FROM resources WHERE DATE(inserted_at) = CURRENT_DATE; -- Today's discoveries
```

See [database/README.md](database/README.md) for complete schema and query examples.

## Testing Your Deployment

```bash
# Invoke discovery Lambda
aws lambda invoke \
  --function-name cloudauditor-discovery-dev \
  --region us-east-1 \
  response.json

# View logs
aws logs tail /aws/lambda/cloudauditor-discovery-dev --follow

# Query database (RDS Query Editor)
SELECT * FROM resources LIMIT 10;
```

## Cost Estimate (Monthly)

| Service | Dev Environment | Production |
|---------|----------------|------------|
| Aurora Serverless v2 | $50-80 | $100-200 |
| NAT Gateway | $32-40 | $32-40 |
| Lambda | $5-10 | $20-50 |
| CloudWatch Logs | $1-2 | $5-10 |
| Secrets Manager | $0.40 | $0.40 |
| S3 Storage | $0.50 | $2-5 |
| **Total** | **~$90-133** | **~$160-305** |

**Cost Optimization:**
- Use existing VPC (saves $32/month)
- Lower Aurora capacity: `AuroraMaxCapacity=1` (saves ~$40/month)
- Delete dev stack when not in use

## Development

### Requirements
- Python 3.13+ (Lambda uses 3.13 for DB init, 3.14 for discovery)
- AWS SAM CLI
- AWS credentials configured

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
python test_discovery.py

# Build SAM
sam build

# Deploy locally
sam deploy --guided
```

### Code Style
- Python 3.13+ syntax
- Type hints on all functions
- F-strings for formatting
- Structured logging
- Environment variables for configuration

## Version History

### 2026-02-02 - Advanced Reporting & Data Quality
- ✅ **Timestamp Tracking**: Added `inserted_at` column for historical asset tracking
  - Date-based filtering for "latest only" reports
  - Support for multiple discovery runs per day
  - Excel reports now include discovery timestamps
- ✅ **Excel Report Generation**: Lambda-based report generator with S3 delivery
  - Executive Summary with discovery metrics and data freshness
  - All Resources sheet with full details and timestamps
  - Resource breakdowns by Type, Account, and Region
- ✅ **Global Resource Normalization**: Fixed duplicate global resources
  - DatabaseClient safety net normalizes empty regions to 'global'
  - Cleaned up 30 duplicate entries from database
  - Consistent handling of IAM, S3, CloudFront, Route53
- ✅ **Multi-Account Support**: Cross-account discovery via Organizations
  - Hub-and-spoke IAM pattern with StackSet deployment
  - Automatic account discovery and onboarding
  - Centralized reporting across all accounts

### 2026-02-01 - Stability & OS Optimization
- ✅ **Python 3.13 Downgrade**: Resolved deployment timeouts by shifting to a fully supported Lambda runtime.
- ✅ **PowerShell Compatibility**: Optimized project for Windows development environments.
- ✅ **Documentation Refresh**: Added exciting new feature announcements and architectural simplifications.

### 2026-01-31 - Universal Discovery Launch
- ✅ **Upgraded to Python Runtimes** for Lambda functions
- ✅ **Automated deployment** via GitHub Actions + SAM
- ✅ **Aurora Serverless v2** with auto-provisioning
- ✅ **Database auto-initialization** via Lambda custom resource
- ✅ **Resource discovery engine** (200+ resource types)
- ✅ **Cleaned codebase** - removed legacy IAM-only scripts

### Previous
- Legacy Python 2.7/3.6 codebase
- IAM-only auditing (users, roles, groups, policies)
- Manual deployment and configuration

## Migration from Legacy

If you're migrating from the old Python 2 version:

1. **Database:** Old schema in `database/legacy_schema.sql` (reference only)
2. **Scripts:** Legacy code in `deprecated/` directory
3. **New approach:** Modern resource discovery replaces manual IAM processing
4. **See:** [deprecated/README.md](deprecated/README.md) for migration notes

## Support

- **Issues:** Use GitHub Issues for bug reports
- **Documentation:** See `docs/` directory
- **Questions:** Refer to module READMEs

## License

[Add license information]
