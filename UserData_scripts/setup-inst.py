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
import logging
import operator

'''
Description:
Wait for all instances to be 'running', and then set the
Elastic IP address to the instance that has been up the longest.
'''

progname = 'setup-inst'


def set_inst_eip (eip, my_instance_id, my_inst_file, instances, client):

    logger.info("Setting EIP")

    launch_time = dict()

    response = client.associate_address(InstanceId=my_instance_id, PublicIp=eip, DryRun=False)
    f = open(my_inst_file, 'a')
    f.write('eip_instance={0}\n'.format(my_instance_id))
    f.close()
    logger.info('Assigned {0} to instance {1}'.format(eip, my_instance_id))

    return

def inst_running(running, not_running, response):

    for r in response['InstanceStatuses']:
        #print(r)
        if (r['InstanceState']['Name']) == 'running':
            running.append(r['InstanceId'])
        else:
            not_running.append(r['InstanceId'])

    return running, not_running

def all_inst_running(instances, client):

    logger.info("Checking if all instances are running")

    running = list()
    not_running = list()
    num_inst = len(instances)

    r = []

    while len(instances) > 100:
        temp_i = instances[:100]
        logger.info("Checking instances are running".format(num_inst))

        response = client.describe_instance_status(InstanceIds=temp_i, IncludeAllInstances=False)
        time.sleep(5)
        (running, not_running) = inst_running(running, not_running, response)

        instances   = instances[100:]
        print("r:{} nr:{}".format(len(running), len(not_running)))

    response = client.describe_instance_status(InstanceIds=instances, IncludeAllInstances=False)
    (running, not_running) = inst_running(running, not_running, response)

    if len(running) == num_inst:
        return True, len(running), running

    return False, len(not_running), not_running


def get_asg_from_stack(stack_name, client):

    logger.info('Getting the ASG(s) from stack {}'.format(stack_name))

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

    logger.info('Checking the instance status for ASG {}'.format(asg))

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


def get_current_instances_from_asg(asg_client, ec2, total_instances, asg_list):

    logger.info('Checking the current instance status for {}'.format(' '.join(asg_list)))

    instances = list()

    while True:
        if int(total_instances) == len(instances):
            break
        for asg in asg_list:
            (in_serv, not_in_serv)  = ck_asg_inst_status(asg, asg_client, ec2)
            for i in in_serv:
                if i not in instances:
                    instances.append(i)
        time.sleep(5)

    return instances


def main():

    logger.info('Setup the instance...')

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

    instances = get_current_instances_from_asg(asg_client, ec2, total_instances, asg_list)

    all_running_status = False
    inst_count = 0

    while not all_running_status:
        (all_running_status, inst_count, inst_status_list) = all_inst_running(instances, client_ec2)
        if not all_running_status:
            logger.info('Waiting for all instances to be running')
            logger.info('Instances not running {0}'.format(', '.join(inst_status_list)))
            time.sleep(10)
            # update instances
            o_instances = instances
            instances = get_current_instances_from_asg(asg_client, ec2, total_instances, asg_list)
            if instances != o_instances:
                logger.info('Some instances that were running are not now')
                for down_i in o_instances:
                    if down_i not in instances:
                        logger.info('Instance is now not running: {0}'.format(down_i))

    logger.info("All {0} instances running.".format(inst_count))
    print("All {0} instances running.".format(inst_count))

    time.sleep(5)

    # only set the EIP to the first Auto Scaling Group
    if my_asg_short_name == "AutoScalingGroup01":
        set_inst_eip(ip_addr, my_instance_id, my_inst_file, instances, client_ec2)


if __name__ == "__main__":

    log_file = "/var/log/{0}.log".format(progname)

    logging.basicConfig(level=logging.ERROR,
                        format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                        datefmt='%m-%d %H:%M',
                        filename=log_file)

    logger = logging.getLogger(progname)

    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print '\nReceived Keyboard interrupt.'
        print 'Exiting...'
    except ValueError as e:
        logger.info('ERROR: {0}'.format(e))



