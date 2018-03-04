#!/usr/bin/env python

import sys
import argparse
from aws_cfn_control import CfnControl

def prRed(prt): print("\033[91m{}\033[00m".format(prt))
def prGreen(prt): print("\033[92m{}\033[00m".format(prt))
def prYellow(prt): print("\033[93m{}\033[00m".format(prt))
def prLightPurple(prt): print("\033[94m{}\033[00m".format(prt))
def prPurple(prt): print("\033[95m{}\033[00m".format(prt))
def prCyan(prt): print("\033[96m{}\033[00m".format(prt))
def prLightGray(prt): print("\033[97m{}\033[00m".format(prt))
def prBlack(prt): print("\033[98m{}\033[00m".format(prt))


progname = 'getinstinfo'

def arg_parse():

    parser = argparse.ArgumentParser(prog=progname, description='Get instance info')

    opt_group = parser.add_argument_group()
    opt_group.add_argument('-s', dest='instance_state', required=False,
                           help='Instance State (pending | running | shutting-down | terminated | stopping | stopped)'
                           )

    req_group = parser.add_argument_group('required arguments')
    req_group.add_argument('-r', dest='region', required=True)

    return parser.parse_args()

def main():

    rc = 0

    args = arg_parse()
    region = args.region
    instance_state = args.instance_state

    client = CfnControl(region=region)
    for inst, info in client.get_instance_info(instance_state=instance_state).items():
        print(inst)
        for k, v in info.items():
            if k == 'State':
                if v == 'running':
                    prGreen("  {0}:  {1}".format(k, v))
                elif v == 'stopped' or v == 'terminated':
                    prRed("  {0}:  {1}".format(k, v))
                else:
                    print("  {0}:  {1}".format(k, v))
            else:
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



