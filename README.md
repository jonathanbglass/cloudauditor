# CloudAuditor

AWS cloud auditing and resource discovery system.

## Overview

CloudAuditor is a comprehensive AWS auditing system that:
- Audits IAM users, roles, groups, and policies across multiple AWS accounts
- Discovers and inventories AWS resources automatically
- Stores audit data in PostgreSQL for analysis
- Runs as AWS Lambda functions for scheduled execution

## Features

### IAM Auditing
- Cross-account IAM auditing via STS AssumeRole
- User, role, group, and policy inventory
- EC2 instance tracking
- PostgreSQL database storage

### Resource Discovery (NEW)
- **Automatic discovery** of 200+ AWS resource types
- **Zero manual coding** - no per-service modules needed
- **Intelligent fallback** between Resource Explorer, Config, and Cloud Control API
- **Fast parallel processing** with configurable filters
- See [Resource Discovery Documentation](docs/resource_discovery/) for details

## Quick Start

### Prerequisites

- Python 3.14+
- AWS credentials configured
- PostgreSQL database (for IAM auditing)

### Local Development

```bash
# Clone repository
git clone <repository-url>
cd cloudauditor

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your credentials
```

### Deployment

**🚀 Quick Deploy with GitHub Actions + AWS SAM:**

1. Set GitHub Secrets (AWS credentials, database config)
2. Create S3 bucket: `aws s3 mb s3://cloudauditor-deployments-dev`
3. Push to `develop` branch → Auto-deploys to dev
4. Push to `main` branch → Auto-deploys to prod

**📖 See [QUICKSTART.md](QUICKSTART.md) for 5-minute deployment guide**
**📖 See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for complete deployment documentation**

### Local Testing

#### IAM Auditing

```bash
# Audit all accounts
python auditor.py

# Audit local account only
python auditor.py --audit local

# Audit remote accounts only
python auditor.py --audit remote
```

#### Resource Discovery

```bash
# Run discovery test
python test_discovery.py

# Use in code
from resource_discovery import ResourceDiscoveryEngine
engine = ResourceDiscoveryEngine()
result = engine.discover_all_resources()
print(f"Found {result.total_count} resources")
```

## Documentation

Comprehensive documentation is available in the [`docs/`](docs/) directory:

### Python 3.14 Upgrade
- [Assessment](docs/python_upgrade/01_assessment.md) - Upgrade analysis and planning
- [Upgrade Summary](docs/python_upgrade/02_upgrade_summary.md) - Completed changes
- [Modernization](docs/python_upgrade/03_modernization.md) - Code quality improvements

### Resource Discovery
- [Implementation Plan](docs/resource_discovery/implementation_plan.md) - Technical design
- [POC Walkthrough](docs/resource_discovery/poc_walkthrough.md) - Usage guide
- [Module README](resource_discovery/README.md) - Detailed API documentation

## Project Structure

```
cloudauditor/
├── docs/                      # Documentation
│   ├── python_upgrade/        # Python 3.14 upgrade docs
│   └── resource_discovery/    # Resource discovery docs
├── resource_discovery/        # Resource discovery module
│   ├── __init__.py
│   ├── models.py
│   ├── discovery_engine.py
│   ├── resource_explorer_client.py
│   ├── config_client.py
│   ├── cloud_control_client.py
│   └── README.md
├── lambda/                    # Lambda deployment scripts
│   └── setup_auditor.sh
├── auditor.py                 # Main auditor script
├── manager.py                 # Lambda manager function
├── processor.py               # Lambda processor function
├── process_*.py               # IAM processing modules
├── test_discovery.py          # Resource discovery test script
├── requirements.txt           # Python dependencies
├── .env.example               # Environment configuration template
└── README.md                  # This file
```

## Lambda Deployment

### Setup

1. Package Lambda function:
```bash
cd lambda
zip -r iso-iam-auditor.zip ../*.py ../lib/
```

2. Deploy using setup script:
```bash
./setup_auditor.sh
```

### Environment Variables

Lambda functions require these environment variables:
- `dbname` - Database name
- `dbuser` - Database user
- `dbhost` - Database host
- `dbpass` - Database password

## Requirements

### Python Packages

- boto3 >= 1.35.0 (AWS SDK)
- psycopg2-binary >= 2.9.9 (PostgreSQL driver)
- beautifulsoup4 >= 4.12.0 (HTML parsing)
- requests >= 2.32.0 (HTTP library)

### AWS Services

- IAM (for auditing)
- STS (for cross-account access)
- Lambda (for scheduled execution)
- SNS (for message passing)
- Resource Explorer (optional, for resource discovery)
- AWS Config (optional, for detailed configuration)

### IAM Permissions

See [implementation plan](docs/resource_discovery/implementation_plan.md) for detailed permission requirements.

## Database Schema

See `create_tables.sql` for the complete database schema.

Key tables:
- `aws_cross_account_roles` - Cross-account role configuration
- `aws_users` - IAM user inventory
- `aws_roles` - IAM role inventory
- `aws_groups` - IAM group inventory
- `aws_policies` - IAM policy inventory
- `aws_resources` - Resource discovery inventory (new)

## Development

### Running Tests

```bash
# Test resource discovery
python test_discovery.py

# Compile all Python files
python -m py_compile *.py resource_discovery/*.py
```

### Code Style

- Python 3.14+ syntax
- Type hints on all functions
- F-strings for formatting
- Structured logging (not print statements)
- Environment variables for configuration

## Version History

### 2026-01-31
- ✅ Upgraded to Python 3.14
- ✅ Added type hints and modern Python features
- ✅ Implemented structured logging
- ✅ Added resource discovery system
- ✅ Created comprehensive documentation

### Previous
- Legacy Python 3.6.5 codebase
- IAM auditing functionality
- Lambda deployment

## License

[Add license information]

## Support

For issues or questions, refer to the documentation in the `docs/` directory.
