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

progname = 'getsecgroups'

def main():

    rc = 0

    try:
        region = sys.argv[1]
    except:
        print('Must give region e.g. {0} us-east-1'.format(progname))
        sys.exit(0)

    client = CfnControl(region=region)
    all_security_group_info = client.get_security_groups(vpc='vpc-6c6ea315')

    security_group_ids = list()
    for r in all_security_group_info:
        security_group_ids.append(r['GroupId'])
        print('  {0} ({1})'.format(r['GroupId'], r['GroupName'][0:20]))

    return rc

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print '\nReceived Keyboard interrupt.'
        print 'Exiting...'
    except ValueError as e:
        print('ERROR: {0}'.format(e))

