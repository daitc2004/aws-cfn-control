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

if [[ $1 ]]; then
  my_inst_info=$1
else
  my_inst_info=/opt/aws/setup-tools/my-instance-info.conf
fi

source $my_inst_info

for h in $($setup_tools_dir/gethostinfo.py); do
    ssh -o StrictHostKeyChecking=no $h date > /dev/null;
done

echo -n "Creating/Updating $home_dir/hosts.all ..."
$setup_tools_dir/gethostinfo.py > $home_dir/hosts.all
echo "done"

exit 0