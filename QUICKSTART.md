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
     - `AWS_ACCESS_KEY_ID`
     - `AWS_SECRET_ACCESS_KEY`
     - `DB_HOST`
     - `DB_NAME`
     - `DB_USER`
     - `DB_PASSWORD`

3. **Create S3 Bucket**
```bash
aws s3 mb s3://cloudauditor-deployments-dev
```

4. **Push to Deploy**
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
   - Enter your database credentials

Done!

## 📋 What Gets Deployed

- ✅ 3 Lambda Functions (Manager, Processor, Discovery)
- ✅ SNS Topic for communication
- ✅ CloudWatch Logs with 30-day retention
- ✅ IAM Roles with least-privilege permissions
- ✅ Scheduled triggers (daily at 2 AM and 3 AM UTC)

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

## 💰 Cost Estimate

- **Lambda**: ~$5-10/month (depends on usage)
- **CloudWatch Logs**: ~$1-2/month
- **S3**: <$1/month
- **Total**: ~$10-15/month

## 🔐 Security Checklist

- [ ] AWS credentials configured
- [ ] GitHub Secrets set
- [ ] Database password is strong
- [ ] IAM permissions reviewed
- [ ] CloudWatch Alarms configured (optional)

## 🎯 Next Steps

1. Deploy to dev environment
2. Test Lambda functions
3. Review CloudWatch Logs
4. Deploy to production when ready
5. Set up monitoring and alerts

---

**Need help?** See [DEPLOYMENT.md](docs/DEPLOYMENT.md) for detailed instructions.
