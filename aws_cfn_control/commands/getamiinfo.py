#!/Users/duff/Envs/boto3-144/bin/python


import argparse
import os, sys
import json
import boto3


# AWS CLI command
#aws ec2 describe-images --owners 309956199498  --region us-west-2 --filters Name=name,Values=RHEL-7.3_HVM_GA-20161026-x86_64-1-Hourly2-GP2


_PROPS = [
    'ImageId',
    'Name',
    'OwnerId',
    'Description',
    'EnaSupport',
    'SriovNetSupport',
    'VirtualizationType',
    'Hypervisor',
    'Architecture',
    'RootDeviceType',
    'CreationDate',
    'Public'
]


def arg_parse():
    parser = argparse.ArgumentParser(prog='get_ami_id')
    parser.add_argument('-i',
                        dest='ami_id',
                        type=str,
                        help='AMI ID for us-east-1',
                        required=True
                        )

    return parser.parse_args()


def image_info(client, owners, ami_name):

    response = client.describe_images(
        DryRun=False,
        Owners=[
            owners,
        ],
        Filters=[
            {
                'Name': 'name',
                'Values': [
                    ami_name,
                ]
            },
        ]
    )

    return response

def get_image_info(client, ami_id):

    response = client.describe_images(
        DryRun=False,
        ImageIds=[
            ami_id,
        ],
    )

    resp = dict()

    for p in _PROPS:
        try:
            resp[p] = response["Images"][0][p]
            if resp[p] == 1:
                resp[p] = "True"
            elif resp[p] == 0:
                resp[p] = "False"
        except KeyError:
            resp[p] = "NO VALUE FOUND"

    return resp


def print_image_info(args, client):

    resp = dict()

    for arg_n, ami_id in vars(args).items():
        if ami_id:
            resp = get_image_info(client, ami_id)

    for k in _PROPS:
        print(" {0:<20}:  {1:<30}".format(k, resp[k]))

def main():

    rc = 0

    args = arg_parse()

    client_iad = boto3.client('ec2', region_name='us-east-1')
    print("Checking region us-east-1 for AMI info...")
    print_image_info(args, client_iad)

    return rc


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print '\nReceived Keyboard interrupt.'
        print 'Exiting...'





