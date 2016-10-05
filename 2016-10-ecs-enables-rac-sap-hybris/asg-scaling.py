import botocore.session
import boto3
import json

session = botocore.session.get_session()
ecs = session.create_client('ecs')
ec2 = session.create_client('ec2')
autoscaling = session.create_client('autoscaling')
DEBUG = True


def get_container_instances(ecs_cluster_name):
    list_container_instance_arns = ecs.list_container_instances(
        cluster=ecs_cluster_name
    )["containerInstanceArns"]

    container_instances = ecs.describe_container_instances(
        cluster=ecs_cluster_name,
        containerInstances=list_container_instance_arns
    )["containerInstances"]

    ec2_instance_ids = []
    for instance in container_instances:
        ec2_instance_ids.append(instance["ec2InstanceId"])

    if DEBUG:
        print "ECS_INSTANCE_COUNT: ", len(ec2_instance_ids)
    return ec2_instance_ids

def get_services(ecs_cluster_name):
    return ecs.list_services(
        cluster=ecs_cluster_name
    )["serviceArns"]


def get_asg_name(instances):
    asg_names = []
    for instance in instances:
        tag_value = ec2.describe_tags(
                Filters=[
                    {
                        'Name': 'resource-id',
                        'Values': [
                            instance
                        ]
                    },
                    {
                        'Name': 'key',
                        'Values': [
                            "aws:autoscaling:groupName"
                        ]
                    }
                ],
            )["Tags"][0]["Value"]
        if tag_value not in asg_names:
            asg_names.append(tag_value)
    if len(asg_names) != 1:
        raise ValueError('Lambda function supports only one AutoScaling group for single ECS cluster')
    if DEBUG:
        print "ASG_NAME: ", asg_names[0]
    return asg_names[0]

def get_asg_params(asg_name):
    asg_description = autoscaling.describe_auto_scaling_groups(
        AutoScalingGroupNames=[
            asg_name
        ]
    )["AutoScalingGroups"][0]
    min_size = asg_description['MinSize']
    max_size = asg_description['MaxSize']
    desired_capacity = asg_description['DesiredCapacity']

    if DEBUG:
        print "ECS MIN, MAX, DESIRED: ", min_size, max_size, desired_capacity

    return min_size, max_size, desired_capacity

def get_ecs_max_task_desired_count(ecs_cluster_name,ecs_services):
    desired_counts = []
    for i in  ecs.describe_services(
        cluster=ecs_cluster_name,
        services=ecs_services
    )['services']:
        desired_counts.append(i['desiredCount'])
    if DEBUG:
        print "MAX_TASK_DESIRED_COUNT: ", max(desired_counts)
    return max(desired_counts)



def asg_scaling(asg, min_extra_capacity, max_extra_capacity):
#reserved_instances

    ecs_instances = get_container_instances(asg)

    ecs_services = get_services(asg)

    asg_name = get_asg_name(ecs_instances)

    max_desired_count = get_ecs_max_task_desired_count(asg, ecs_services)

    ##Get asg current desired capacity
    response = autoscaling.describe_auto_scaling_groups(AutoScalingGroupNames=[asg_name])
    current_asg_desired_capacity = response['AutoScalingGroups'][0]['DesiredCapacity']
    asg_min_capacity = response['AutoScalingGroups'][0]['MinSize']
    asg_max_capacity = response['AutoScalingGroups'][0]['MaxSize']

    if current_asg_desired_capacity < (max_desired_count + min_extra_capacity) :
        total_instances = max_desired_count + min_extra_capacity
    elif current_asg_desired_capacity > max_desired_count + max_extra_capacity:
        total_instances = max_desired_count + max_extra_capacity
    else:
        total_instances = current_asg_desired_capacity

    if total_instances > asg_max_capacity:
        total_instances = asg_max_capacity
    elif total_instances < asg_min_capacity:
        total_instances = asg_min_capacity

    if total_instances != len(ecs_instances):
        response = autoscaling.update_auto_scaling_group(
            AutoScalingGroupName=asg_name,
            DesiredCapacity=total_instances
        )
    else:
        response = "Nothing changed"
    if DEBUG:
        print "RESPONSE: ", str(response)
    return response



def lambda_handler(event,context):
    #event = {"ECSClusters": ["ECSClusterName-XXXXXXX"],MinExtraCapacity: 2, MaxExtraCapacity: 2}
    message = {}
    if DEBUG:
        print "EVENT: ", event
    for asg in event["ECSClusters"]:
        message[asg] = asg_scaling(asg, event["MinExtraCapacity"], event["MaxExtraCapacity"])

    return message
