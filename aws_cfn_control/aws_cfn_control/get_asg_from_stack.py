#!/Users/duff/Envs/boto3-144/bin/python

import sys
import boto3
import argparse
sys.path.append('/Users/duff/Duff_code')
from modules.kumo import Kumo

progname = 'get_asg_from_stack'

def arg_parse():

    parser = argparse.ArgumentParser(prog=progname, description='Launch a stack, with a config file')

    req_group = parser.add_argument_group('required arguments')
    req_group.add_argument('-s', dest='stack_name', required=True)
    req_group.add_argument('-r', dest='region', required=True)

    return parser.parse_args()



def get_asg_from_stack(stack_name, client):

    asg = list()

    stk_response = client.describe_stack_resources(StackName=stack_name)

    for resp in stk_response['StackResources']:
        for resrc_type in resp:
            if resrc_type == "ResourceType":
                if resp[resrc_type] == "AWS::AutoScaling::AutoScalingGroup":
                    asg.append(resp['PhysicalResourceId'])

    return asg


def main():

    rc = 0

    args = arg_parse()

    region = args.region
    stack = args.stack_name

    cfn_client = boto3.client('cloudformation', region_name=region)

    asg = get_asg_from_stack(stack, cfn_client)

    print(asg)

    return rc

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print '\nReceived Keyboard interrupt.'
        print 'Exiting...'
