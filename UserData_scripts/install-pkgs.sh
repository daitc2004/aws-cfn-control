#!/bin/bash

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

CFN_SIG=$(rpm -ql aws-cfn-bootstrap | grep "/opt/aws/apitools/.*/bin/cfn-signal$")

if [[ ! "$CFN_SIG" ]]; then
    yum install epel-release -y
    yum install pystache python-daemon -y
    curl -O https://s3.amazonaws.com/cloudformation-examples/aws-cfn-bootstrap-latest.amzn1.noarch.rpm
    rpm -ivh aws-cfn-bootstrap-latest.amzn1.noarch.rpm
    export PYTHONPATH=$PYTHONPATH:/usr/local/lib/python2.7/site-packages
    CFN_SIG=$(rpm -ql aws-cfn-bootstrap | grep "/opt/aws/apitools/.*/bin/cfn-signal$")
fi



