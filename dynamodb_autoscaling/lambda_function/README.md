## Lambda function for Dynamodb autoscaling custom resource

The lambda function is dependent on the latest version of botocore library ( version 1.5.68 or later). At the time of this writing this library is not yet available in the lambda runtime container, one has to include it explicitly in the lambda package. 

### How to create lambda deployment package
```
#change to the current directory
cd blog-code-samples/dynamodb_autoscaling/lambda_function
pip install boto3 -t /.
zip -r dynamodb_autoscaling.zip .
```

### Upload the file to an s3 bucket 
`aws s3 cp dynamodb_autoscaling.zip s3://<s3_bucket_name>/lambda_functions/dynamodb_autoscaling.zip`