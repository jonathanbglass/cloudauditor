# CloudAuditor - Generate Excel Report from Database
# This script invokes the report generator Lambda and downloads the Excel file

param(
    [string]$Profile = "cloudAuditor",
    [string]$Region = "us-east-1",
    [string]$OutputFile = "reports\CloudAuditor_Assets_Latest.xlsx"
)

Write-Host "`n========================================" -ForegroundColor Green
Write-Host "  CloudAuditor Excel Report Generator" -ForegroundColor Green
Write-Host "========================================`n" -ForegroundColor Green

# Create reports directory if it doesn't exist
if (!(Test-Path "reports")) {
    New-Item -ItemType Directory -Path "reports" | Out-Null
}

# Invoke the Lambda function
Write-Host "Generating Excel report from Aurora database..." -ForegroundColor Cyan
aws lambda invoke `
    --function-name cloudauditor-report-generator-dev `
    --profile $Profile `
    --region $Region `
    report-result.json | Out-Null

# Parse the result
$result = Get-Content report-result.json | ConvertFrom-Json
$body = $result.body | ConvertFrom-Json

if ($body.success) {
    Write-Host "`n✅ Report Generated Successfully!`n" -ForegroundColor Green
    Write-Host "  Resources: $($body.resource_count)" -ForegroundColor White
    Write-Host "  S3 Bucket: $($body.s3_bucket)" -ForegroundColor White
    Write-Host "  S3 Key: $($body.s3_key)" -ForegroundColor White
    
    # Download the report
    Write-Host "`nDownloading Excel file..." -ForegroundColor Cyan
    Invoke-WebRequest -Uri $body.download_url -OutFile $OutputFile
    
    Write-Host "`n✅ Report Downloaded!`n" -ForegroundColor Green
    Write-Host "  Location: $OutputFile" -ForegroundColor White
    Write-Host "  Size: $((Get-Item $OutputFile).Length / 1KB) KB" -ForegroundColor White
    
    # Open the file
    Write-Host "`nOpening Excel file..." -ForegroundColor Cyan
    Start-Process $OutputFile
    
}
else {
    Write-Host "`n❌ Report Generation Failed`n" -ForegroundColor Red
    Write-Host "  Error: $($body.error)" -ForegroundColor Red
}

# Clean up temp file
Remove-Item report-result.json -ErrorAction SilentlyContinue

Write-Host "`n========================================`n" -ForegroundColor Green
