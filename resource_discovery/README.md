# Resource Discovery POC - README

## Overview

Intelligent AWS resource discovery system that automatically discovers all AWS resources across your account without requiring manual per-service modules.

## Features

- **Hybrid Discovery**: Uses Resource Explorer, AWS Config, and Cloud Control API
- **Automatic Fallback**: Intelligently falls back between discovery methods
- **200+ Resource Types**: Supports all AWS services automatically
- **Multi-Region**: Discovers resources across all regions
- **Parallel Processing**: Fast discovery using thread pools
- **Type Filtering**: Include/exclude specific resource types
- **Comprehensive Data**: ARNs, tags, configuration, relationships

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure AWS Credentials

```bash
aws configure
# Or set environment variables:
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
export AWS_DEFAULT_REGION=us-east-1
```

### 3. Run the Test Script

```bash
python test_discovery.py
```

## Usage Examples

### Basic Discovery

```python
from resource_discovery import ResourceDiscoveryEngine

engine = ResourceDiscoveryEngine()
result = engine.discover_all_resources()

print(f"Found {result.total_count} resources")
```

### Filtered Discovery

```python
from resource_discovery import ResourceDiscoveryEngine, DiscoveryConfig

config = DiscoveryConfig(
    include_types=['AWS::EC2::Instance', 'AWS::S3::Bucket'],
    regions=['us-east-1']
)

engine = ResourceDiscoveryEngine(config=config)
result = engine.discover_all_resources()
```

### Get Resource Summary

```python
summary = engine.get_resource_summary(result)
for resource_type, count in summary.items():
    print(f"{resource_type}: {count}")
```

## Architecture

### Discovery Flow

1. **Resource Explorer** (Primary)
   - Fastest and most comprehensive
   - 200+ resource types
   - Multi-account search

2. **AWS Config** (Secondary)
   - Detailed configuration data
   - Configuration history
   - Compliance information

3. **Cloud Control API** (Fallback)
   - Universal CRUDL operations
   - All CloudFormation types
   - Standardized interface

### Components

- `discovery_engine.py` - Main orchestrator
- `resource_explorer_client.py` - Resource Explorer wrapper
- `config_client.py` - AWS Config wrapper
- `cloud_control_client.py` - Cloud Control API wrapper
- `models.py` - Data models (Resource, DiscoveryConfig, etc.)

## Configuration Options

```python
DiscoveryConfig(
    # Which discovery methods to use
    use_resource_explorer=True,
    use_config=True,
    use_cloud_control=False,
    
    # Resource type filters
    include_types=None,  # None = all types
    exclude_types=[],
    
    # Region configuration
    regions=None,  # None = all regions
    
    # Performance tuning
    batch_size=100,
    max_workers=10,
    max_retries=3
)
```

## Requirements

### AWS Services

- **Resource Explorer**: Recommended (automatic indexing)
- **AWS Config**: Optional (for detailed configuration)
- **IAM Permissions**: See below

### IAM Permissions

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "resource-explorer-2:Search",
        "resource-explorer-2:ListIndexes",
        "resource-explorer-2:GetResource",
        "config:DescribeConfigurationRecorders",
        "config:DescribeConfigurationRecorderStatus",
        "config:ListDiscoveredResources",
        "config:GetResourceConfigHistory",
        "cloudcontrol:ListResources",
        "cloudcontrol:GetResource",
        "sts:GetCallerIdentity"
      ],
      "Resource": "*"
    }
  ]
}
```

## Output Format

Each discovered resource includes:

```python
Resource(
    arn='arn:aws:ec2:us-east-1:123456789012:instance/i-1234567890abcdef0',
    resource_type='AWS::EC2::Instance',
    region='us-east-1',
    account_id='123456789012',
    name='my-instance',
    tags={'Environment': 'Production', 'Team': 'Platform'},
    configuration={...},  # Full resource configuration
    relationships=[...],  # Related resource ARNs
    created_at=datetime(...),
    last_modified=datetime(...),
    source=DiscoverySource.RESOURCE_EXPLORER
)
```

## Troubleshooting

### Resource Explorer Not Available

```
WARNING: Resource Explorer index not found, disabling
```

**Solution**: Enable Resource Explorer in AWS Console or CLI:

```bash
aws resource-explorer-2 create-index --region us-east-1
aws resource-explorer-2 create-view --view-name default-view
```

### AWS Config Not Enabled

```
WARNING: AWS Config not enabled, disabling
```

**Solution**: Enable AWS Config in AWS Console or use the setup wizard.

### No Resources Found

- Check IAM permissions
- Verify AWS credentials are correct
- Ensure resources exist in the account
- Try enabling Resource Explorer

## Performance

- **Small accounts** (<1000 resources): ~5-10 seconds
- **Medium accounts** (1000-10000 resources): ~30-60 seconds
- **Large accounts** (>10000 resources): ~2-5 minutes

## Next Steps

1. Test the POC with your AWS account
2. Review discovered resources
3. Integrate with database (see implementation plan)
4. Deploy as Lambda function
5. Add scheduled discovery

## Support

For issues or questions, refer to the implementation plan document.
