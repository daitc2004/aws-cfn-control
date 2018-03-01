#!/bin/bash

CFN_SIG=$(rpm -ql aws-cfn-bootstrap | grep "/opt/aws/apitools/.*/bin/cfn-signal$")

if [[ ! "$CFN_SIG" ]]; then
    yum install epel-release -y
    yum install pystache python-daemon -y
    curl -O https://s3.amazonaws.com/cloudformation-examples/aws-cfn-bootstrap-latest.amzn1.noarch.rpm
    rpm -ivh aws-cfn-bootstrap-latest.amzn1.noarch.rpm
    export PYTHONPATH=$PYTHONPATH:/usr/local/lib/python2.7/site-packages
    CFN_SIG=$(rpm -ql aws-cfn-bootstrap | grep "/opt/aws/apitools/.*/bin/cfn-signal$")
fi



