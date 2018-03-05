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

progname = 'cfnctl'

def arg_parse():

    parser = argparse.ArgumentParser(prog=progname, description='Launch a stack, with a config file')

    opt_group = parser.add_argument_group()
    opt_group.add_argument('-c', dest='stack_name', required=False)
    opt_group.add_argument('-r', dest='region', required=False)
    opt_group.add_argument('-f', dest='config_file', required=False)
    opt_group.add_argument('-t', dest='template_url', required=False, help='Build config file from template URL')
    opt_group.add_argument('-n', dest='rollback', required=False, help='Do not rollback', action='store_true')
    opt_group.add_argument('-v', dest='verbose_config_file', required=False, action='store_true', help='Verbose config file')
    opt_group.add_argument('-p', dest='aws_profile', required=False, help='AWS Profile')

    req_group = parser.add_argument_group('required arguments')
    #req_group.add_argument('-s', dest='stack_name', required=True)
    #req_group.add_argument('-r', dest='region', required=True)
    #req_group.add_argument('-c', dest='config_file', required=True)

    return parser.parse_args()


def main():

    rc = 0
    args = arg_parse()
    rollback = 'ROLLBACK'

    stack_name = args.stack_name
    region = args.region
    config_file = args.config_file
    template = args.template_url
    verbose_config_file = args.verbose_config_file

    aws_profile = 'NULL'
    if args.aws_profile:
        aws_profile = args.aws_profile
        print('Using profile {0}'.format(aws_profile))

    if args.rollback:
        rollback = 'DO_NOTHING'

    client = CfnControl(region=region,aws_profile=aws_profile)

    if template and config_file:
        errmsg = "Specify either the CFN template location, or the local config file to use"
        raise ValueError(errmsg)
    elif template:
        try:
            response = client.build_cfn_config(args.template_url, verbose=verbose_config_file)
            return response
        except Exception as e:
            raise ValueError(e)
    elif config_file:
        try:
            response = client.cr_stack(stack_name, config_file, set_rollback=rollback)
            return response
        except Exception as e:
            raise ValueError(e)
    else:
        try:
            print("Gathering info on CFN stacks...")
            response = client.ls_stacks(show_deleted=False)
            return response
        except Exception as e:
            raise ValueError(e)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print '\nReceived Keyboard interrupt.'
        print 'Exiting...'
    except ValueError as e:
        print('ERROR: {0}'.format(e))



