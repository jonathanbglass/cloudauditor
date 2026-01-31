# CloudAuditor Deployment Guide

Complete guide for deploying CloudAuditor using AWS SAM and GitHub Actions.

## Architecture

```
GitHub Repository
       ↓
GitHub Actions (CI/CD)
       ↓
AWS SAM Build & Package
       ↓
CloudFormation Stack
       ↓
┌──────────────────────────────────────┐
│  Lambda Functions                    │
│  - Manager (IAM Auditing)           │
│  - Processor (Data Processing)      │
│  - Discovery (Resource Discovery)   │
└──────────────────────────────────────┘
       ↓
PostgreSQL Database
```

## Prerequisites

### 1. AWS Account Setup

- AWS Account with appropriate permissions
- S3 buckets for deployment artifacts (one per environment):
  - `cloudauditor-deployments-dev`
  - `cloudauditor-deployments-staging`
  - `cloudauditor-deployments-prod`

### 2. GitHub Repository Setup

Configure the following GitHub Secrets:

| Secret Name | Description | Example |
|-------------|-------------|---------|
| `AWS_ACCESS_KEY_ID` | AWS access key | `AKIAIOSFODNN7EXAMPLE` |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key | `wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY` |
| `DB_HOST` | Database hostname | `db.example.com` |
| `DB_NAME` | Database name | `cloudauditor` |
| `DB_USER` | Database username | `cloudauditor_user` |
| `DB_PASSWORD` | Database password | `SecurePassword123!` |

**To add secrets:**
1. Go to repository Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Add each secret above

### 3. Local Development Setup

Install AWS SAM CLI:

```bash
# macOS
brew install aws-sam-cli

# Windows
choco install aws-sam-cli

# Linux
pip install aws-sam-cli
```

## Deployment Methods

### Method 1: Automated Deployment (GitHub Actions)

**Recommended for production use**

#### Deploy to Dev (automatic)
```bash
git checkout develop
git add .
git commit -m "Your changes"
git push origin develop
```

#### Deploy to Prod (automatic)
```bash
git checkout main
git merge develop
git push origin main
```

#### Manual Deployment via GitHub UI
1. Go to Actions tab
2. Select "Deploy CloudAuditor" workflow
3. Click "Run workflow"
4. Select environment (dev/staging/prod)
5. Click "Run workflow"

### Method 2: Local Deployment (SAM CLI)

**Recommended for development and testing**

#### First-time Setup

1. **Create S3 bucket for deployments:**
```bash
aws s3 mb s3://cloudauditor-deployments-dev --region us-east-1
```

2. **Build the application:**
```bash
sam build
```

3. **Deploy with guided setup:**
```bash
sam deploy --guided
```

Follow the prompts:
- Stack Name: `cloudauditor-dev`
- AWS Region: `us-east-1`
- Parameter Environment: `dev`
- Parameter DatabaseHost: `your-db-host`
- Parameter DatabaseName: `cloudauditor`
- Parameter DatabaseUser: `cloudauditor_user`
- Parameter DatabasePassword: `your-password`
- Confirm changes before deploy: `Y`
- Allow SAM CLI IAM role creation: `Y`
- Save arguments to configuration file: `Y`

#### Subsequent Deployments

```bash
# Build
sam build

# Deploy to dev
sam deploy --config-env dev

# Deploy to staging
sam deploy --config-env staging

# Deploy to prod
sam deploy --config-env prod
```

## Testing Deployments

### Local Testing

```bash
# Test locally with SAM
sam local invoke ManagerFunction --event events/test-event.json

# Start local API (if you add API Gateway later)
sam local start-api
```

### Remote Testing

```bash
# Invoke Manager Lambda
aws lambda invoke \
  --function-name cloudauditor-manager-dev \
  --payload '{"test": true}' \
  response.json

# Invoke Discovery Lambda
aws lambda invoke \
  --function-name cloudauditor-discovery-dev \
  --payload '{"test": true}' \
  response.json

# View logs
aws logs tail /aws/lambda/cloudauditor-manager-dev --follow
```

## CI/CD Pipeline

The GitHub Actions workflow includes:

### 1. Test Stage
- Python syntax checking
- Linting with flake8
- Type checking with mypy
- Compile all Python files

### 2. Build & Package Stage
- SAM build with container
- Package Lambda functions
- Upload to S3
- Create packaged template

