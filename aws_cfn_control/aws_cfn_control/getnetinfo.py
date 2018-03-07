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
import argparse
from aws_cfn_control import CfnControl

progname = 'getnetinfo'


def arg_parse():

    parser = argparse.ArgumentParser(prog=progname, description='Launch a stack, with a config file')

    opt_group = parser.add_argument_group()
    opt_group.add_argument('-r', dest='region', required=False, help="Region name")

    return parser.parse_args()


def get_subnets(client, vpc):

    all_subnets = client.get_subnets_from_vpc(vpc)

    subnet_ids = list()
    for subnet_id, subnet_info in all_subnets.items():
        subnet_ids.append(subnet_id)

    return ' | '.join(subnet_ids)


def get_sec_groups(client, vpc):

    all_security_group_info = client.get_security_groups(vpc=vpc)

    security_groups = list()
    for r in all_security_group_info:
        security_groups.append(r['GroupId'] + " (" + r['GroupName'][0:20] + ")")

    return ' | '.join(security_groups)


def main():

    rc = 0

    args = arg_parse()
    region = args.region

    client = CfnControl(region=region)

    vpc_keys_to_print = [
        'Tag_Name',
        'IsDefault',
        'CidrBlock',
    ]

    all_vpcs = client.get_vpcs()

    for vpc_id, vpc_info in all_vpcs.items():
        print('{0}'.format(vpc_id))
        print('   Subnets: {0}'.format(get_subnets(client,vpc_id)))
        print('   Security Groups: {0}'.format(get_sec_groups(client,vpc_id)))
        for vpc_k in vpc_keys_to_print:
            try:
                print('   {0} = {1}'.format(vpc_k, vpc_info[vpc_k]))
            except KeyError:
                pass


    return rc

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print '\nReceived Keyboard interrupt.'
        print 'Exiting...'
    except ValueError as e:
        print('ERROR: {0}'.format(e))


