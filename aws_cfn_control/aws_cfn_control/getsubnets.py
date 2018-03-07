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
from aws_cfn_control import CfnControl

progname = 'getsubnets'

def main():


    rc = 0

    try:
        region = sys.argv[1]
        vpc_to_get = sys.argv[2]
    except:
        print('Must give region and vpc, e.g. {0} us-east-1 vpc-1234abcd'.format(progname))
        sys.exit(0)

    client = CfnControl(region=region)
    all_subnets = client.get_subnets_from_vpc(vpc_to_get)

    subnet_ids = list()
    for subnet_id, subnet_info in all_subnets.items():
        subnet_ids.append(subnet_id)

    print(' | '.join(subnet_ids))

    return rc


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print '\nReceived Keyboard interrupt.'
        print 'Exiting...'
    except ValueError as e:
        print('ERROR: {0}'.format(e))



