#!/Users/duff/Envs/boto3-144/bin/python

import sys
sys.path.append('/Users/duff/Duff_code')
import time
import boto3
import argparse
from modules.kumo import Kumo


def arg_parse():

    parser = argparse.ArgumentParser(prog='add_netdev_cfn_asg')

    req_group = parser.add_argument_group('required arguments')

    req_group.add_argument('-s', dest='stack_name', help="Name of ClouldFormation Stack", required=True )
    req_group.add_argument('-r', dest='region', help="Region name", required=True )

    return parser.parse_args()


def main():

    args = arg_parse()

    region = args.region
    stack_name = args.stack_name

    kumo_c = Kumo(region=region)

    asg = kumo_c.get_asg_from_stack(stack_name)
    instances = kumo_c.get_inst_from_asg(asg)

    eip = kumo_c.set_elastic_ip(instances=instances)

    return


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print '\nReceived Keyboard interrupt.'
        print 'Exiting...'
    except ValueError as e:
        print(e)



