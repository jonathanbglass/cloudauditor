# Deprecated Code

This directory contains legacy Python 2/3 code that has been replaced by the modern resource discovery engine.

## Legacy Scripts (Python 2 Era)

### Main Scripts
- **auditor.py** - Original main auditor script
- **manager.py** - Old Lambda manager (replaced by modern manager in root)
- **processor.py** - Old Lambda processor (replaced by modern processor in root)

### IAM Processing Modules
- **process_users.py** - IAM users processing
- **process_roles.py** - IAM roles processing
- **process_groups.py** - IAM groups processing
- **process_policies.py** - IAM policies processing
- **process_instances.py** - EC2 instances processing
- **process_cht_aws_users.py** - CHT AWS users processing
- **process_cht_ec2_instances.py** - CHT EC2 instances processing

### Utilities
- **example_assume_role.py** - Cross-account role assumption example

### API
- **api/** - Legacy API directory

## Why Deprecated?

These scripts were designed for the original CloudAuditor architecture which:
- Used Python 2.7 (later partially upgraded to Python 3)
- Focused only on IAM resources (users, roles, groups, policies)
- Used psycopg2 for database connections
- Had separate processing modules for each resource type
- Required manual schema management

## Modern Replacement

The new CloudAuditor uses:
- **Python 3.14** - Latest Python runtime
- **Resource Discovery Engine** - Discovers 40+ AWS resource types
  - `resource_discovery/discovery_engine.py`
  - `resource_discovery/resource_explorer_client.py`
  - `resource_discovery/config_client.py`
  - `resource_discovery/cloud_control_client.py`
- **Automated Schema** - Database initialization via Lambda
- **Modern Architecture** - SAM + GitHub Actions deployment
- **Flexible Storage** - JSONB for any resource type

## Migration Notes

If you need to reference the old logic:
1. IAM processing logic → See `deprecated/process_*.py`
2. Database schema → See `database/legacy_schema.sql`
3. Cross-account roles → See `deprecated/example_assume_role.py`

The new resource discovery engine automatically discovers all resource types including IAM, EC2, VPC, S3, Lambda, and more.

## Do Not Use

⚠️ **These files are kept for historical reference only.**  
⚠️ **Do not use in production.**  
⚠️ **Use the modern resource discovery engine instead.**
