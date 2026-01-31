# Intelligent AWS Resource Discovery System - Implementation Plan

## Problem Statement

Currently, the CloudAuditor requires writing a separate Python module for EACH AWS service (EC2, RDS, Lambda, etc.), manually coding Get, List, and Describe API calls. This approach is:
- **Time-consuming**: New services require new modules
- **Error-prone**: Manual API call construction
- **Incomplete**: Easy to miss services or resource types
- **Maintenance-heavy**: API changes require updates

## Proposed Solution: Hybrid Multi-Service Approach

After researching modern AWS capabilities, I recommend a **hybrid approach** leveraging three complementary AWS services:

### 1. **AWS Resource Explorer** (Primary - Discovery & Search)
- **Best for**: Comprehensive resource discovery across all regions and accounts
- **Coverage**: 200+ resource types (as of Dec 2024)
- **Key Features**:
  - Multi-account search via AWS Organizations
  - New `ListResources` API for programmatic access
  - Automatic indexing with minimal setup
  - Tags, names, IDs searchable
  - Resource relationships and insights

### 2. **AWS Config** (Secondary - Configuration Tracking)
- **Best for**: Detailed configuration history and compliance
- **Coverage**: 100+ resource types with full configuration details
- **Key Features**:
  - `list_discovered_resources()` API
  - Configuration snapshots and history
  - Relationship tracking
  - Compliance rules integration

### 3. **AWS Cloud Control API** (Tertiary - Universal CRUD)
- **Best for**: Standardized resource management
- **Coverage**: All CloudFormation-supported resources
- **Key Features**:
  - Unified CRUDL operations (Create, Read, Update, Delete, List)
  - Consistent API across all services
  - Immediate support for new AWS services

## User Review Required

> [!IMPORTANT]
> **Approach Decision**: This plan uses a hybrid multi-service approach rather than a single API. This provides:
> - **Completeness**: Resource Explorer for discovery + Config for details
> - **Flexibility**: Fall back to Cloud Control API for unsupported types
> - **Cost**: Resource Explorer and Config have associated costs (minimal for small-scale)
>
> **Alternative**: Use only Cloud Control API (simpler but less feature-rich)

> [!WARNING]
> **AWS Config Requirement**: Requires AWS Config to be enabled in target accounts. If not enabled, we'll fall back to Resource Explorer + Cloud Control API only.

## Proposed Changes

### Core Discovery Engine

#### [NEW] `resource_discovery/discovery_engine.py`

Main orchestrator that intelligently selects the best discovery method:

```python
class ResourceDiscoveryEngine:
    def __init__(self, session, regions=None):
        self.resource_explorer = ResourceExplorerClient(session)
        self.config_client = ConfigClient(session)
        self.cloud_control = CloudControlClient(session)
        
    def discover_all_resources(self, account_id: str) -> List[Resource]:
        """
        Intelligently discover all resources using hybrid approach:
        1. Try Resource Explorer first (fastest, most comprehensive)
        2. Fall back to Config for detailed configuration
        3. Use Cloud Control API for unsupported types
        """
```

**Features**:
- Automatic service detection
- Multi-region support
- Pagination handling
- Error recovery and fallback logic
- Progress tracking and logging

---

#### [NEW] `resource_discovery/resource_explorer_client.py`

Wrapper for AWS Resource Explorer API:

```python
class ResourceExplorerClient:
    def list_all_resources(self, filters=None) -> Iterator[Dict]:
        """
        Use Resource Explorer ListResources API
        - Handles pagination (1000 result limit per call)
        - Supports filtering by tags, resource types, regions
        - Returns standardized resource format
        """
```

**Key Methods**:
- `list_all_resources()` - Paginate through all resources
- `search_resources(query)` - Natural language search
- `get_resource_details(arn)` - Fetch enhanced insights
- `list_supported_types()` - Get available resource types

---

#### [NEW] `resource_discovery/config_client.py`

Wrapper for AWS Config API:

```python
class ConfigClient:
    def list_discovered_resources(self, resource_type: str) -> List[Dict]:
        """
        Use Config list_discovered_resources API
        - Get detailed configuration for specific resource types
        - Include configuration history
        - Relationship mapping
        """
```

**Key Methods**:
- `list_discovered_resources(type)` - List by resource type
- `get_resource_config(arn)` - Get full configuration
- `get_resource_history(arn)` - Configuration timeline
- `check_compliance(arn)` - Compliance status

