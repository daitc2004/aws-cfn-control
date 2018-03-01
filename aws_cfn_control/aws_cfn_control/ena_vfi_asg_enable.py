#!/Users/duff/Envs/boto3-144/bin/python

import sys
import time
import boto3
import argparse
sys.path.append('/Users/duff/Duff_code')
from modules.kumo import Kumo


def arg_parse():
    parser = argparse.ArgumentParser(prog='ena_vfi_asg_enable')
    req_group = parser.add_argument_group('required arguments')

    req_group.add_argument('-s', dest='stack_name', help="ClouldFormation Stack", required=True )
    req_group.add_argument('-r', dest='region', help="Region name", required=True )

    return parser.parse_args()


def ena_vfi(stack_name, region):

    kumo_c = Kumo(region=region)
    asg = kumo_c.get_asg_from_stack(stack_name)
    instances = kumo_c.get_inst_from_asg(asg)
    kumo_c.enable_ena_vfi(instances)

    return 0


if __name__ == "__main__":

    args = arg_parse()

    region = args.region
    stack_name = args.stack_name

    sys.exit(ena_vfi(stack_name, region))

