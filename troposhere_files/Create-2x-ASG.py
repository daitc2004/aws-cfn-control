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
from pprint import pprint

from troposphere import Base64, FindInMap, GetAtt, Join, iam, Tags
from troposphere import Parameter, Output, Ref, Template, Condition, Equals, And, Or, Not, If
from troposphere import cloudformation, autoscaling
from troposphere.autoscaling import AutoScalingGroup, Tag, Metadata
from troposphere.autoscaling import LaunchConfiguration
from troposphere.elasticloadbalancing import LoadBalancer
from troposphere.policies import (
    AutoScalingReplacingUpdate, AutoScalingRollingUpdate, UpdatePolicy
)
import troposphere.ec2 as ec2
from troposphere.ec2 import PortRange, NetworkAcl, Route, \
    VPCGatewayAttachment, SubnetRouteTableAssociation, Subnet, RouteTable, \
    VPC, NetworkInterfaceProperty, NetworkAclEntry, \
    SubnetNetworkAclAssociation, EIP, Instance, InternetGateway, \
    SecurityGroupRule, SecurityGroup
import troposphere.elasticloadbalancing as elb
from troposphere.helpers import userdata
from troposphere.iam import AccessKey, Group, LoginProfile, PolicyType, Role, InstanceProfile, User
from troposphere import GetAtt, Ref, Template
from troposphere.iam import LoginProfile, Policy, User
import awacs
import awacs.aws
from awacs.aws import Allow, Statement, Principal, Policy, PolicyDocument
import awacs.sns
import awacs.sqs
from awacs.sts import AssumeRole
from troposphere.efs import FileSystem, MountTarget

from troposphere.policies import CreationPolicy, ResourceSignal

from _include.cfn_mappings import AddAMIMap, AddEBSOptMap, AddOSInfoMap
from _include.setup_env_file import env_file

