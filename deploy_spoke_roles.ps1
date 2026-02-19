# Deploy CloudAuditorSpokeRole to member accounts via cross-account assume role
# Run from management account (demoFMMBAAdmin profile)

$memberAccounts = @("633605692871", "000277563702")
$hubAccountId = "286861024884"
$templatePath = "infrastructure/spoke-role.yaml"

foreach ($accountId in $memberAccounts) {
    Write-Host "`n=== Deploying to account $accountId ===" -ForegroundColor Cyan
    
    # Assume OrganizationAccountAccessRole in the member account
    $creds = aws sts assume-role `
        --role-arn "arn:aws:iam::${accountId}:role/OrganizationAccountAccessRole" `
        --role-session-name "SpokeRoleDeploy" `
        --profile demoFMMBAAdmin `
        --region us-east-1 `
        --output json | ConvertFrom-Json
    
    if (-not $creds) {
        Write-Host "ERROR: Failed to assume role in account $accountId" -ForegroundColor Red
        continue
    }

    # Set temporary credentials
    $env:AWS_ACCESS_KEY_ID = $creds.Credentials.AccessKeyId
    $env:AWS_SECRET_ACCESS_KEY = $creds.Credentials.SecretAccessKey
    $env:AWS_SESSION_TOKEN = $creds.Credentials.SessionToken

    # Deploy the CloudFormation stack
    Write-Host "Creating CloudFormation stack..."
    aws cloudformation create-stack `
        --stack-name CloudAuditorSpokeRole `
        --template-body "file://$templatePath" `
        --parameters "ParameterKey=HubAccountId,ParameterValue=$hubAccountId" `
        --capabilities CAPABILITY_NAMED_IAM `
        --region us-east-1

    # Wait for completion
    Write-Host "Waiting for stack creation to complete..."
    aws cloudformation wait stack-create-complete `
        --stack-name CloudAuditorSpokeRole `
        --region us-east-1

    if ($LASTEXITCODE -eq 0) {
        Write-Host "SUCCESS: Spoke role deployed to $accountId" -ForegroundColor Green
    } else {
        Write-Host "ERROR: Stack creation failed in $accountId" -ForegroundColor Red
    }

    # Clean up env vars
    Remove-Item Env:AWS_ACCESS_KEY_ID -ErrorAction SilentlyContinue
    Remove-Item Env:AWS_SECRET_ACCESS_KEY -ErrorAction SilentlyContinue
    Remove-Item Env:AWS_SESSION_TOKEN -ErrorAction SilentlyContinue
}

Write-Host "`n=== Deployment Complete ===" -ForegroundColor Cyan
