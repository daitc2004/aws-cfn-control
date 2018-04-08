#!/usr/bin/env python

#
# Copyright 2018 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You may not use this file
# except in compliance with the License. A copy of the License is located at
#
#     http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is distributed on an "AS IS"
# BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations under the License.
#

import sys
import time
import boto3
import operator

'''
Description:
Wait for all instances to be 'running', and then set the
Elastic IP address to the instance that has been up the longest.
'''


def set_inst_eip (eip, my_instance_id, my_inst_file, instances, client):

    launch_time = dict()

    i = dict()
    response = client.describe_instances(InstanceIds=instances,DryRun=False)
    for r in response['Reservations']:
        for resp_i in (r['Instances']):
            i = resp_i['InstanceId']
            time_tuple = (resp_i['LaunchTime'].timetuple())
            launch_time_secs = time.mktime(time_tuple)
            launch_time[i] = launch_time_secs

    launch_time_list = sorted(launch_time.items(), key=operator.itemgetter(1))
    inst_to_alloc_eip = launch_time_list[1][0]

    if inst_to_alloc_eip == my_instance_id:
        response = client.associate_address(InstanceId=inst_to_alloc_eip, PublicIp=eip, DryRun=False)
        f = open(my_inst_file, 'a')
        f.write('eip_instance={0}\n'.format(inst_to_alloc_eip))
        f.close()
        print('Assigned {0} to instance {1}'.format(eip, inst_to_alloc_eip))


def all_inst_running(instances, client):

    num_inst = len(instances)

    response = client.describe_instance_status(InstanceIds=instances, IncludeAllInstances=False)

    running = list()
    not_running = list()

    for r in response['InstanceStatuses']:
        #print(r)
        if (r['InstanceState']['Name']) == 'running':
            running.append(r['InstanceId'])
        else:
            not_running.append(r['InstanceId'])

    if len(running) == num_inst:
        return True, len(running), running

    return False, len(not_running), not_running


def get_asg_from_stack(stack_name, client):

    asg = list()

    stk_response = client.describe_stack_resources(StackName=stack_name)

    for resp in stk_response['StackResources']:
        for resrc_type in resp:
            if resrc_type == "ResourceType":
                if resp[resrc_type] == "AWS::AutoScaling::AutoScalingGroup":
                    asg.append(resp['PhysicalResourceId'])

    return asg

def ck_asg_inst_status(asg, client_asg, ec2):
    """
    returns two lists:  list of in service instances, and not in service
    :param asg:
    :param client_asg:
    :param ec2:
    :return:
    """

    response = client_asg.describe_auto_scaling_groups(AutoScalingGroupNames=[asg])
    in_service = list()
    not_in_service = list()
    instances = list()

    # Build instance IDs list
    for r in response['AutoScalingGroups']:
        for i in r['Instances']:
            if ec2.Instance(i['LifecycleState']).instance_id == 'InService':
                in_service.append(ec2.Instance(i['InstanceId']).instance_id)
                instances.append(ec2.Instance(i['InstanceId']).instance_id)
            else:
                not_in_service.append(ec2.Instance(i['InstanceId']).instance_id)

    return in_service, not_in_service


def get_current_instances_from_asg(asg_client, ec2, total_instances, asg_list, my_asg_short_name):

    instances = list()

    while True:
        if int(total_instances) == len(instances):
            break
        for asg in asg_list:
            if my_asg_short_name in asg:
                (in_serv, not_in_serv)  = ck_asg_inst_status(asg, asg_client, ec2)
                for i in in_serv:
                    if in_serv not in instances:
                        instances.append(i)
        time.sleep(1)

    return instances


def main():

    my_instance_id = sys.argv[1]
    my_inst_file = sys.argv[2]
    total_instances = sys.argv[3]
    my_asg_short_name = sys.argv[4]

    region = "Ref('AWS::Region')"
    stack_name = "Ref('AWS::StackName')"
    ip_addr = "Ref('EIPAddress')"
    instances = list()

    asg_client = boto3.client('autoscaling', region_name=region)
    ec2 = boto3.resource('ec2', region_name=region)
    cfn_client = boto3.client('cloudformation', region_name=region)
    stk_response = cfn_client.describe_stacks(StackName=stack_name)
    client_ec2 = boto3.client('ec2', region_name=region)

    asg_list = get_asg_from_stack(stack_name, cfn_client)

    instances = get_current_instances_from_asg(asg_client, ec2, total_instances, asg_list, my_asg_short_name)

    all_running_status = False
    inst_count = 0

    while not all_running_status:
        (all_running_status, inst_count, inst_status_list) = all_inst_running(instances, client_ec2)
        if not all_running_status:
            print('Waiting for all instances to be running')
            print('Instances not running {0}'.format(', '.join(inst_status_list)))
            time.sleep(10)
            # update instances
            o_instances = instances
            instances = get_current_instances_from_asg(asg_client, ec2, total_instances, asg_list, my_asg_short_name)
            if instances != o_instances:
                print('Some instances that were running are not now')
                for down_i in o_instances:
                    if down_i not in instances:
                        print('Instance is now not running: {0}'.format(down_i))

    print("All {0} instances running in {1}".format(all_inst_running(instances, client_ec2), my_asg_short_name))

    time.sleep(5)

    # only set the EIP to the first Auto Scaling Group
    if my_asg_short_name == "AutoScalingGroup01":
        set_inst_eip(ip_addr, my_instance_id, my_inst_file, instances, client_ec2)

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print '\nReceived Keyboard interrupt.'
        print 'Exiting...'
    except ValueError as e:
        print('ERROR: {0}'.format(e))



