# autoAlarm
CloudFormation Template for deploying CloudFormation Macro which generates &amp; deploys Invocations, Errors &amp; Throttles Alarms for the Lambda functions
The default Threshold values for Invocations, Errors and Throttles is 5. You can change the values from ***alarm_macro.py***. Also the default SNS Topic is ***monitorBottleLambdaBottleIOT***. You can replace with your own Monitoring Topic ARN from ***MacroTemplate.yaml***. Instructions are provided as comments in the code.

***To deploy this stack*** :
- You need to create an S3 bucket, To create the bucket run the following command :
```
aws s3api create-bucket --bucket <BucketName> --region <RegionOfChoice>
```
- Then You've to package the template and put it to s3. To do so run the following command : 
```
aws cloudformation package --template-file MacroTemplate.yml --s3-bucket <YourBucketName> --output-template-file packaged-template.yaml
```

- Now you deploy the CloudFormation Stack using the following command : 
```
aws cloudformation deploy --template-file packaged-template.yaml --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM CAPABILITY_AUTO_EXPAND --stack-name <CFStackName> --region <RegionOfChoice>
```

#### After deployment is succesful : 
Once the stack is deployed, you can just paste ***Transform: AlarmMacro*** in the ***resources*** section [Not Resources] of your Lambda function and Alarms will be created automatically for your Lambda Function.

***To delete a created S3 Bucket***, Execute the following command :
```
aws s3api delete-bucket --bucket <YourBucketName> --region <Region>
```

***To delete the created CloudFormation Stack***, Execute the following command :
```
aws cloudformation delete-stack --stack-name <YourStackName> --region <Region>
```