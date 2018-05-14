#!/usr/bin/env bash

set -x

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

'function fix_cfn_init {\n',
'  # Setup CFN init and signal\n',
'  CFN_INIT=$(rpm -ql aws-cfn-bootstrap | grep cfn-init$)\n',
'  test_cfn_init_rc=$?\n',
'\n',
'  if [[ ! "$test_cfn_init_rc" = 0 ]]; then\n',
'      if [[ "$operating_system" = "rhel7" ]]; then\n',
'          yum install -y https://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm\n',
'      else\n',
'          yum install epel-release -y\n',
'      fi\n',
'\n',
'      yum install pystache python-daemon python-setuptools -y\n',
'      curl -O https://s3.amazonaws.com/cloudformation-examples/aws-cfn-bootstrap-latest.amzn1.noarch.rpm\n',
'      rpm -ivh aws-cfn-bootstrap-latest.amzn1.noarch.rpm\n',
'    export PYTHONPATH=$PYTHONPATH:/usr/local/lib/python2.7/site-packages\n',
'  fi\n',
'}\n',