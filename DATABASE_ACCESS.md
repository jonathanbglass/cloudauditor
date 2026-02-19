# Database Access Guide

## Important: VPC Limitation

The CloudAuditor Aurora database is **deployed in a private VPC** and is **not publicly accessible**. This means you cannot connect to it directly from your local machine.

### Why the query_database.py script hangs:

The script tries to connect to the database endpoint, but since the database is in a VPC without public access, the connection times out.

## Solutions for Querying the Database

### Option 1: Use AWS Lambda (Recommended)

Create a simple Lambda function in the same VPC to query the database:

```python
# query_lambda.py
import json
from lib.database import DatabaseClient

def lambda_handler(event, context):
    db = DatabaseClient()
    conn = db._get_connection()
    
    query = event.get('query', 'SELECT COUNT(*) FROM resources')
    
    with conn.cursor() as cur:
        cur.execute(query)
        results = cur.fetchall()
    
    return {
        'statusCode': 200,
        'body': json.dumps({'results': results}, default=str)
    }
```

### Option 2: Use AWS Systems Manager Session Manager

Connect to an EC2 instance in the same VPC (if you have one) and run queries from there.

### Option 3: Enable Public Access (Not Recommended for Production)

You can modify the Aurora cluster to allow public access, but this is a security risk.

### Option 4: Use AWS RDS Proxy with Public Endpoint

Set up an RDS Proxy with a public endpoint to access the database.

## Best Practice: Query via Lambda

Since the Lambda functions already have VPC access, the best way to query the database is:

1. **Use CloudWatch Logs Insights** to query Lambda execution logs
2. **Create a custom query Lambda** (like the example above)
3. **Use the discovery Lambda** - it already saves all data to the database

## Viewing Discovery Results

### Via CloudWatch Logs:

```powershell
# View latest discovery results
aws logs tail /aws/lambda/cloudauditor-discovery-dev --profile cloudAuditor --region us-east-1 --since 1h --format short | Select-String -Pattern "total_resources|resource_types"
```

### Via Lambda Invocation:

```powershell
# Trigger discovery and see results
aws lambda invoke --function-name cloudauditor-discovery-dev --profile cloudAuditor --region us-east-1 output.json
Get-Content output.json | ConvertFrom-Json | ConvertTo-Json -Depth 5
```

## Alternative: Use main.py for Local Queries

The `main.py` script doesn't use the database - it discovers resources directly and saves to JSON/Excel:

```powershell
.\venv\Scripts\Activate.ps1
python main.py --accounts 286861024884 --format both --output-dir ./reports
```

This will create local JSON and Excel files with all discovered resources.

## Summary

- ❌ **Cannot** connect to Aurora database from local machine (VPC limitation)
- ✅ **Can** use Lambda to query database (already in VPC)
- ✅ **Can** use main.py for local discovery (no database needed)
- ✅ **Can** view results in CloudWatch Logs
