# CloudAuditor - Quick Start

## 🚀 Deploy in 5 Minutes

### Prerequisites
- GitHub repository with Actions enabled
- AWS account with appropriate permissions
- Strong database password (min 8 characters)

### Step 1: Create S3 Deployment Buckets

GitHub Actions needs S3 buckets to store deployment artifacts:

```bash
# For dev environment (required)
aws s3 mb s3://cloudauditor-artifacts-2026 --region us-east-1
aws s3 mb s3://cloudauditor-sam-deploy-2026 --region us-east-1

# Optional: For staging/prod
aws s3 mb s3://cloudauditor-artifacts-staging --region us-east-1
aws s3 mb s3://cloudauditor-artifacts-prod --region us-east-1
```

### Step 2: Configure GitHub Secrets

1. Go to your GitHub repository
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret** and add each of these:

| Secret Name | Value | Example |
|-------------|-------|---------|
| `AWS_ACCESS_KEY_ID` | Your AWS access key | `AKIAIOSFODNN7EXAMPLE` |
| `AWS_SECRET_ACCESS_KEY` | Your AWS secret key | `wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY` |
| `DB_PASSWORD` | Database master password | `MySecurePass123!` |

**Important:** 
- Password must be at least 8 characters
- Use a strong, unique password
- Don't use special characters that might cause shell issues: `"`, `'`, `` ` ``, `$`, `\`

### Step 3: Trigger Deployment

The workflow automatically deploys when you push to specific branches:

**Deploy to dev environment:**
```bash
git add .
git commit -m "Initial deployment"
git push origin develop
```

**Deploy to production:**
```bash
git push origin main
```

### Step 4: Monitor Deployment

1. Go to **Actions** tab in your GitHub repository
2. Watch the deployment workflow run (~20 minutes)
3. Check for successful completion

**That's it!** The database schema is automatically initialized during deployment.

## Option 2: Local SAM Deployment

1. **Install SAM CLI**
```bash
brew install aws-sam-cli  # macOS
# or
choco install aws-sam-cli  # Windows
```

2. **Build and Deploy**
```bash
sam build
sam deploy --guided
```

3. **Follow Prompts**
   - Stack name: `cloudauditor-dev`
   - Region: `us-east-1`
   - Environment: `dev`
   - DatabaseMasterPassword: `<your-secure-password>`
   
   **Optional parameters** (leave default to auto-create):
   - DatabaseName: `cloudauditor` (default)
   - VpcId: Leave empty to create new VPC
   - AuroraMinCapacity: `0.5` (default)
   - AuroraMaxCapacity: `2` (default)

Done!


## 📋 What Gets Deployed

### Infrastructure
- ✅ **VPC** with public/private subnets (or uses existing VPC)
- ✅ **NAT Gateway** for Lambda internet access
- ✅ **Security Groups** for Lambda and Aurora

### Database
- ✅ **Aurora Serverless v2** PostgreSQL 15.8 cluster (0.5-2 ACUs)
- ✅ **Automatic schema initialization** via Lambda custom resource
- ✅ **Secrets Manager** for database credentials
- ✅ **Data API enabled** for RDS Query Editor access
- ✅ **Automated backups** with 7-day retention

### Compute & Events
- ✅ **4 Lambda Functions**
  - Manager - Orchestrates discovery runs
  - Processor - Processes discovered resources
  - Discovery - Discovers AWS resources
  - DB Init - Initializes database schema automatically
- ✅ **SNS Topic** for inter-Lambda communication
- ✅ **EventBridge Rules** (scheduled triggers)
- ✅ **CloudWatch Logs** with 30-day retention

### Security
- ✅ **IAM Roles** with least-privilege permissions
- ✅ **VPC isolation** for database
- ✅ **Encryption at rest** for Aurora

## 🧪 Test Your Deployment

```bash
# Test Discovery Lambda
aws lambda invoke \
  --function-name cloudauditor-discovery-dev \
  --region us-east-1 \
  --payload '{}' \
  response.json

# View logs
aws logs tail /aws/lambda/cloudauditor-discovery-dev --follow

# Query database (RDS Query Editor)
# The schema is automatically created - just run queries!
SELECT resource_type, COUNT(*) as count 
FROM resources 
GROUP BY resource_type 
ORDER BY count DESC;
```

## 📚 Full Documentation

- [Deployment Guide](docs/DEPLOYMENT.md) - Complete deployment instructions
- [Main README](README.md) - Project overview
- [Resource Discovery](resource_discovery/README.md) - API documentation

## 🆘 Troubleshooting

**Build fails?**
```bash
sam validate  # Check template syntax
python --version  # Should be 3.14
```

**Deployment fails?**
```bash
aws cloudformation describe-stack-events \
  --stack-name cloudauditor-dev
```

**Lambda errors?**
```bash
aws logs tail /aws/lambda/cloudauditor-manager-dev
```

## 💰 Cost Estimate (Dev Environment)

- **Aurora Serverless v2**: ~$50-80/month (scales 0.5-2 ACUs)
- **NAT Gateway**: ~$32/month + data transfer
- **Lambda**: ~$5-10/month (depends on usage)
- **CloudWatch Logs**: ~$1-2/month
- **Secrets Manager**: ~$0.40/month
- **S3**: <$1/month
- **Total**: ~$90-125/month

**Cost Optimization:**
- Use existing VPC to save $32/month (no NAT Gateway)
- Lower Aurora capacity: Set `AuroraMaxCapacity=1` (~$43/month)
- Delete dev stack when not in use

## 🔐 Security Checklist

- [ ] AWS credentials configured
- [ ] GitHub Secrets set (AWS keys + DB password)
- [ ] Database password is strong (min 8 characters)
- [ ] IAM permissions reviewed
- [ ] VPC security groups configured (automatic)
- [ ] Database encryption enabled (automatic)
- [ ] CloudWatch Alarms configured (optional)

## 🎯 Next Steps

1. Deploy to dev environment
2. Test Lambda functions
3. Review CloudWatch Logs
4. Deploy to production when ready
5. Set up monitoring and alerts

---

**Need help?** See [DEPLOYMENT.md](docs/DEPLOYMENT.md) for detailed instructions.
