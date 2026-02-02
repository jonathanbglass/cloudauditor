# Multi-Account Setup Guide

This guide describes how to configure CloudAuditor to scan multiple AWS accounts within an Organization.

## 🎯 Deployment Modes

### Organization Management Account (Recommended)
When CloudAuditor is deployed in an **Organization Management account**, it automatically:
- Detects all active member accounts
- Auto-registers them in the database
- Scans them on every discovery run

**No manual registration required!** Simply deploy the Spoke Role via StackSets and CloudAuditor handles the rest.

### Standalone/Hub Account
For non-Organization deployments, use `register_account.py` to manually register accounts.

---

## 1. Deploy the Spoke Role
The `CloudAuditorExecutionRole` must be deployed to every member account you wish to scan.

### Via CloudFormation StackSets (Recommended)
1. Use the [spoke-role.yaml](../infrastructure/spoke-role.yaml) template.
2. Parameter `HubAccountId`: Enter your main CloudAuditor account ID.
3. Deploy as a Service-Managed StackSet across your entire Organization or specific OUs.

### Via Terraform
```hcl
resource "aws_iam_role" "cloudauditor_spoke" {
  name = "CloudAuditorExecutionRole"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        AWS = "arn:aws:iam::<HUB_ACCOUNT_ID>:role/cloudauditor-lambda-role-dev"
      }
    }]
  })
}

resource "aws_iam_role_policy" "read_only" {
  name = "CloudAuditorReadOnly"
  role = aws_iam_role.cloudauditor_spoke.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = [
        "iam:Get*", "iam:List*", "ec2:Describe*", "rds:Describe*",
        "resource-explorer-2:Search", "resource-explorer-2:ListIndexes"
      ]
      Effect   = "Allow"
      Resource = "*"
    }]
  })
}
```

## 2. Cross-Account Architecture
CloudAuditor uses a "Hub and Spoke" model:
1. **Hub**: The primary account where the Discovery Lambda lives.
2. **Spoke**: Member accounts containing the resources.

The Hub Lambda performs `sts:AssumeRole` to obtain temporary credentials for each Spoke, then executes discovery as if it were local to that account.

## 4. Registering New Accounts
Once the Spoke Role is deployed, you must register the account in the CloudAuditor database to enable monitoring.

### Using the CLI
Run the `register_account.py` script from the Hub account environment:
```powershell
python register_account.py <ACCOUNT_ID> --name "Production-West"
```

### What happens during registration:
1. **IAM Pre-flight Check**: The script immediately attempts to assume the role in the target account.
2. **Immediate Feedback**: If the check fails, you'll receive specific troubleshooting tips (e.g., checking the Hub ID or role name).
3. **Automatic Discovery**: If the check passes, the account is added to the database and an **initial inventory scan** is triggered immediately.

## 5. Troubleshooting Account Access
If registration fails with `AccessDenied`:
1. **Check Hub ID**: Ensure the `AssumeRolePolicy` in the member account role includes your Hub Account ID.
2. **Role Name**: The default role name is `CloudAuditorExecutionRole`. If you customized it, update the verifier and engine configuration.
3. **Hub Permissions**: Re-verify that the Hub Lambda role has `sts:AssumeRole` on the member account ARN.
