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

from troposphere import Ref, FindInMap

env_file = [
    'login_user=', FindInMap("OSInfo", "LoginID" , Ref("OperatingSystem")), '\n',
    '\n',
    'if [[ $1 ]]; then\n',
    '  my_inst_file=$1\n',
    'else\n',
    '  my_inst_file=/opt/aws/setup-tools/my-instance-info.conf\n',
    'fi\n',
    '\n',
    'source $my_inst_file\n',
    '\n',
    'home_dir=/home/$login_user\n',
    'if [[ "$login_user" = "" ]]; then\n',
    '  login_user="root"\n',
    '  home_dir="/root"\n',
    'fi\n',
    'echo login_user=$login_user >> $my_inst_file\n',
    'echo setup_tools_dir=$setup_tools_dir >> $my_inst_file\n',
    'echo my_inst_file=$my_inst_file >> $my_inst_file\n',
    'echo my_instance_id=$(curl http://169.254.169.254/latest/meta-data/instance-id) >> $my_inst_file\n',
    'echo operating_system=', Ref('OperatingSystem'), ' >> $my_inst_file\n',
    'echo home_dir=$home_dir >> $my_inst_file\n',
    'echo gethostinfo_filename=$setup_tools_dir/gethostinfo.py >> $my_inst_file\n',
    'echo region=', Ref('AWS::Region'), ' >> $my_inst_file\n',
    'echo stack_name=', Ref('AWS::StackName'), ' >> $my_inst_file\n',
    'echo eip_address=', Ref('EIPAddress'), ' >> $my_inst_file\n',
    '\n',
    'source $my_inst_file\n',
    '\n',
    'echo /usr/local/lib/python2.7/site-packages/ >> /usr/lib/python2.7/site-packages/usrlocal.pth\n',
    '\n'
]