### 3. Deploy Stage
- Deploy CloudFormation stack
- Update Lambda functions
- Configure environment variables
- Create/update IAM roles

### 4. Post-Deploy Tests
- Invoke Lambda functions
- Check CloudWatch logs
- Verify deployment

## Environment Configuration

### Development (dev)
- Triggered by: Push to `develop` branch
- Stack: `cloudauditor-dev`
- Schedule: Manual or on push

### Staging (staging)
- Triggered by: Manual workflow dispatch
- Stack: `cloudauditor-staging`
- Schedule: Manual only

### Production (prod)
- Triggered by: Push to `main` branch
- Stack: `cloudauditor-prod`
- Schedule: Daily at 2 AM UTC (Manager), 3 AM UTC (Discovery)

## Monitoring

### CloudWatch Logs

```bash
# View Manager logs
aws logs tail /aws/lambda/cloudauditor-manager-dev --follow

# View Processor logs
aws logs tail /aws/lambda/cloudauditor-processor-dev --follow

# View Discovery logs
aws logs tail /aws/lambda/cloudauditor-discovery-dev --follow
```

### CloudWatch Metrics

Monitor in AWS Console:
- Lambda → Functions → Select function → Monitoring
- Key metrics:
  - Invocations
  - Duration
  - Errors
  - Throttles

### CloudWatch Alarms (Optional)

Create alarms for:
- Lambda errors > 5 in 5 minutes
- Lambda duration > 100 seconds
- Lambda throttles > 0

## Rollback

### Automatic Rollback
CloudFormation automatically rolls back on deployment failure.

### Manual Rollback

```bash
# List stack events
aws cloudformation describe-stack-events \
  --stack-name cloudauditor-dev

# Rollback to previous version
aws cloudformation cancel-update-stack \
  --stack-name cloudauditor-dev
```

### Rollback via GitHub
1. Revert the commit that caused issues
2. Push to trigger redeployment

## Updating the Stack

### Update Lambda Code Only

```bash
sam build
sam deploy --config-env dev
```

### Update Infrastructure

1. Modify `template.yaml`
2. Commit and push
3. GitHub Actions will deploy changes

### Update Dependencies

1. Modify `requirements.txt`
2. SAM will automatically package new dependencies

## Troubleshooting

### Build Failures

```bash
# Clean build
rm -rf .aws-sam
sam build --use-container

# Check Python version
python --version  # Should be 3.14

# Validate template
sam validate
```

### Deployment Failures

```bash
# Check CloudFormation events
aws cloudformation describe-stack-events \
  --stack-name cloudauditor-dev \
  --max-items 20

# Check stack status
aws cloudformation describe-stacks \
  --stack-name cloudauditor-dev
```

### Lambda Errors

```bash
# Check recent errors
aws logs filter-pattern /aws/lambda/cloudauditor-manager-dev \
  --filter-pattern "ERROR" \
  --start-time $(date -u -d '1 hour ago' +%s)000

# Test function locally
sam local invoke ManagerFunction
```

## Cost Optimization

- **Lambda**: Pay per invocation and duration
- **CloudWatch Logs**: 30-day retention (configurable)
- **S3**: Minimal storage for deployment artifacts
- **Estimated monthly cost**: $5-20 depending on usage

## Security Best Practices

1. **Secrets Management**
   - Use GitHub Secrets for sensitive data
   - Rotate credentials regularly
   - Use AWS Secrets Manager for production

2. **IAM Permissions**
   - Principle of least privilege
   - Separate roles per function
   - Regular permission audits

3. **Network Security**
   - Deploy in VPC if accessing private resources
   - Use Security Groups
   - Enable VPC Flow Logs

4. **Monitoring**
   - Enable CloudTrail
   - Set up CloudWatch Alarms
   - Review logs regularly

## Next Steps

1. ✅ Set up GitHub Secrets
2. ✅ Create S3 deployment buckets
3. ✅ Test local deployment with SAM
4. ✅ Push to `develop` branch to trigger first deployment
5. ✅ Verify Lambda functions in AWS Console
6. ✅ Test scheduled execution
7. ✅ Set up CloudWatch Alarms
8. ✅ Deploy to production

## Support

For issues:
1. Check CloudWatch Logs
2. Review CloudFormation events
3. Consult [AWS SAM Documentation](https://docs.aws.amazon.com/serverless-application-model/)
4. Review GitHub Actions logs
