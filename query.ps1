#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Query CloudAuditor database via Lambda invocation
.DESCRIPTION
    Invokes the cloudauditor-query Lambda function to query the database remotely
.EXAMPLE
    .\query.ps1 -ReportType summary
    .\query.ps1 -ReportType by_type -Limit 20
    .\query.ps1 -Query "SELECT COUNT(*) FROM resources WHERE region='us-east-1'"
#>

param(
    [Parameter()]
    [ValidateSet('summary', 'accounts', 'by_type', 'by_account', 'resources')]
    [string]$ReportType = 'summary',
    
    [Parameter()]
    [string]$Query,
    
    [Parameter()]
    [int]$Limit = 100,
    
    [Parameter()]
    [string]$Profile = 'cloudAuditor',
    
    [Parameter()]
    [string]$Region = 'us-east-1',
    
    [Parameter()]
    [string]$Environment = 'dev'
)

$functionName = "cloudauditor-query-$Environment"

# Build event payload
$event = @{
    report_type = $ReportType
    limit = $Limit
}

if ($Query) {
    $event.query = $Query
    $event.Remove('report_type')
}

$eventJson = $event | ConvertTo-Json -Compress

Write-Host "Invoking Lambda: $functionName" -ForegroundColor Cyan
Write-Host "Report Type: $ReportType" -ForegroundColor Gray

# Invoke Lambda
$outputFile = "query-result-$(Get-Date -Format 'HHmmss').json"
aws lambda invoke `
    --function-name $functionName `
    --profile $Profile `
    --region $Region `
    --payload $eventJson `
    $outputFile | Out-Null

if ($LASTEXITCODE -eq 0) {
    $result = Get-Content $outputFile | ConvertFrom-Json
    
    if ($result.statusCode -eq 200) {
        $body = $result.body | ConvertFrom-Json
        
        Write-Host "`n=== QUERY RESULTS ===" -ForegroundColor Green
        $body.results | ConvertTo-Json -Depth 10 | Write-Host
        
        Write-Host "`nFull response saved to: $outputFile" -ForegroundColor Gray
    } else {
        Write-Host "`nError: $($result.body)" -ForegroundColor Red
        $result | ConvertTo-Json -Depth 5 | Write-Host
    }
} else {
    Write-Host "Failed to invoke Lambda" -ForegroundColor Red
}
