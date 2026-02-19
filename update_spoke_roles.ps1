# Update CloudAuditorSpokeRole stacks in member accounts with new template (adds Resource Explorer index)
# Run from management account (demoFMMBAAdmin profile)

$memberAccounts = @("633605692871", "000277563702")
$hubAccountId = "286861024884"
$templatePath = "infrastructure/spoke-role.yaml"

foreach ($accountId in $memberAccounts) {
    Write-Host "`n=== Updating stack in account $accountId ===" -ForegroundColor Cyan
    
    # Assume OrganizationAccountAccessRole in the member account
    $creds = aws sts assume-role `
        --role-arn "arn:aws:iam::${accountId}:role/OrganizationAccountAccessRole" `
        --role-session-name "SpokeRoleUpdate" `
        --profile demoFMMBAAdmin `
        --region us-east-1 `
        --output json | ConvertFrom-Json
    
    if (-not $creds) {
        Write-Host "ERROR: Failed to assume role in account $accountId" -ForegroundColor Red
        continue
    }

    $env:AWS_ACCESS_KEY_ID = $creds.Credentials.AccessKeyId
    $env:AWS_SECRET_ACCESS_KEY = $creds.Credentials.SecretAccessKey
    $env:AWS_SESSION_TOKEN = $creds.Credentials.SessionToken

    Write-Host "Updating CloudFormation stack..."
    aws cloudformation update-stack `
        --stack-name CloudAuditorSpokeRole `
        --template-body "file://$templatePath" `
        --parameters "ParameterKey=HubAccountId,ParameterValue=$hubAccountId" `
        --capabilities CAPABILITY_NAMED_IAM `
        --region us-east-1

    Write-Host "Waiting for stack update to complete..."
    aws cloudformation wait stack-update-complete `
        --stack-name CloudAuditorSpokeRole `
        --region us-east-1

    if ($LASTEXITCODE -eq 0) {
        Write-Host "SUCCESS: Stack updated in $accountId" -ForegroundColor Green
    }
    else {
        Write-Host "ERROR: Stack update failed in $accountId" -ForegroundColor Red
    }

    Remove-Item Env:AWS_ACCESS_KEY_ID -ErrorAction SilentlyContinue
    Remove-Item Env:AWS_SECRET_ACCESS_KEY -ErrorAction SilentlyContinue
    Remove-Item Env:AWS_SESSION_TOKEN -ErrorAction SilentlyContinue
}

# Also wait for management account update
Write-Host "`n=== Waiting for management account (399078540411) stack update ===" -ForegroundColor Cyan
aws cloudformation wait stack-update-complete --stack-name CloudAuditorSpokeRole --profile demoFMMBAAdmin --region us-east-1
if ($LASTEXITCODE -eq 0) {
    Write-Host "SUCCESS: Management account stack updated" -ForegroundColor Green
}

Write-Host "`n=== All stacks updated ===" -ForegroundColor Cyan
