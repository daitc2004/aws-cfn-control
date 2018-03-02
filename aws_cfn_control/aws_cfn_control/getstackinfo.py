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

    client = CfnControl(region=region)
    client.get_stack_info(stack_name=stack_name)

    return rc

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print '\nReceived Keyboard interrupt.'
        print 'Exiting...'
    except ValueError as e:
        print('ERROR: {0}'.format(e))


