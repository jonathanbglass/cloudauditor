# iso-cloud-auditor

# Documentation
## Requirements
* Postgresql Database Endpoint
* Postgresql User with SELECT, INSERT, and UPDATE rights
* Tables as defined in create_tables.sql
* pycopg2 module
* boto3 module
* Script must run in EC2 with instance role allowing access to STS:AssumeRole
* Policy must permit sts:assumerole for each remote account: see example_iam_policy.json
## Use
    $ python auditor.py (default is Audit All Accounts)
    $ python auditor.py -h 

# LAMBDA Use
* See the cloud-auditor/lambda/ directory
* iso-cloud-auditor/lambda/setup_auditor.sh
** adjust the setup_auditor.sh script for your environment
** written to pull files from development server via scp
** deletes existing LAMBDAs
** creates new LAMBDAs with the same name
** handles permissions for SNS topics / notification to processor lambda
* iso-cloud-auditor/manager.py - 
** checks the database for Cross Account Roles
** creates messages in an SNS topic
** one message for EACH account, and EACH Process ITEM
** ie, Account #, ARN, process_users
* iso-cloud-auditor/processor.py
** receives the SNS notification (see setup_auditor.sh for required permissions)
** runs the requested "process" against the given account using the cross account role ARN

# Auditor Design Notes & Roadmap

## Data Sources
* AWS API - Primary 
* CloudHealthTech API
* Alert Logic API
* Kubernetes APIs

### AWS API
* Collect Data from AWS 
  * start with a single account - DONE 12/22/2016
  * Use Python so it can be deployed in LAMBDA
  * Collect Users, Groups, Roles, and Policy details - DONE 2/2/2017
  	* Users -
    * Groups - 
    * Roles - 
    * Policies - 
  * Loop through every ARN in aws_cross_account_arn ISODB table and collect this data - DONE 2/2/2017       
	* Collect each data set as a separate thread to speed up processing - LOW PRIORITY
	* Restrict to Attached policies only - DONE 1/2/2017
* Store Data in Database - 
	* Convert data into SQL statement - DONE 12/22/2016
	* Connect to PGSQL ISODB - DONE 12/22/2016
	* Insert rows to begin with
	  * Update on Insert to minimize database work: 
	  * match on {RoleID, UserID, PolicyID, GroupID}, CreateDate and UpdateDate; 
	  * If no change, just update Last Audited TimeStamp
	* Close DB connection - DONE 1/2/2017
* Figure out how to get pycopg2 to work in AWS LAMBDA 
* Display the data
	* First, just display the data
	* Add filtering/sorting options
	* Add authentication
	* Enforce RBAC 
		* Make sure every record has an Account ID field for RBAC perms tracking
* Interact with the Data
	* Provide an Account Audit Report for Account Owners
		* Give the option to flag certain accounts for deletion/disabling - after RBAC
	* Provide 
* Archive the Data - 
	* Figure out how to archive data for long-term forensics 

## Reports
* User & Permission audit report
  * Business Units/Managers must approve the list of users and their level of access once a quarter
  * Provide a mechanism to SEE AWS users and permissions
  * Provide a mechanism to FLAG/DISABLE users
* Accounts Security Overview
  * RYG icons for each security tool/service per account
  * RYG icons for each security best practice/recommendation 
    * See CSA CCM Guidelines
* Accounts Overview
  * Billing information for each AWS account
  * Account Owners for each account
  * Support Team responsible for each account
  * Security Contact for each account
  
