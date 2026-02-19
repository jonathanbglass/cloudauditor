$query = @"
ALTER TABLE resources ADD COLUMN IF NOT EXISTS inserted_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW();
CREATE INDEX IF NOT EXISTS idx_resources_inserted ON resources(inserted_at DESC);
"@

$payload = @{
    query = $query
} | ConvertTo-Json

aws lambda invoke `
    --function-name cloudauditor-query-dev `
    --profile cloudAuditor `
    --region us-east-1 `
    --payload $payload `
    query-result.json

Get-Content query-result.json | ConvertFrom-Json