---

#### [NEW] `resource_discovery/cloud_control_client.py`

Wrapper for AWS Cloud Control API:

```python
class CloudControlClient:
    def list_resources(self, type_name: str) -> List[Dict]:
        """
        Use Cloud Control API for universal resource listing
        - Standardized CRUDL operations
        - Works for all CloudFormation types
        - Fallback when other methods unavailable
        """
```

**Key Methods**:
- `list_resources(type)` - List resources of specific type
- `get_resource(identifier)` - Get resource details
- `list_supported_types()` - Available resource types

---

### Data Processing & Storage

#### [NEW] `resource_discovery/resource_normalizer.py`

Normalizes data from different sources into unified format:

```python
class ResourceNormalizer:
    def normalize(self, raw_resource: Dict, source: str) -> Resource:
        """
        Convert from Resource Explorer/Config/Cloud Control format
        to standardized Resource object
        """
```

**Standardized Resource Format**:
```python
@dataclass
class Resource:
    arn: str
    resource_type: str
    region: str
    account_id: str
    name: Optional[str]
    tags: Dict[str, str]
    configuration: Dict[str, Any]
    relationships: List[str]
    created_at: datetime
    last_modified: datetime
    source: str  # 'resource_explorer', 'config', 'cloud_control'
```

---

#### [NEW] `resource_discovery/database_writer.py`

Handles database operations:

```python
class DatabaseWriter:
    def bulk_insert_resources(self, resources: List[Resource]):
        """
        Efficiently insert/update resources in database
        - Upsert logic (insert or update if exists)
        - Batch operations for performance
        - Transaction management
        """
```

**Database Schema**:
```sql
CREATE TABLE aws_resources (
    id SERIAL PRIMARY KEY,
    arn VARCHAR(512) UNIQUE NOT NULL,
    resource_type VARCHAR(128) NOT NULL,
    region VARCHAR(32) NOT NULL,
    account_id VARCHAR(12) NOT NULL,
    name VARCHAR(256),
    tags JSONB,
    configuration JSONB,
    relationships JSONB,
    created_at TIMESTAMP,
    last_modified TIMESTAMP,
    discovered_at TIMESTAMP DEFAULT NOW(),
    discovery_source VARCHAR(32),
    INDEX idx_account_type (account_id, resource_type),
    INDEX idx_arn (arn),
    INDEX idx_tags (tags) USING GIN
);
```

---

### Lambda Functions

#### [MODIFY] `manager.py`

Add resource discovery to existing manager:

```python
def lambda_handler(event, context):
    # Existing code...
    
    # NEW: Trigger resource discovery
    if event.get('discover_resources'):
        discovery_engine = ResourceDiscoveryEngine(boto3.Session())
        resources = discovery_engine.discover_all_resources(account_id)
        
        db_writer = DatabaseWriter(cur)
        db_writer.bulk_insert_resources(resources)
```

---

#### [NEW] `resource_discovery_lambda.py`

Dedicated Lambda for resource discovery:

```python
def lambda_handler(event, context):
    """
    Triggered by:
    - CloudWatch Events (scheduled)
    - SNS messages (on-demand)
    - API Gateway (manual trigger)
    """
    account_id = event['account_id']
    regions = event.get('regions', ['all'])
    
    engine = ResourceDiscoveryEngine(boto3.Session(), regions)
    resources = engine.discover_all_resources(account_id)
    
    # Store in database
    db_writer = DatabaseWriter()
    db_writer.bulk_insert_resources(resources)
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'resources_discovered': len(resources),
            'account_id': account_id
        })
    }
```

---

### Configuration & Deployment

#### [NEW] `resource_discovery/config.py`

Configuration management:

```python
@dataclass
class DiscoveryConfig:
    # Which discovery methods to use
    use_resource_explorer: bool = True
    use_config: bool = True
    use_cloud_control: bool = False  # Fallback only
    
    # Resource type filters
    include_types: List[str] = None  # None = all types
    exclude_types: List[str] = []
    
    # Region configuration
    regions: List[str] = None  # None = all regions
    
    # Performance tuning
    batch_size: int = 100
    max_workers: int = 10
    
    # Database configuration
    db_config: Dict = field(default_factory=dict)
```

---

#### [MODIFY] `requirements.txt`

Add new dependencies:

