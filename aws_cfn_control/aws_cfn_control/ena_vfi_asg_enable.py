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


def arg_parse():
    parser = argparse.ArgumentParser(prog='ena_vfi_asg_enable')
    req_group = parser.add_argument_group('required arguments')

    req_group.add_argument('-s', dest='stack_name', help="ClouldFormation Stack", required=True )
    req_group.add_argument('-r', dest='region', help="Region name", required=True )

    return parser.parse_args()


def ena_vfi(stack_name, region):

    client = CfnControl(region=region)
    asg = client.get_asg_from_stack(stack_name)
    instances = client.get_inst_from_asg(asg)
    client.enable_ena_vfi(instances)

    return 0


if __name__ == "__main__":

    args = arg_parse()

    region = args.region
    stack_name = args.stack_name

    sys.exit(ena_vfi(stack_name, region))




