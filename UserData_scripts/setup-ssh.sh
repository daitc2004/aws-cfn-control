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

if [[ $1 ]]; then
  my_inst_file=$1
else
  my_inst_file=/opt/aws/setup-tools/my-instance-info.conf
fi

source $my_inst_file

echo Copying ssh keys to $home_dir/.ssh

ssh_bucket="Ref('SSHBucketName')"
ssh_keypriv="Ref('SSHClusterKeyPriv')"
ssh_keypub="Ref('SSHClusterKeyPub')"

aws s3 cp s3://$ssh_bucket/$ssh_keypriv $home_dir/.ssh/id_rsa
aws s3 cp s3://$ssh_bucket/$ssh_keypub $home_dir/.ssh/id_rsa.pub

cat $home_dir/.ssh/id_rsa.pub >> $home_dir/.ssh/authorized_keys
chown ${login_user}:${login_user} $home_dir/.ssh/id_rsa.pub $home_dir/.ssh/id_rsa $home_dir/.ssh/authorized_keys
chmod 600 $home_dir/.ssh/id_rsa.pub $home_dir/.ssh/id_rsa

exit 0
