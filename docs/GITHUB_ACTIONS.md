# GitHub Actions Deployment Guide

This guide walks you through deploying CloudAuditor using GitHub Actions CI/CD pipeline.

## Overview

The GitHub Actions workflow automatically:
1. Tests and lints your code
2. Builds Lambda functions with SAM
3. Packages and uploads to S3
4. Deploys infrastructure via CloudFormation
5. Runs post-deployment tests

**Deployment Time:** ~20 minutes (first deployment with Aurora)

## Prerequisites

- GitHub repository with Actions enabled
- AWS account with appropriate permissions
- AWS CLI installed locally (for setup only)

## Step-by-Step Deployment

### 1. Create S3 Deployment Buckets

GitHub Actions needs S3 buckets to store deployment artifacts.

```bash
# Required: Dev environment
aws s3 mb s3://cloudauditor-deployments-dev --region us-east-1

# Optional: Additional environments
aws s3 mb s3://cloudauditor-deployments-staging --region us-east-1
aws s3 mb s3://cloudauditor-deployments-prod --region us-east-1
```

**Note:** Bucket names must be globally unique. If these names are taken, use:
```bash
aws s3 mb s3://cloudauditor-deployments-dev-YOURCOMPANY --region us-east-1
```

Then update `.github/workflows/deploy.yml` line 100 with your bucket name.

### 2. Configure GitHub Secrets

#### Navigate to Secrets Settings
1. Open your GitHub repository
2. Click **Settings** (top navigation)
3. Click **Secrets and variables** → **Actions** (left sidebar)
4. Click **New repository secret**

#### Add Required Secrets

Add these three secrets one at a time:

**Secret 1: AWS_ACCESS_KEY_ID**
- Name: `AWS_ACCESS_KEY_ID`
- Value: Your AWS access key (e.g., `AKIAIOSFODNN7EXAMPLE`)
- Click **Add secret**

**Secret 2: AWS_SECRET_ACCESS_KEY**
- Name: `AWS_SECRET_ACCESS_KEY`
- Value: Your AWS secret access key (e.g., `wJalrXUtnFEMI/K7MDENG/bPxRfiCY...`)
- Click **Add secret**

