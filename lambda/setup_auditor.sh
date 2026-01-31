#!/bin/sh
S3Bucket=MyAttack
scp jumpserver:/home/ec2-user/iso-iam-auditor.zip .
aws s3 rm s3://iso-acct-audits/iso-iam-auditor.zip
aws s3 cp iso-iam-auditor.zip s3://iso-acct-audits/
aws lambda delete-function --region us-east-1 --function-name iso-iam-auditor-mgr
aws lambda create-function --region us-east-1 --function-name iso-iam-auditor-mgr --code S3Bucket=iso-acct-audits,S3Key=iso-iam-auditor.zip --role arn:aws:iam::987569341137:role/isoAuditOnlyInstanceRole --handler manager.lambda_handler --runtime python3.14 --timeout 120 --memory-size 512 --vpc-config SubnetIds=subnet-a165c0fa,subnet-58993875,SecurityGroupIds=sg-a141c2de --environment Variables={"dbhost='iso-prod-isodb.c20dabuuv4ab.us-east-1.rds.amazonaws.com',dbname='isodb',dbuser='isodbadmin',dbpass='UQPU4kTj3MRemZyh'"}
aws lambda delete-function --region us-east-1 --function-name iso-iam-auditor-proc
aws lambda create-function --region us-east-1 --function-name iso-iam-auditor-proc --code S3Bucket=iso-acct-audits,S3Key=iso-iam-auditor.zip --role arn:aws:iam::987569341137:role/isoAuditOnlyInstanceRole --handler processor.lambda_handler --runtime python3.14 --timeout 120 --memory-size 512 --vpc-config SubnetIds=subnet-a165c0fa,subnet-58993875,SecurityGroupIds=sg-a141c2de --environment Variables={"dbhost='iso-prod-isodb.c20dabuuv4ab.us-east-1.rds.amazonaws.com',dbname='isodb',dbuser='isodbadmin',dbpass='UQPU4kTj3MRemZyh'"}
aws lambda add-permission --function-name iso-iam-auditor-proc \
  --region us-east-1 \
  --statement-id Id-123 \
  --action "lambda:InvokeFunction" \
  --principal sns.amazonaws.com \
	--source-arn arn:aws:sns:us-east-1:987569341137:iso-cloud-auditor
aws events put-rule \
  --region us-east-1 \
--name iso-cloud-auditor-scheduled-rule \
--schedule-expression 'cron(5 0 * * ? *)'
aws lambda add-permission \
  --region us-east-1 \
--function-name iso-iam-auditor-mgr \
--statement-id iso-cloud-auditor-scheduled-event \
--action 'lambda:InvokeFunction' \
--principal events.amazonaws.com \
--source-arn arn:aws:events:us-east-1:987569341137:rule/iso-cloud-auditor-scheduled-rule
aws events put-targets --region us-east-1 --rule iso-cloud-auditor-scheduled-rule --targets file://targets.json
