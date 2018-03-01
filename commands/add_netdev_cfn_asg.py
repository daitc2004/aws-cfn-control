#!/Users/duff/Envs/duff-code/bin/python

import sys, os
import json
import boto3
import argparse

def list_from_file(fn):
    """
    reads a list from a named file

    :param fn: a file name
    :return:  a list spearated but "\n"
    """
    f = open(fn, "r")
    s = f.read()
    f.close()
    # if last char == '\n', delete it
    if s[-1] == "\n":
        s = s[:-1]
    l = s.split("\n")
    return l


def arg_parse():
    parser = argparse.ArgumentParser(prog='add_netdev_cfn_asg')

    req_group = parser.add_argument_group('required arguments')

    req_group.add_argument('-d', dest='int_desc', help="Description for the interface", required=True )
    req_group.add_argument('-c', dest='stack_name', help="Name of ClouldFormation Stack", required=True )
    req_group.add_argument('-s', dest='subnet', help='Subnet ID', required=True )
    req_group.add_argument('-r', dest='region', help="Region name", required=True )
    req_group.add_argument('-t', dest='tot_interfaces', help="Total number of interfaces that each instance should have",
                           required=True
                           )


    return parser.parse_args()


def create_net_dev(client, subnet_id_n, desc, sg):
    """
    Creates a network device, returns the id
    :return: network device id
    """

    response = client.create_network_interface(SubnetId=subnet_id_n,Description=desc,Groups=[sg])

    return response['NetworkInterface']['NetworkInterfaceId']


def get_instance_list (asg, region):
    """
    Returns a list of instances
    """

    asg_client = boto3.client('autoscaling', region_name=region)
    asg_response = asg_client.describe_auto_scaling_groups(AutoScalingGroupNames=[asg])
    ec2 = boto3.resource('ec2', region_name=region)

    instances = list()

    # Build instance list
    for r in asg_response['AutoScalingGroups']:
        for i in r['Instances']:
            instances.append(ec2.Instance(i['InstanceId']).instance_id)

    return instances

def attach_new_dev(i_id, dev_num, client, subnet_id, desc, sg):

    net_dev_to_attach = (create_net_dev(client, subnet_id, desc, sg))

    response = client.attach_network_interface(
        DeviceIndex=dev_num,
        InstanceId=i_id,
        NetworkInterfaceId=net_dev_to_attach
    )

    return response['AttachmentId']



def main():

    rc=0

    args = arg_parse()
    region = args.region
    stack_name = args.stack_name

    ec2 = boto3.resource('ec2', region_name=region)
    client = boto3.client('ec2', region_name=region)

    cfn_client = boto3.client('cloudformation', region_name=region)
    stk_response = cfn_client.describe_stacks(StackName=stack_name)

    asg = 'None'
    subnet = 'None'
    sec_group = list()

    for i in stk_response['Stacks']:
        for r in i['Outputs']:
            if (r['OutputKey']) == 'AutoScalingGroup':
                asg=(r['OutputValue'])
            elif (r['OutputKey']) == 'SecurityGroups':
                sec_group=(r['OutputValue'])


    inst_list =  get_instance_list(asg, region)

    for i in inst_list:

        instance = ec2.Instance(i)

        num_interfaces_b = (len(instance.network_interfaces))
        num_interfaces = num_interfaces_b

        num_int_count = 0

        while num_interfaces < int(args.tot_interfaces):

            attach_resp = attach_new_dev(i,
                                         num_interfaces_b + num_int_count,
                                         client,
                                         args.subnet,
                                         args.int_desc,
                                         sec_group
                                         )

            instance = ec2.Instance(i)

            num_interfaces = (len(instance.network_interfaces))
            num_int_count += 1


        print("{0} {1} {2}".format(instance.id, num_interfaces_b, num_interfaces))

    return rc


if __name__ == '__main__':
    sys.exit(main())

