# Virtual Environment Setup & Usage Guide

## Initial Setup

I've created a Python virtual environment for you with all required dependencies installed.

### What was installed:
- `boto3` - AWS SDK
- `psycopg[binary]` - PostgreSQL database adapter
- `pandas` - Data analysis
- `openpyxl` - Excel file generation
- `beautifulsoup4` - HTML parsing

## How to Use

### Activate the Virtual Environment

**Every time** you want to run CloudAuditor scripts, activate the virtual environment first:

```powershell
# Activate the virtual environment
.\venv\Scripts\Activate.ps1

# You should see (venv) in your prompt
```

### Run Scripts

Once activated, you can run any CloudAuditor script:

```powershell
# Query the database
python query_database.py --summary

# Run one-off discovery
python main.py --accounts 123456789012 --format excel

# Register an account
python register_account.py 123456789012 --name "My Account"
```

### Deactivate When Done

```powershell
deactivate
```

## AWS Profile Configuration

The `query_database.py` script uses the `DatabaseClient` which needs AWS credentials to fetch the database password from Secrets Manager.

Make sure you have your AWS profile configured:

```powershell
# Set your AWS profile
$env:AWS_PROFILE = "cloudAuditor"

# Or use the --profile flag with AWS CLI commands
```

## Troubleshooting

### "ModuleNotFoundError: No module named 'boto3'"
- Make sure you activated the virtual environment: `.\venv\Scripts\Activate.ps1`
- Look for `(venv)` in your prompt

### "Error querying database: 'password'"
- Ensure your AWS credentials are configured
- Set the AWS profile: `$env:AWS_PROFILE = "cloudAuditor"`
- The script needs access to AWS Secrets Manager to get the database password

### Execution Policy Error
If you get an error about execution policies when activating:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## Quick Reference

```powershell
# Full workflow example:
.\venv\Scripts\Activate.ps1
$env:AWS_PROFILE = "cloudAuditor"
python query_database.py --summary --by-type
deactivate
```
