import json
import cfnresponse
import boto3
def handler(event, context):
  app_asg_client = boto3.client('application-autoscaling')
  if event["RequestType"] == "Delete":
    try:
      app_asg_client.delete_policy(
        PolicyName = event['ResourceProperties']['PolicyName'],
        ServiceNamespace = 'dynamodb',
        ResourceId = event['ResourceProperties']['ResourceId'],
        ScalableDimension = event['ResourceProperties']['ScalableDimension']
      )
    finally:
      cfnresponse.send(event, context, cfnresponse.SUCCESS, {"Result": "Delete"},event["LogicalResourceId"])
    return
  print("Received event: " + json.dumps(event, indent=2))

  try:
    target_tracking_scaling_configuration = event['ResourceProperties']['TargetTrackingScalingPolicyConfiguration']
    target_tracking_scaling_configuration['TargetValue'] = float(target_tracking_scaling_configuration['TargetValue'])
    target_tracking_scaling_configuration['ScaleOutCooldown'] = int(target_tracking_scaling_configuration['ScaleOutCooldown'])
    target_tracking_scaling_configuration['ScaleInCooldown'] = int(target_tracking_scaling_configuration['ScaleInCooldown'])
    put_policy_response = app_asg_client.put_scaling_policy(
      PolicyName = event['ResourceProperties']['PolicyName'],
      ServiceNamespace = 'dynamodb',
      ResourceId = event['ResourceProperties']['ResourceId'],
      PolicyType = 'TargetTrackingScaling',
      ScalableDimension = event['ResourceProperties']['ScalableDimension'],
      TargetTrackingScalingPolicyConfiguration = target_tracking_scaling_configuration
    )
    print(put_policy_response)
    cfnresponse.send(event, context, cfnresponse.SUCCESS,put_policy_response,event["LogicalResourceId"])
  except Exception as e:
    print "Error: {0}".format(str(e))
    cfnresponse.send(event,context,cfnresponse.FAILED, {"Error":str(e)},event["LogicalResourceId"])