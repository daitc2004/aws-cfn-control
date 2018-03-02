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

progname = 'getvpcs'

def main():

    rc = 0

    try:
        region = sys.argv[1]
    except:
        print('Must give region name, e.g. {0} us-east-1'.format(progname))
        sys.exit(0)

    kumo_c = Kumo(region=region)

    vpc_keys_to_print = [
        'Tag_Name',
        'IsDefault',
        'CidrBlock',
    ]

    all_vpcs = kumo_c.get_vpcs()

    for vpc_id, vpc_info in all_vpcs.items():
        print('{0}'.format(vpc_id))
        for vpc_k in vpc_keys_to_print:
            try:
                print('  {0} = {1}'.format(vpc_k, vpc_info[vpc_k]))
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


