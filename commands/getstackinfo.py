#!/Users/duff/Envs/boto3-144/bin/python

import os,sys
import json
import boto3
import argparse
sys.path.append('/Users/duff/Duff_code')
from modules.kumo import Kumo

progname = 'getstackinfo'

def arg_parse():

    parser = argparse.ArgumentParser(prog=progname, description='Get information for a stack')

    opt_group = parser.add_argument_group()

    req_group = parser.add_argument_group('required arguments')
    req_group.add_argument('-s', dest='stack_name', required=True)
    req_group.add_argument('-r', dest='region', required=True)

    return parser.parse_args()

def main():

    rc = 0

    args = arg_parse()
    region = args.region
    stack_name = args.stack_name

    k = Kumo(region=region)
    k.get_stack_info(stack_name=stack_name)

    return rc

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print '\nReceived Keyboard interrupt.'
        print 'Exiting...'