def main():
    t = Template()
    AddAMIMap(t)
    AddEBSOptMap(t)
    AddOSInfoMap(t)

    user_data_all = list()
    setup_tools_dir = "/opt/aws/setup-tools"
    asg1 = "AutoScalingGroup01"
    asg2 = "AutoScalingGroup02"
    launch_config1 = "ASG01LaunchConfiguration"
    launch_config2 = "ASG02LaunchConfiguration"

    user_data_all = [ '#!/bin/bash -x\n',
                      '\n',
                      '##exit 0\n',  # use this to disable all user-data and bring up files
                      '\n',
                      'setup_tools_dir={0}\n'.format(setup_tools_dir),
                      'mkdir -p $setup_tools_dir\n',
                      'chmod 755 $setup_tools_dir\n',
                      '\n',
    ]

    user_data_all = list(user_data_all + env_file)

    asg1UserData = list()
    asg1UserData = [
        'asg_name="{0}"\n'.format(asg1),
        'init_cluster_size="', Ref('ASG01ClusterSize'), '"\n',
        'launch_config="{0}"\n'.format(launch_config1),
        '\n',
    ]
    asg1UserData_all = list(user_data_all + asg1UserData)

    asg2UserData = list()
    asg2UserData = [
        'asg_name="{0}"\n'.format(asg2),
        'init_cluster_size="', Ref('ASG02ClusterSize'), '"\n',
        'launch_config="{0}"\n'.format(launch_config2),
        '\n',
    ]
    asg2UserData_all = list(user_data_all + asg2UserData)

    with open('../UserData_scripts/user-data.sh', 'r',) as ud_file:
        user_data_file = ud_file.readlines()

    for l in user_data_file:
        asg1UserData_all.append(l)

    for l in user_data_file:
        asg2UserData_all.append(l)

    t.add_version("2010-09-09")

    t.add_description(
        "Launch two AutoScaling Groups, with the option to choose a different "
        "instance type for each. A placement group is used.  An instance from the first ASG"
        "is assigned an EIP, and pdsh is setup on the instance (that has the EIP) to manager the"
        "entire cluster (both ASGs)."
    )

    t.add_metadata({
        'AWS::CloudFormation::Interface': {
            'ParameterGroups': [
                {
                    'Label': {'default': 'Instance Configuration'},
                    'Parameters': ['ASG01InstanceType',
                                   'ASG02InstanceType',
                                   "OperatingSystem",
                                   'EC2KeyName',
                                   "SSHClusterKeyPub",
                                   "SSHClusterKeyPriv",
                                   "SSHBucketName",
                                   "UsePublicIp",
                                   ]
                },
                {
                    'Label': {'default': 'Network Configuration'},
                    'Parameters': ["VPCId",
                                   "Subnet",
                                   "SecurityGroups",
                                   "CreateElasticIP",
                                   ]
                },
                {
                    'Label': {'default': 'First AutoScaling Group Configuration'},
                    'Parameters': ["ASG01ClusterSize",
                                   "ASG01MaxClusterSize",
                                   "ASG01MinClusterSize"
                                   ]
                },
                {
                    'Label': {'default': 'Second AutoScaling Group Configuration'},
                    'Parameters': ["ASG02ClusterSize",
                                   "ASG02MaxClusterSize",
                                   "ASG02MinClusterSize"
                                   ]
                },
                {
                    'Label': {'default': 'Additional Configuration Parameters'},
                    'Parameters': ["AdditionalBucketName",
                                   "EfsId"
                                   ]
                }
            ],
            'ParameterLabels': {
                'ASG01InstanceType': {'default': 'ASG 01 Instance Type'},
                'ASG02InstanceType': {'default': 'ASG 02 Instance Type'},
                'OperatingSystem': {'default': 'Instance OS'},
                'EC2KeyName': {'default': 'EC2 Key Name'},
                'SSHClusterKeyPub': {'default': 'SSH Public Key Name'},
                'SSHClusterKeyPriv': {'default': 'SSH Private Key Name'},
                'SSHBucketName': {'default': 'SSH Bucket'},
                'UsePublicIp': {'default': 'Use a Public IP'},
                'VPCId': {'default': 'VPC ID'},
                'Subnet': {'default': 'Subnet ID'},
                'SecurityGroups': {'default': 'Security Groups'},
                'CreateElasticIP': {'default': 'Create and Elaastic IP'},
                'ASG01ClusterSize': {'default': 'Initial ASG 01 cluster size'},
                'ASG01MaxClusterSize': {'default': 'Max ASG 01 cluster size'},
                'ASG01MinClusterSize': {'default': 'Min ASG 01 cluster size'},
                'ASG02ClusterSize': {'default': 'Initial ASG 02 cluster size'},
                'ASG02MaxClusterSize': {'default': 'Max ASG 02 cluster size'},
                'ASG02MinClusterSize': {'default': 'Min ASG 02 cluster size'},
                'AdditionalBucketName': {'default': 'Additional Bucket'},
                'EfsId': {'default': 'EFS File System ID'}
            }
        }
    })

    EC2KeyName = t.add_parameter(Parameter(
        'EC2KeyName',
        Type="AWS::EC2::KeyPair::KeyName",
        Description="Name of an existing EC2 KeyPair to enable SSH access to the instance.",
        ConstraintDescription="REQUIRED: Must be a valud EC2 key pair"
    ))

    ASG01InstanceType = t.add_parameter(Parameter(
        'ASG01InstanceType',
        Type="String",
        Description="First AutoScaling Group instance type",
        Default="c4.8xlarge",
        AllowedValues=[
            "c3.4xlarge",
            "c3.8xlarge",
            "c4.4xlarge",
            "c4.8xlarge",
            "c5.18xlarge",
            "i3.8xlarge",
            "i3.16xlarge",
            "m4.10xlarge",
            "m4.16xlarge",
            "m5.12xlarge",
            "m5.24xlarge",
            "r3.4xlarge",
            "r3.8xlarge",
            "r4.4xlarge",
            "r4.8xlarge",
            "r4.16xlarge",
            "t2.2xlarge"
        ],
        ConstraintDescription="Must be a valid instance type for that region, with HVM64 support"
    ))

    ASG02InstanceType = t.add_parameter(Parameter(
        'ASG02InstanceType',
        Type="String",
        Description="Second AutoScaling Group instance type",
        Default="c4.8xlarge",
        AllowedValues=[
            "c3.4xlarge",
            "c3.8xlarge",
            "c4.4xlarge",
            "c4.8xlarge",
            "c5.18xlarge",
            "i3.8xlarge",
            "i3.16xlarge",
            "m4.10xlarge",
            "m4.16xlarge",
            "m5.12xlarge",
            "m5.24xlarge",
            "r3.4xlarge",
            "r3.8xlarge",
            "r4.4xlarge",
            "r4.8xlarge",
            "r4.16xlarge",
            "t2.2xlarge"
        ],
        ConstraintDescription="Must be a valid instance type for that region, with HVM64 support"
    ))

    OperatingSystem = t.add_parameter(Parameter(
        'OperatingSystem',
        Type="String",
        Description="Operating System",
        Default="alinux",
        AllowedValues=[
            "alinux",
            "alinux2",
            "centos6",
            "centos7",
            "rhel7",
            "suse11",
            "suse12",
            "ubuntu14",
            "ubuntu16"
        ],
        ConstraintDescription="Must be: alinux, alinux2, centos6, centos7, rhel7, suse11, suse12, ubuntu14, ubuntu16"
    ))

    VPCId = t.add_parameter(Parameter(
        'VPCId',
        Type="AWS::EC2::VPC::Id",
        Description="VPC Id for this instance"
    ))

    Subnet = t.add_parameter(Parameter(
        'Subnet',
        Type="AWS::EC2::Subnet::Id",
        Description="Subnet IDs"
    ))

    SecurityGroups = t.add_parameter(Parameter(
        'SecurityGroups',
        Type="AWS::EC2::SecurityGroup::Id",
        Description="REQUIRED: Security Groups IDs"
    ))

    SSHBucketName = t.add_parameter(Parameter(
        'SSHBucketName',
        Type="String",
        Description="REQUIRED:  Bucket for the ssh keys (named below)",
        ConstraintDescription="Existing bucket where the ssh keyes are stored"
    ))

    SSHClusterKeyPub = t.add_parameter(Parameter(
        'SSHClusterKeyPub',
        Type="String",
        Description="REQUIRED:  Public key name for ssh between instances in cluster",
        Default="id_rsa.pub"
    ))

    SSHClusterKeyPriv = t.add_parameter(Parameter(
        'SSHClusterKeyPriv',
        Type="String",
        Description="REQUIRED:  Private key name for ssh between instances in cluster",
        Default="id_rsa"
    ))

    UsePublicIp = t.add_parameter(Parameter(
        'UsePublicIp',
        Type="String",
        Description="Should a public IP address be given to the instance",
        Default="True",
        ConstraintDescription="True/False",
        AllowedValues=[
            "True",
            "False"
        ]
    ))

    CreateElasticIP = t.add_parameter(Parameter(
        'CreateElasticIP',
        Type="String",
        Description="Create an Elasic IP address, that will be assinged to an instance in the stack",
        Default="True",
        ConstraintDescription="True/False",
        AllowedValues=[
            "True",
            "False"
        ]
    ))

    ASG01ClusterSize = t.add_parameter(Parameter(
        'ASG01ClusterSize',
        Type="Number",
        Description="ASG 01 Initial number of instances",
        Default="2",
        ConstraintDescription="Should be an integer"
    ))

    ASG01MaxClusterSize = t.add_parameter(Parameter(
        'ASG01MaxClusterSize',
        Type="Number",
        Description="ASG 01 Max number of instances that can be launch in the ASG",
        Default="2",
        ConstraintDescription="Should be an integer"
    ))

    ASG01MinClusterSize = t.add_parameter(Parameter(
        'ASG01MinClusterSize',
        Type="Number",
        Description="ASG 01 Min number of instances that can be launch in the ASG (should be left at 0)",
        Default="0",
        ConstraintDescription="Should be an integer"
    ))

    ASG02ClusterSize = t.add_parameter(Parameter(
        'ASG02ClusterSize',
        Type="Number",
        Description="ASG 02 Initial number of instances",
        Default="2",
        ConstraintDescription="Should be an integer"
    ))

    ASG02MaxClusterSize = t.add_parameter(Parameter(
        'ASG02MaxClusterSize',
        Type="Number",
        Description="ASG 02 Max number of instances that can be launch in the ASG",
        Default="2",
        ConstraintDescription="Should be an integer"
    ))

    ASG02MinClusterSize = t.add_parameter(Parameter(
        'ASG02MinClusterSize',
        Type="Number",
        Description="ASG 02 Min number of instances that can be launch in the ASG (should be left at 0)",
        Default="0",
        ConstraintDescription="Should be an integer"
    ))

    AdditionalBucketName = t.add_parameter(Parameter(
        'AdditionalBucketName',
        Type="String",
        Description="Additional bucket for other files."
    ))

    EfsId = t.add_parameter(Parameter(
        'EfsId',
        Type="String",
        Description="EFS ID (e.g. fs-1234abcd)",
    ))

    RootRole = t.add_resource(iam.Role(
        "RootRole",
        AssumeRolePolicyDocument={"Statement": [{
            "Effect": "Allow",
            "Principal": {
                "Service": [ "ec2.amazonaws.com" ]
            },
            "Action": [ "sts:AssumeRole" ]
        }]},
        Policies=[
            iam.Policy(
                PolicyName="s3bucketaccess",
                PolicyDocument={
                    "Statement": [{
                        "Effect": "Allow",
                        "Action": [ "s3:GetObject" ],
                        "Resource": { "Fn::Join" : [ "", [ "arn:aws:s3:::", { "Ref" : "SSHBucketName" } , "/*" ] ] }
                    },
                    {
                        "Effect": "Allow",
                        "Action": [ "s3:ListBucket" ],
                        "Resource": { "Fn::Join" : [ "", [ "arn:aws:s3:::", { "Ref" : "SSHBucketName" } ] ] }
                    },
                    {
                        "Effect": "Allow",
                        "Action": [ "s3:GetObject" ],
                        "Resource": { "Fn::Join" : [ "", [ "arn:aws:s3:::", { "Ref" : "AdditionalBucketName" } , "/*" ] ] }
                    },
                    {
                        "Effect": "Allow",
                        "Action": [ "s3:ListBucket" ],
                        "Resource": { "Fn::Join" : [ "", [ "arn:aws:s3:::", { "Ref" : "AdditionalBucketName" } ] ] }
                    }],
                }
            ),
            iam.Policy(
                PolicyName="ec2describe",
                PolicyDocument={
                    "Statement": [{
                        "Effect": "Allow",
                        "Action": ["ec2:DescribeInstances",
                                   "ec2:DescribeSubnets",
                                   "ec2:DescribeInstanceStatus",
                                   "ec2:AssociateAddress",
                                   ],
                        "Resource": "*"
                    }],
                }
            ),
            iam.Policy(
                PolicyName="cfndescribe",
                PolicyDocument={
                    "Statement": [{
                        "Effect": "Allow",
                        "Action": ["cloudformation:DescribeStacks",
                                   "cloudformation:DescribeStackResources"
                                   ],
                        "Resource": "*"
                    }]
                }
            ),
            iam.Policy(
                PolicyName="asgdescribe",
                PolicyDocument={
                    "Statement": [{
                        "Effect": "Allow",
                        "Action": [ "autoscaling:DescribeAutoScalingGroups",
                                   ],
                        "Resource": "*"
                    }],
                }
            ),

        ]
    ))

    RootInstanceProfile = t.add_resource(InstanceProfile(
        "RootInstanceProfile",
        Roles=[Ref(RootRole)]
    ))

    EIPAddress = t.add_resource(EIP(
        'EIPAddress',
        Domain='vpc',
        Condition="create_elastic_ip"
    ))

    PlacementGroup = t.add_resource(ec2.PlacementGroup(
        'PlacementGroup',
        Strategy='cluster',
    ))

    tags = Tags(Name=Ref("AWS::StackName"))
    NewEfsFileSystem = t.add_resource(FileSystem(
        "NewEfsFileSystem",
        Encrypted=True,
        PerformanceMode='generalPurpose',
        FileSystemTags=tags,
        Condition='create_efs',
    ))

    EfsMountTarget = t.add_resource(MountTarget(
        "NewEfsMountTarget",
        FileSystemId=Ref(NewEfsFileSystem),
        SecurityGroups=[Ref(SecurityGroups)],
        SubnetId=Ref(Subnet),
        Condition='create_efs'
    ))

    ASG01LaunchConfig = t.add_resource(LaunchConfiguration(
        'ASG01LaunchConfiguration',
        ImageId=FindInMap("AWSRegionAMI", Ref("AWS::Region"), Ref(OperatingSystem)),
        KeyName=Ref(EC2KeyName),
        SecurityGroups=[Ref(SecurityGroups)],
        InstanceType=(Ref(ASG01InstanceType)),
        AssociatePublicIpAddress=(Ref(UsePublicIp)),
        IamInstanceProfile=(Ref(RootInstanceProfile)),
        Metadata=autoscaling.Metadata(
            cloudformation.Init({
                "config": cloudformation.InitConfig(
                    files=cloudformation.InitFiles({
                        # setup-inst.py
                        # Wait for all instances to be 'running', and then set the
                        #  Elastic IP address to the instance that has been up the longest.
                        "{0}/setup-inst.py".format(setup_tools_dir): cloudformation.InitFile(
                            content=userdata.from_file('../UserData_scripts/setup-inst.py'),
                            mode="000700",
                            owner="root",
                            group="root",
                            encoding="base64"
                        ),
                        "{0}/setup-ssh.sh".format(setup_tools_dir): cloudformation.InitFile(
                            content=userdata.from_file('../UserData_scripts/setup-ssh.sh'),
                            mode="000700",
                            owner="root",
                            group="root",
                            encoding="base64"
                        ),
                        "{0}/gethostinfo.py".format(setup_tools_dir): cloudformation.InitFile(
                            content=userdata.from_file('../UserData_scripts/gethostinfo.py'),
                            mode="000700",
                            owner=FindInMap("OSInfo", "LoginID" , Ref('OperatingSystem')),
                            group=FindInMap("OSInfo", "LoginID" , Ref('OperatingSystem')),
                            encoding="base64"
                        ),
                        "{0}/updatehostinfo.sh".format(setup_tools_dir): cloudformation.InitFile(
                            content=userdata.from_file('../UserData_scripts/updatehostinfo.sh'),
                            mode="000700",
                            owner=FindInMap("OSInfo", "LoginID" , Ref('OperatingSystem')),
                            group=FindInMap("OSInfo", "LoginID" , Ref('OperatingSystem')),
                            encoding="base64"
                        ),
                        "{0}/setup-main.sh".format(setup_tools_dir): cloudformation.InitFile(
                            content=Join('', [
                                '#!/bin/bash -x\n',
                                '\n',
                                'total_instances=', Ref(ASG01ClusterSize), '\n',
                                'function ck_for_yum_lck {\n',
                                '  if [[ -f  /var/run/yum.pid ]]; then\n',
                                '    sleep 30\n',
                                '  fi\n',
                                '  killall -9 yum\n',
                                '}\n',
                                '\n',
                                'if [[ $1 ]]; then\n',
                                '  my_inst_file=$1\n',
                                'else\n',
                                '  my_inst_file={0}/my-instance-info.conf\n'.format(setup_tools_dir),
                                'fi\n',
                                '\n',
                                'echo my_asg={0} >> $my_inst_file\n'.format(asg1),
                                '\n',
                                'source $my_inst_file\n',
                                '\n',
                                'ck_for_yum_lck\n',
                                'yum install -y aws-cfn-bootstrap\n',
                                'yum install --enablerepo=epel pdsh -y\n',
                                'pip install awscli boto3\n',
                                '\n',
                                '{0}/setup-inst.py $my_instance_id $my_inst_file $total_instances {1}\n'.format(setup_tools_dir, asg1),
                                '{0}/setup-ssh.sh $my_inst_file\n'.format(setup_tools_dir),
                                '\n',
                                'source $my_inst_file\n',
                                '\n',
                                'if [[ "$my_instance_id" = "$eip_instance" ]]; then\n',
                                '  ln -s {0}/updatehostinfo.sh /usr/local/bin/updatehostinfo\n'.format(setup_tools_dir),
                                '  ln -s {0}/gethostinfo.py /usr/local/bin/gethostinfo\n'.format(setup_tools_dir),
                                '  /bin/su $login_user -c "{0}/updatehostinfo.sh {0}/my-instance-info.conf"\n'.format(setup_tools_dir),
                                '  /bin/su $login_user -c "echo >> ~/.bash_profile; echo export WCOLL=$home_dir/hosts.all >> ~/.bash_profile"\n',
                                'fi\n',
                                '\n',
                                'exit 0\n',
                                '\n',
                                ]
                            ),
                            mode="000700",
                            owner=FindInMap("OSInfo", "LoginID" , Ref('OperatingSystem')),
                            group=FindInMap("OSInfo", "LoginID" , Ref('OperatingSystem')),
                            encoding="plain"
                        )
                    }
                    )
                )
            })
        ),
        UserData=Base64(Join('', asg1UserData_all)),
    ))
    # End of ASG01LuanchConfig

    ASG02LaunchConfig = t.add_resource(LaunchConfiguration(
        'ASG02LaunchConfiguration',
        ImageId=FindInMap("AWSRegionAMI", Ref("AWS::Region"), Ref(OperatingSystem)),
        KeyName=Ref(EC2KeyName),
        SecurityGroups=[Ref(SecurityGroups)],
        InstanceType=(Ref(ASG02InstanceType)),
        AssociatePublicIpAddress=(Ref(UsePublicIp)),
        IamInstanceProfile=(Ref(RootInstanceProfile)),
        Metadata=autoscaling.Metadata(
            cloudformation.Init({
                "config": cloudformation.InitConfig(
                    files=cloudformation.InitFiles({
                        # setup-inst.py
                        # Wait for all instances to be 'running', and then set the
                        #  Elastic IP address to the instance that has been up the longest.
                        "{0}/setup-inst.py".format(setup_tools_dir): cloudformation.InitFile(
                            content=userdata.from_file('../UserData_scripts/setup-inst.py'),
                            mode="000700",
                            owner="root",
                            group="root",
                            encoding="base64"
                        ),
                        "{0}/setup-ssh.sh".format(setup_tools_dir): cloudformation.InitFile(
                            content=userdata.from_file('../UserData_scripts/setup-ssh.sh'),
                            mode="000700",
                            owner="root",
                            group="root",
                            encoding="base64"
                        ),
                        "{0}/gethostinfo.py".format(setup_tools_dir): cloudformation.InitFile(
                            content=userdata.from_file('../UserData_scripts/gethostinfo.py'),
                            mode="000700",
                            owner=FindInMap("OSInfo", "LoginID" , Ref('OperatingSystem')),
                            group=FindInMap("OSInfo", "LoginID" , Ref('OperatingSystem')),
                            encoding="base64"
                        ),
                        "{0}/updatehostinfo.sh".format(setup_tools_dir): cloudformation.InitFile(
                            content=userdata.from_file('../UserData_scripts/updatehostinfo.sh'),
                            mode="000700",
                            owner=FindInMap("OSInfo", "LoginID" , Ref('OperatingSystem')),
                            group=FindInMap("OSInfo", "LoginID" , Ref('OperatingSystem')),
                            encoding="base64"
                        ),
                        "{0}/setup-main.sh".format(setup_tools_dir): cloudformation.InitFile(
                            content=Join('', [
                                '#!/bin/bash -x\n',
                                '\n',
                                'total_instances=', Ref(ASG02ClusterSize), '\n',
                                'function ck_for_yum_lck {\n',
                                '  if [[ -f  /var/run/yum.pid ]]; then\n',
                                '    sleep 30\n',
                                '  fi\n',
                                '  killall -9 yum\n',
                                '}\n',
                                '\n',
                                'if [[ $1 ]]; then\n',
                                '  my_inst_file=$1\n',
                                'else\n',
                                '  my_inst_file={0}/my-instance-info.conf\n'.format(setup_tools_dir),
                                'fi\n',
                                '\n',
                                'echo my_asg={0} >> $my_inst_file\n'.format(asg2),
                                '\n',
                                'source $my_inst_file\n',
                                '\n',
                                'ck_for_yum_lck\n',
                                'yum install -y aws-cfn-bootstrap\n',
                                'yum install --enablerepo=epel pdsh -y\n',
                                'pip install awscli boto3\n',
                                '\n',
                                '{0}/setup-inst.py $my_instance_id $my_inst_file $total_instances {1}\n'.format(setup_tools_dir, asg2),
                                '{0}/setup-ssh.sh $my_inst_file\n'.format(setup_tools_dir),
                                '\n',
                                'source $my_inst_file\n',
                                '\n',
                                'if [[ "$my_instance_id" = "$eip_instance" ]]; then\n',
                                '  ln -s {0}/updatehostinfo.sh /usr/local/bin/updatehostinfo\n'.format(setup_tools_dir),
                                '  ln -s {0}/gethostinfo.py /usr/local/bin/gethostinfo\n'.format(setup_tools_dir),
                                '  /bin/su $login_user -c "{0}/updatehostinfo.sh {0}/my-instance-info.conf"\n'.format(setup_tools_dir),
                                '  /bin/su $login_user -c "echo >> ~/.bash_profile; echo export WCOLL=$home_dir/hosts.all >> ~/.bash_profile"\n',
                                'fi\n',
                                '\n',
                                'exit 0\n',
                                '\n',
                            ]
                                         ),
                            mode="000700",
                            owner=FindInMap("OSInfo", "LoginID" , Ref('OperatingSystem')),
                            group=FindInMap("OSInfo", "LoginID" , Ref('OperatingSystem')),
                            encoding="plain"
                        )
                    }
                    )
                )
            })
        ),
        UserData=Base64(Join('', asg2UserData_all)),
    ))
    # End of ASG02LaunchConfig

    ASG01_PG = t.add_resource(AutoScalingGroup(
        asg1,
        DesiredCapacity=Ref(ASG01ClusterSize),
        MinSize=Ref(ASG01MinClusterSize),
        MaxSize=Ref(ASG01MaxClusterSize),
        Cooldown=10,
        LaunchConfigurationName=Ref(ASG01LaunchConfig),
        VPCZoneIdentifier=[(Ref(Subnet))],
        PlacementGroup=Ref(PlacementGroup),
        CreationPolicy=CreationPolicy(
            ResourceSignal=ResourceSignal(
                Count=Ref(ASG01ClusterSize),
                Timeout='PT60M'
            )
        ),
    ))

    ASG02_PG = t.add_resource(AutoScalingGroup(
        asg2,
        DesiredCapacity=Ref(ASG02ClusterSize),
        MinSize=Ref(ASG02MinClusterSize),
        MaxSize=Ref(ASG02MaxClusterSize),
        Cooldown=10,
        LaunchConfigurationName=Ref(ASG02LaunchConfig),
        VPCZoneIdentifier=[(Ref(Subnet))],
        PlacementGroup=Ref(PlacementGroup),
        CreationPolicy=CreationPolicy(
            ResourceSignal=ResourceSignal(
                Count=Ref(ASG02ClusterSize),
                Timeout='PT60M'
            )
        ),
    ))

    t.add_condition("use_public_ip",
                    Equals(
                        Ref(UsePublicIp),
                        "True"
                    )
    )

    t.add_condition("create_elastic_ip",
                    Equals(
                        Ref(CreateElasticIP),
                        "True"
                    )
    )

    t.add_condition("create_efs",
                    Equals(
                        Ref(EfsId),
                        ""
                    )
    )

    t.add_output([
        Output(
            "ElasticIP",
            Description="Elastic IP address for the cluster",
            Value=Ref(EIPAddress)
        )
    ])

    print(t.to_json(indent=2))


if __name__ == "__main__":
    sys.exit(main())
