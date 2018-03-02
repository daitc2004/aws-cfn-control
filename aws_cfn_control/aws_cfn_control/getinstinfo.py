#!/usr/bin/env python

import sys
import argparse
from aws_cfn_control import CfnControl

progname = 'getinstinfo'

def arg_parse():

    parser = argparse.ArgumentParser(prog=progname, description='Get instance info')

    opt_group = parser.add_argument_group()
    opt_group.add_argument('-t', dest='terminate', required=False, help='Terminate instances', action='store_true')

    req_group = parser.add_argument_group('required arguments')
    req_group.add_argument('-r', dest='region', required=True)

    return parser.parse_args()

def main():

    rc = 0

    args = arg_parse()
    region = args.region

    client = CfnControl(region=region)
    for inst, info in client.get_instance_info().items():
        print(inst)
        for k, v in info.items():
            print("  {0}:  {1}".format(k, v))

        print('-----------')

    return rc

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print '\nReceived Keyboard interrupt.'
        print 'Exiting...'
    except ValueError as e:
        print('ERROR: {0}'.format(e))



