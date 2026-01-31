# CloudAuditor - Quick Start

## 🚀 Deploy in 5 Minutes

### Option 1: GitHub Actions (Recommended)

1. **Fork/Clone Repository**
```bash
git clone <your-repo-url>
cd cloudauditor
```

2. **Set GitHub Secrets**
   - Go to Settings → Secrets → Actions
   - Add these secrets:
     - `AWS_ACCESS_KEY_ID` - Your AWS access key
     - `AWS_SECRET_ACCESS_KEY` - Your AWS secret key
     - `DB_PASSWORD` - Database master password (min 8 characters)

   **Note:** Database infrastructure (Aurora, VPC, etc.) is created automatically!

3. **Push to Deploy**
```bash
git push origin develop  # Deploys to dev
```

Done! Check AWS Lambda console for your functions.

### Option 2: Local SAM Deployment

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
- ✅ **Aurora Serverless v2** PostgreSQL cluster (0.5-2 ACUs)
- ✅ **Secrets Manager** for database credentials
- ✅ **Automated backups** with 7-day retention

### Compute & Events
- ✅ **3 Lambda Functions** (Manager, Processor, Discovery)
- ✅ **SNS Topic** for inter-Lambda communication
- ✅ **EventBridge Rules** (scheduled triggers)
- ✅ **CloudWatch Logs** with 30-day retention

### Security
- ✅ **IAM Roles** with least-privilege permissions
- ✅ **VPC isolation** for database
- ✅ **Encryption at rest** for Aurora

## 🧪 Test Your Deployment

```bash
# Test Manager Lambda
aws lambda invoke \
  --function-name cloudauditor-manager-dev \
  --payload '{"test": true}' \
  response.json

# View logs
aws logs tail /aws/lambda/cloudauditor-manager-dev --follow
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
2. Wait ~15 minutes for Aurora cluster creation
3. Initialize database schema (see [DATABASE.md](docs/DATABASE.md))
4. Test Lambda functions
5. Review CloudWatch Logs
6. Deploy to production when ready
7. Set up monitoring and alerts

---

**Need help?** 
- [DEPLOYMENT.md](docs/DEPLOYMENT.md) - Detailed deployment guide
- [DATABASE.md](docs/DATABASE.md) - Database setup and management
- [DATABASE_AUTOMATION.md](docs/DATABASE_AUTOMATION.md) - Infrastructure overview
