# Enabling AWS Resource Explorer for CloudAuditor & FleetMarshal

CloudAuditor and FleetMarshal rely on [AWS Resource Explorer](https://docs.aws.amazon.com/resource-explorer/latest/userguide/welcome.html) to discover resources across all member accounts in your AWS Organization. Each member account must have a **LOCAL** Resource Explorer index for the discovery engine to inventory its resources.

This guide walks you through enabling Resource Explorer Organization-wide so that all **current and future** member accounts are automatically configured.

## Prerequisites

- Access to your **AWS Organizations management account**
- AWS CLI v2 installed and configured
- The Organization must have [all features enabled](https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_org_support-all-features.html)

## Step 1 — Enable Trusted Access

Resource Explorer requires [trusted access](https://docs.aws.amazon.com/resource-explorer/latest/userguide/getting-started-setting-up-prereqs.html) with AWS Organizations to operate across member accounts.

Run from the **management account**:

```bash
aws organizations enable-aws-service-access \
  --service-principal resource-explorer-2.amazonaws.com
```

Verify it's enabled:

```bash
aws organizations list-aws-service-access-for-organization \
  --query "EnabledServicePrincipals[?ServicePrincipal=='resource-explorer-2.amazonaws.com']"
```

> **Reference:** [Setting up Resource Explorer for multi-account search](https://docs.aws.amazon.com/resource-explorer/latest/userguide/getting-started-setting-up.html)

## Step 2 — Deploy LOCAL Indexes via StackSet

Use the included CloudFormation template ([`resource-explorer-index.yaml`](infrastructure/resource-explorer-index.yaml)) to create a LOCAL Resource Explorer index in every member account.

### 2a. Create the StackSet

```bash
aws cloudformation create-stack-set \
  --stack-set-name ResourceExplorerIndex \
  --template-body file://infrastructure/resource-explorer-index.yaml \
  --permission-model SERVICE_MANAGED \
  --auto-deployment Enabled=true,RetainStacksOnAccountRemoval=false \
  --region us-east-1
```

The `SERVICE_MANAGED` permission model uses [AWS Organizations integration](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/stacksets-orgs.html), and `auto-deployment` ensures new accounts automatically receive a Resource Explorer index.

### 2b. Deploy to Your Root OU

Find your Root OU ID:

```bash
aws organizations list-roots --query "Roots[0].Id" --output text
```

Deploy stack instances:

```bash
aws cloudformation create-stack-instances \
  --stack-set-name ResourceExplorerIndex \
  --deployment-targets OrganizationalUnitIds=<ROOT_OU_ID> \
  --regions us-east-1 \
  --region us-east-1
```

### 2c. Monitor Deployment

```bash
aws cloudformation describe-stack-set-operation \
  --stack-set-name ResourceExplorerIndex \
  --operation-id <OPERATION_ID> \
  --region us-east-1 \
  --query "StackSetOperation.Status"
```

Wait until the status is `SUCCEEDED`.

## Step 3 — Create an Aggregator Index (Optional)

If you want a single query point that searches across all accounts and regions, designate one account/region as the [aggregator](https://docs.aws.amazon.com/resource-explorer/latest/userguide/getting-started-setting-up.html):

```bash
aws resource-explorer-2 update-index-type \
  --arn <LOCAL_INDEX_ARN> \
  --type AGGREGATOR \
  --region us-east-1
```

> **Note:** Only one aggregator index is allowed per Organization. CloudAuditor's hub account typically holds this aggregator.

## Step 4 — Verify

Trigger a CloudAuditor discovery scan:

```bash
aws lambda invoke \
  --function-name cloudauditor-discovery-dev \
  --profile cloudAuditor \
  response.json
```

Then check resource counts per account:

```bash
aws lambda invoke \
  --function-name cloudauditor-query-dev \
  --profile cloudAuditor \
  --payload '{"report_type":"by_account"}' \
  --cli-binary-format raw-in-base64-out \
  response.json
```

All accounts should now report non-zero resource counts.

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `ResourceExplorer=False` in discovery logs | No LOCAL index in account | Deploy the StackSet to that account's OU |
| `AccessDenied` on `CreateIndex` | Spoke role lacks permissions | Add `resource-explorer-2:*` to the spoke role policy |
| Account shows 0 resources after index creation | Index is still populating | Wait 5–10 minutes for initial indexing |
| StackSet deployment `FAILED` in management account | Index already exists | Expected — the management account may already have an index; other member accounts should succeed |

## References

- [AWS Resource Explorer User Guide](https://docs.aws.amazon.com/resource-explorer/latest/userguide/welcome.html)
- [Setting up multi-account search](https://docs.aws.amazon.com/resource-explorer/latest/userguide/getting-started-setting-up.html)
- [CloudFormation StackSets with Organizations](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/stacksets-orgs.html)
- [Resource Explorer CloudFormation resource type](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-resourceexplorer2-index.html)