**Secret 3: DB_PASSWORD**
- Name: `DB_PASSWORD`
- Value: Your database master password
- Requirements:
  - Minimum 8 characters
  - Can include: letters, numbers, and special chars: `!@#$%^&*()_+-=[]{};<>?`
  - Avoid: quotes (`"`, `'`), backticks (`` ` ``), dollar signs (`$`), backslashes (`\`)
- Example: `MySecurePass123!`
- Click **Add secret**

#### Verify Secrets
After adding all three, you should see:
- `AWS_ACCESS_KEY_ID` ✓
- `AWS_SECRET_ACCESS_KEY` ✓
- `DB_PASSWORD` ✓

### 3. Trigger Deployment

You have three options to trigger deployment:

#### Option A: Automatic Deployment (Push to Branch)

**Deploy to Dev:**
```bash
git add .
git commit -m "Deploy to dev environment"
git push origin develop
```

**Deploy to Prod:**
```bash
git checkout main
git merge develop
git push origin main
```

The workflow automatically detects the branch:
- `develop` branch → deploys to **dev**
- `main` branch → deploys to **prod**

#### Option B: Manual Deployment (Any Environment)

1. Go to your GitHub repository
2. Click **Actions** tab
3. Click **Deploy CloudAuditor** in the left sidebar
4. Click **Run workflow** button (right side)
5. Select branch: `develop` or `main`
6. Select environment: `dev`, `staging`, or `prod`
7. Click green **Run workflow** button

#### Option C: Pull Request (Test Only)

Opening a PR to `main` runs tests but doesn't deploy:
```bash
git checkout -b feature/my-changes
git push origin feature/my-changes
# Create PR on GitHub
```

### 4. Monitor Deployment Progress

#### View Workflow Execution

1. Go to **Actions** tab in GitHub
2. Click on the running workflow (top of list)
3. Click on the job name to see detailed logs

#### Workflow Stages

The deployment goes through these stages:

**Stage 1: Test and Lint** (~2 minutes)
- ✅ Checkout code
- ✅ Set up Python 3.14
- ✅ Install dependencies
- ✅ Run flake8 linter
- ✅ Run mypy type checker
- ✅ Compile Python files

**Stage 2: Build and Package** (~3 minutes)
- ✅ SAM build (with Docker container)
- ✅ SAM package (upload to S3)
- ✅ Upload packaged template artifact

**Stage 3: Deploy to AWS** (~15 minutes)
- ✅ Download packaged template
- ✅ SAM deploy to CloudFormation
- ✅ Create VPC and networking (~3 min)
- ✅ Create Aurora cluster (~10 min)
- ✅ Create Lambda functions (~2 min)
- ✅ Get stack outputs

**Stage 4: Post-Deployment Tests** (~1 minute)
- ✅ Invoke Manager Lambda
- ✅ Invoke Discovery Lambda
- ✅ Check CloudWatch logs

**Total Time:** ~20 minutes

#### View Deployment Summary

After deployment completes, scroll to the bottom of the workflow to see:
- Environment deployed
- AWS region
- Stack name
- Commit SHA
- **Stack Outputs** (JSON) including:
  - Database endpoint
  - Lambda function ARNs
  - VPC and security group IDs
  - Secrets Manager ARN

### 5. Verify Deployment

#### Check AWS Console

**Lambda Functions:**
1. Open [AWS Lambda Console](https://console.aws.amazon.com/lambda)
2. Look for functions:
   - `cloudauditor-manager-dev`
   - `cloudauditor-processor-dev`
   - `cloudauditor-discovery-dev`

**Aurora Database:**
1. Open [RDS Console](https://console.aws.amazon.com/rds)
2. Click **Databases**
3. Look for cluster starting with `cloudauditor-`
4. Status should be **Available**

**VPC:**
1. Open [VPC Console](https://console.aws.amazon.com/vpc)
2. Look for VPC tagged `cloudauditor-vpc-dev`

#### Test from Command Line

**Test Lambda Function:**
```bash
aws lambda invoke \
  --function-name cloudauditor-manager-dev \
  --payload '{"test": true}' \
  --cli-binary-format raw-in-base64-out \
  response.json

cat response.json
```

**View Logs:**
```bash
aws logs tail /aws/lambda/cloudauditor-manager-dev --follow
```

**Check Database:**
```bash
aws rds describe-db-clusters \
  --query 'DBClusters[?contains(DBClusterIdentifier, `cloudauditor`)].{Name:DBClusterIdentifier,Status:Status,Endpoint:Endpoint}' \
  --output table
```

**Get Stack Outputs:**
```bash
aws cloudformation describe-stacks \
  --stack-name cloudauditor-dev \
  --query 'Stacks[0].Outputs' \
  --output table
```

### 6. Initialize Database

After deployment, initialize the database schema:

1. **Get database endpoint from stack outputs**
2. **Connect to database:**
```bash
# Get credentials from Secrets Manager
aws secretsmanager get-secret-value \
  --secret-id cloudauditor-db-credentials-dev \
  --query SecretString \
  --output text

# Connect with psql (if you have it)
psql -h <endpoint> -U cloudauditor_admin -d cloudauditor
```

3. **Create tables** - See [DATABASE.md](../DATABASE.md) for schema

## Troubleshooting

### Workflow Fails at "Test and Lint"

**Error: Python version not found**
- Check `.github/workflows/deploy.yml` has `python-version: '3.14'`

**Error: flake8 or mypy failures**
- Fix code issues locally first
- Run `flake8 .` and `mypy *.py` before pushing

### Workflow Fails at "SAM Build"

**Error: Docker not available**
- GitHub Actions runners have Docker pre-installed
- Check workflow file has `sam build --use-container`

**Error: Build failed**
- Check `requirements.txt` is valid
- Verify all Python files have correct syntax

### Workflow Fails at "SAM Package"

**Error: S3 bucket does not exist**
```bash
# Create the bucket
aws s3 mb s3://cloudauditor-deployments-dev --region us-east-1
```

**Error: Access Denied**
- Verify AWS credentials in GitHub Secrets
- Check IAM user has S3 permissions: `s3:PutObject`, `s3:GetObject`

### Workflow Fails at "SAM Deploy"

**Error: Invalid parameter: DatabaseMasterPassword**
- Check `DB_PASSWORD` secret is set in GitHub
- Verify password meets requirements (8+ chars)
- Avoid special shell characters: `"`, `'`, `` ` ``, `$`, `\`

**Error: CREATE_FAILED for VPC resources**
- Check AWS account VPC limits
- Default limit: 5 VPCs per region
- Request increase or delete unused VPCs

**Error: CREATE_FAILED for Aurora cluster**
- Check Aurora Serverless v2 is available in your region
- Verify account limits for RDS clusters
- Check for existing clusters with same name

**Error: Insufficient permissions**
- IAM user needs permissions for:
  - CloudFormation: `CreateStack`, `UpdateStack`, `DescribeStacks`
  - Lambda: `CreateFunction`, `UpdateFunctionCode`
  - RDS: `CreateDBCluster`, `CreateDBInstance`
  - EC2: `CreateVpc`, `CreateSubnet`, `CreateSecurityGroup`
  - IAM: `CreateRole`, `AttachRolePolicy`
  - Secrets Manager: `CreateSecret`

### Deployment Succeeds but Lambda Fails

**Check Lambda Logs:**
```bash
aws logs tail /aws/lambda/cloudauditor-manager-dev --since 10m
```

**Common Issues:**
- **Database connection timeout**: Check security groups allow Lambda → Aurora
- **Module import errors**: Verify `requirements.txt` includes all dependencies
- **Environment variable missing**: Check Lambda has `DB_HOST`, `DB_PORT`, etc.

### How to Redeploy

**After fixing issues:**
```bash
git add .
git commit -m "Fix deployment issue"
git push origin develop
```

The workflow automatically triggers again.

**Force redeploy without changes:**
1. Go to **Actions** tab
2. Click **Deploy CloudAuditor**
3. Click **Run workflow**
4. Select environment
5. Click **Run workflow**

## Workflow Configuration

### Customizing the Workflow

Edit `.github/workflows/deploy.yml` to customize:

**Change AWS Region:**
```yaml
env:
  AWS_REGION: us-west-2  # Change from us-east-1
```

**Change S3 Bucket:**
```yaml
- name: SAM Package
  run: |
    sam package \
      --s3-bucket cloudauditor-deployments-YOURCOMPANY-${{ matrix.environment }}
```

**Add Staging Environment:**
```yaml
strategy:
  matrix:
    environment:
      - dev
      - staging  # Add this
      - prod
```

**Change Deployment Schedule:**
Add scheduled deployments:
```yaml
on:
  schedule:
    - cron: '0 2 * * 1'  # Deploy every Monday at 2 AM UTC
```

### Workflow Triggers

Current triggers:
- **Push to `develop`** → Deploy to dev
- **Push to `main`** → Deploy to prod
- **Manual workflow dispatch** → Deploy to any environment
- **Pull request to `main`** → Test only (no deploy)

## Next Steps

1. ✅ Deployment complete
2. ⬜ Initialize database schema - [DATABASE.md](../DATABASE.md)
3. ⬜ Test Lambda functions
4. ⬜ Set up CloudWatch alarms
5. ⬜ Configure EventBridge schedules
6. ⬜ Deploy to production

## Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [AWS SAM CLI Reference](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-command-reference.html)
- [CloudFormation User Guide](https://docs.aws.amazon.com/cloudformation/)
- [Main Deployment Guide](DEPLOYMENT.md)
- [Database Setup Guide](DATABASE.md)

---

**Need Help?** Open an issue in the repository or check the [Troubleshooting](#troubleshooting) section above.
