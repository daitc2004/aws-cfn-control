#!/Users/duff/Envs/boto3-144/bin/python

import sys
import time
import boto3
import argparse
sys.path.append('/Users/duff/Duff_code')
from modules.kumo import Kumo

prgname = 'test-kumo'

def arg_parse():

    parser = argparse.ArgumentParser(prog='test-kumo')

    req_group = parser.add_argument_group('required arguments')

    req_group.add_argument('-s', dest='stack_name', help="Name of ClouldFormation Stack", required=True )
    req_group.add_argument('-r', dest='region', help="Region name", required=True )

    return parser.parse_args()


def main():

    args = arg_parse()

    region = args.region
    stack_name = args.stack_name

    kumo_c = Kumo(region=region)

    instances = list()

    asg_list = kumo_c.get_asg_from_stack(stack_name)
    for asg in asg_list:
        for i in kumo_c.get_inst_from_asg(asg):
            instances.append(i)

    client_ec2 = boto3.client('ec2', region_name=region)

    launch_time = dict()

    response = client_ec2.describe_instances(InstanceIds=instances,DryRun=False)
    for r in response['Reservations']:
        for resp_i in (r['Instances']):
            i = resp_i['InstanceId']
            time_tuple = (resp_i['LaunchTime'].timetuple())
            launch_time_secs = time.mktime(time_tuple)
            launch_time[i] = launch_time_secs

    print(launch_time)
    return


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print '\nReceived Keyboard interrupt.'
        print 'Exiting...'
    except ValueError as e:
        print(e)