```
boto3>=1.35.0
psycopg2-binary>=2.9.9
beautifulsoup4>=4.12.0
requests>=2.32.0

# NEW: For resource discovery
dataclasses-json>=0.6.0  # Serialization
tenacity>=8.2.0  # Retry logic
```

---

#### [NEW] `lambda/setup_resource_discovery.sh`

Deployment script for new Lambda:

```bash
#!/bin/bash
# Package and deploy resource discovery Lambda
cd resource_discovery
zip -r ../lambda/resource-discovery.zip *.py
cd ../lambda

aws lambda create-function \
  --function-name cloud-auditor-resource-discovery \
  --runtime python3.14 \
  --handler resource_discovery_lambda.lambda_handler \
  --role arn:aws:iam::ACCOUNT:role/LambdaExecutionRole \
  --code S3Bucket=...,S3Key=resource-discovery.zip \
  --timeout 900 \
  --memory-size 1024
```

## Verification Plan

### Automated Tests

1. **Unit Tests** - `tests/test_discovery_engine.py`
   ```bash
   pytest tests/test_discovery_engine.py -v
   ```
   - Test Resource Explorer client pagination
   - Test Config client error handling
   - Test resource normalization
   - Test database upsert logic

2. **Integration Tests** - `tests/test_integration.py`
   ```bash
   # Requires AWS credentials and test account
   pytest tests/test_integration.py --aws-account=123456789012
   ```
   - Test end-to-end discovery in real AWS account
   - Verify all three discovery methods
   - Validate database insertion

3. **Lambda Tests** - `tests/test_lambda.py`
   ```bash
   # Test Lambda handler locally
   python -m pytest tests/test_lambda.py
   ```
   - Mock Lambda events
   - Test error handling
   - Verify response format

### Manual Verification

1. **Enable AWS Resource Explorer** (if not already enabled)
   ```bash
   aws resource-explorer-2 create-index --region us-east-1
   aws resource-explorer-2 create-view --view-name default-view
   ```

2. **Run Discovery Locally**
   ```bash
   python -m resource_discovery.discovery_engine \
     --account-id 123456789012 \
     --regions us-east-1,us-west-2
   ```
   
   **Expected Output**:
   - List of discovered resources with counts by type
   - Database insertion confirmation
   - No errors or warnings

3. **Deploy to Lambda and Test**
   ```bash
   cd lambda
   ./setup_resource_discovery.sh
   
   # Trigger manually
   aws lambda invoke \
     --function-name cloud-auditor-resource-discovery \
     --payload '{"account_id":"123456789012"}' \
     response.json
   
   cat response.json
   ```
   
   **Expected**: JSON response with resource count

4. **Verify Database Contents**
   ```sql
   -- Check resource counts
   SELECT resource_type, COUNT(*) 
   FROM aws_resources 
   GROUP BY resource_type 
   ORDER BY COUNT(*) DESC;
   
   -- Verify recent discoveries
   SELECT * FROM aws_resources 
   WHERE discovered_at > NOW() - INTERVAL '1 hour'
   LIMIT 10;
   ```

5. **Compare with Manual Count**
   - Use AWS Console to manually count EC2 instances
   - Compare with database count for EC2::Instance
   - Should match within 1-2 resources (timing differences)

## Benefits of This Approach

| Benefit | Description |
|---------|-------------|
| **Zero Manual Modules** | No need to write per-service code |
| **Automatic New Services** | Resource Explorer adds new types automatically |
| **Multi-Region** | Discover across all regions simultaneously |
| **Multi-Account** | Works with AWS Organizations |
| **Comprehensive** | 200+ resource types vs ~10 currently |
| **Maintainable** | Single discovery engine vs dozens of modules |
| **Flexible** | Can enable/disable discovery methods |
| **Scalable** | Lambda-based, handles large accounts |

## Cost Considerations

- **Resource Explorer**: ~$0.0001 per resource per month (indexed)
- **AWS Config**: ~$0.003 per configuration item per month
- **Cloud Control API**: No additional cost
- **Lambda**: Minimal (seconds of execution time)

**Estimated cost for 10,000 resources**: ~$30-40/month

## Migration Path

1. **Phase 1**: Deploy new discovery engine alongside existing modules
2. **Phase 2**: Run both in parallel, compare results
3. **Phase 3**: Gradually deprecate old per-service modules
4. **Phase 4**: Remove old code once validated

---

**Ready for Implementation**: This plan provides a modern, scalable, intelligent approach to AWS resource discovery that eliminates manual per-service coding.
