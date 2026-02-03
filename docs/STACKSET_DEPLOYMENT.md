# StackSet Deployment Guide

## Overview

CloudAuditor uses AWS CloudFormation StackSets to deploy the **CloudAuditorExecutionRole** to all member accounts in your AWS Organization. This role allows the CloudAuditor Lambda functions in the hub account to assume cross-account access and discover resources.

## Prerequisites

- AWS Organizations enabled
- CloudAuditor deployed in the hub/management account
- Administrator access to the Organization management account
- StackSets enabled in your Organization

## Architecture

```
┌─────────────────────────────────────┐
│   Hub Account (286861024884)        │
│                                      │
│  ┌────────────────────────────────┐ │
│  │ CloudAuditor Lambda Functions  │ │
│  │  - Discovery                   │ │
│  │  - Query                       │ │
│  │  - Database Init               │ │
│  └────────────────────────────────┘ │
│              │                       │
│              │ AssumeRole            │
└──────────────┼───────────────────────┘
               │
               ▼
    ┌──────────────────────────┐
    │  StackSet (Root OU)      │
    │  CloudAuditorSpokeRole   │
    └──────────────────────────┘
               │
       ┌───────┴───────┬───────────┐
       ▼               ▼           ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│ Member      │ │ Member      │ │ Member      │
│ Account 1   │ │ Account 2   │ │ Account 3   │
│             │ │             │ │             │
│ CloudAuditor│ │ CloudAuditor│ │ CloudAuditor│
│ Execution   │ │ Execution   │ │ Execution   │
│ Role        │ │ Role        │ │ Role        │
└─────────────┘ └─────────────┘ └─────────────┘
```

## Step 1: Verify StackSet Exists

Check if the StackSet has already been created:

```powershell
aws cloudformation describe-stack-set `
  --stack-set-name CloudAuditorSpokeRole `
  --profile cloudAuditor `
  --region us-east-1 | ConvertFrom-Json | `
  Select-Object -ExpandProperty StackSet | `
  Select-Object StackSetName, Status
```

**Expected Output:**
```
StackSetName          Status
------------          ------
CloudAuditorSpokeRole ACTIVE
```

## Step 2: Create StackSet (If Needed)

If the StackSet doesn't exist, create it:

```powershell
aws cloudformation create-stack-set `
  --stack-set-name CloudAuditorSpokeRole `
  --template-body file://infrastructure/spoke-role.yaml `
  --parameters ParameterKey=HubAccountId,ParameterValue=286861024884 `
  --capabilities CAPABILITY_NAMED_IAM `
  --permission-model SERVICE_MANAGED `
  --auto-deployment Enabled=true,RetainStacksOnAccountRemoval=false `
  --profile cloudAuditor `
  --region us-east-1
```

**Parameters:**
- `HubAccountId`: The AWS account ID where CloudAuditor is deployed (replace `286861024884` with your hub account ID)
- `permission-model SERVICE_MANAGED`: Allows automatic deployment to Organization accounts
- `auto-deployment Enabled=true`: Automatically deploys to new accounts added to the Organization

## Step 3: Get Organization Root OU

Find your Organization's root OU ID:

```powershell
aws organizations list-roots `
  --profile cloudAuditor `
  --region us-east-1 | ConvertFrom-Json | `
  Select-Object -ExpandProperty Roots | `
  Select-Object Id, Name
```

**Expected Output:**
```
Id     Name
--     ----
r-s4nj Root
```

## Step 4: Deploy Stack Instances

Deploy the spoke role to all accounts in the Organization:

```powershell
aws cloudformation create-stack-instances `
  --stack-set-name CloudAuditorSpokeRole `
  --deployment-targets OrganizationalUnitIds=r-s4nj `
  --regions us-east-1 `
  --profile cloudAuditor `
  --region us-east-1 | ConvertFrom-Json | `
  Select-Object OperationId
```

**Note:** Replace `r-s4nj` with your root OU ID from Step 3.

**Expected Output:**
```
OperationId
-----------
67ece20c-e837-4a80-9458-0c22590fdc16
```

## Step 5: Monitor Deployment

Check the deployment status:

```powershell
# Check operation status
aws cloudformation describe-stack-set-operation `
  --stack-set-name CloudAuditorSpokeRole `
  --operation-id <OPERATION_ID> `
  --profile cloudAuditor `
  --region us-east-1 | ConvertFrom-Json | `
  Select-Object -ExpandProperty StackSetOperation | `
  Select-Object Status, Action
```

**Status Values:**
- `RUNNING` - Deployment in progress
- `SUCCEEDED` - Deployment completed successfully
- `FAILED` - Deployment failed (check individual stack instances)

## Step 6: Verify Stack Instances

List all deployed stack instances:

```powershell
aws cloudformation list-stack-instances `
  --stack-set-name CloudAuditorSpokeRole `
  --profile cloudAuditor `
  --region us-east-1 | ConvertFrom-Json | `
  Select-Object -ExpandProperty Summaries | `
  Select-Object Account, Region, Status | `
  Format-Table -AutoSize
```

**Expected Output:**
```
Account      Region    Status
-------      ------    ------
154673468484 us-east-1 CURRENT
740991958584 us-east-1 CURRENT
833277790337 us-east-1 CURRENT
```

**Status Values:**
- `CURRENT` - Stack is up-to-date
- `OUTDATED` - Stack needs update
- `INOPERABLE` - Stack failed to deploy

## Step 7: Test Cross-Account Discovery

Trigger the discovery Lambda to verify cross-account access:

```powershell
aws lambda invoke `
  --function-name cloudauditor-discovery-dev `
  --profile cloudAuditor `
  --region us-east-1 `
  discovery-test.json

# View results
Get-Content discovery-test.json | ConvertFrom-Json
```

**Expected Success:**
```json
{
  "statusCode": 200,
  "body": "{\"success\": true, \"total_resources\": 158, ...}"
}
```

## Step 8: Verify Monitored Accounts

Check which accounts were auto-discovered:

```powershell
aws lambda invoke `
  --function-name cloudauditor-query-dev `
  --profile cloudAuditor `
  --region us-east-1 `
  --payload '{"report_type":"accounts"}' `
  --cli-binary-format raw-in-base64-out `
  accounts.json

Get-Content accounts.json | ConvertFrom-Json
```

## Troubleshooting

### StackSet Already Exists Error

If you get `NameAlreadyExistsException`, the StackSet already exists. Skip to Step 3 to deploy instances.

### No Stack Instances Deployed

If the StackSet exists but has no instances:
1. Verify you're using the correct root OU ID
2. Check that your account has permissions to deploy StackSets
3. Ensure Organizations is properly configured

### Access Denied Errors in Discovery

If discovery fails with `AccessDenied` errors:
1. Verify stack instances are in `CURRENT` status
2. Check that the `HubAccountId` parameter matches your hub account
3. Ensure the Lambda execution role name matches in `spoke-role.yaml` (line 21)

### Stack Instance Failed

If a stack instance shows `INOPERABLE`:
1. Check CloudFormation events in the member account
2. Verify IAM permissions in the member account
3. Delete and recreate the failed instance:

```powershell
# Delete failed instance
aws cloudformation delete-stack-instances `
  --stack-set-name CloudAuditorSpokeRole `
  --accounts <ACCOUNT_ID> `
  --regions us-east-1 `
  --no-retain-stacks `
  --profile cloudAuditor `
  --region us-east-1

# Recreate
aws cloudformation create-stack-instances `
  --stack-set-name CloudAuditorSpokeRole `
  --accounts <ACCOUNT_ID> `
  --regions us-east-1 `
  --profile cloudAuditor `
  --region us-east-1
```

## Auto-Discovery

With `auto-deployment` enabled, the StackSet will automatically:
- Deploy to new accounts added to the Organization
- Remove stacks from accounts removed from the Organization (if `RetainStacksOnAccountRemoval=false`)

The CloudAuditor discovery Lambda will also automatically:
- Detect new Organization member accounts
- Register them in the database
- Attempt to discover resources (once the spoke role is deployed)

## Updating the Spoke Role

To update the spoke role template:

```powershell
# Update StackSet
aws cloudformation update-stack-set `
  --stack-set-name CloudAuditorSpokeRole `
  --template-body file://infrastructure/spoke-role.yaml `
  --parameters ParameterKey=HubAccountId,UsePreviousValue=true `
  --capabilities CAPABILITY_NAMED_IAM `
  --profile cloudAuditor `
  --region us-east-1

# Deploy updates to all instances
aws cloudformation create-stack-instances `
  --stack-set-name CloudAuditorSpokeRole `
  --deployment-targets OrganizationalUnitIds=r-s4nj `
  --regions us-east-1 `
  --operation-preferences MaxConcurrentPercentage=100 `
  --profile cloudAuditor `
  --region us-east-1
```

## Security Considerations

The CloudAuditorExecutionRole has **read-only** permissions:
- `iam:Get*`, `iam:List*`
- `ec2:Describe*`
- `rds:Describe*`
- `s3:GetBucket*`, `s3:List*`
- `resource-explorer-2:*`
- `config:ListDiscoveredResources`
- `cloudcontrol:ListResources`

**No write permissions are granted.** The role can only discover and read resource metadata.

## Next Steps

After successful deployment:
1. ✅ Verify all accounts show `CURRENT` status
2. ✅ Test discovery Lambda
3. ✅ Check monitored accounts in database
4. ✅ Schedule regular discovery runs (already configured for 3 AM UTC daily)
5. ✅ Monitor CloudWatch logs for any errors
