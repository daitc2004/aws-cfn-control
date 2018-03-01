#!/Users/duff/Envs/boto3-144/bin/python

import os, sys, errno
import time
import boto3
import datetime
import operator
import urllib, json
import urlparse
import subprocess
from ConfigParser import SafeConfigParser
from botocore.exceptions import ClientError


class CfnControl:

    def __init__(self, **kwords):
        self.region = kwords.get('region')

        if not self.region:
            print("Must specify region")
            return

        self.aws_profile = kwords.get('aws_profile')
        if not self.aws_profile:
            self.aws_profile = 'default'
        elif self.aws_profile == 'NULL':
            self.aws_profile = 'default'

        print('Using AWS credentials profile "{0}"'.format(self.aws_profile))

        self.instances = list()

        session = boto3.session.Session(profile_name=self.aws_profile)

        # boto resources
        self.s3 = session.resource('s3')
        self.ec2 = session.resource('ec2', region_name=self.region)

        # boto clients
        self.client_ec2 = session.client('ec2', region_name=self.region)
        self.client_asg = session.client('autoscaling', region_name=self.region)
        self.client_cfn = session.client('cloudformation', region_name=self.region)


        self.asg = kwords.get('asg')
        self.cfn_config_file = kwords.get('config_file')
        self.instances = kwords.get('instances')
        self.homedir = os.path.expanduser("~")
        self.cfn_config_base_dir = ".cfnctlconfig"
        self.cfn_config_file_dir = os.path.join(self.homedir, self.cfn_config_base_dir)
        self.TemplateUrl = 'NULL'

        self.key_pairs = list()
        key_pairs_response = self.client_ec2.describe_key_pairs()
        for pair in (key_pairs_response['KeyPairs']):
            self.key_pairs.append(pair['KeyName'])

        self. vpc_keys_to_print = [ 'Tag_Name',
                                    'IsDefault',
                                    'CidrBlock',
                                  ]

        self.subnet_keys_to_print = [ 'Tag_Name',
                                      'AvailabilityZone',
                                    ]

        self.sec_groups_keys_to_print = [ 'Description',
                                          'GroupName',
                                       ]

        if self.asg:
            response = self.client_asg.describe_auto_scaling_groups(AutoScalingGroupNames=[self.asg])

            # Build instance IDs list
            for r in response['AutoScalingGroups']:
                for i in r['Instances']:
                    self.instances.append(self.ec2.Instance(i['InstanceId']).instance_id)

        #if not self.instances:
        #    print("Instance list is null, creating stack?")

    def runcmd(self, cmdlist):

        proc = subprocess.Popen(cmdlist, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = proc.communicate()
        if proc.returncode != 0:
            log = out + err
        else:
            log = out
        return (log, proc.returncode)

    def instanace_list(self):
        # return list of instance IDs
        return self.instances

    def inst_list_from_file(self, file_name):
        """
        reads a list from a named file

        :param fn: a file name
        :return:  a list spearated but "\n"
        """
        try:
            f = open(file_name, "r")
        except:
            raise

        s = f.read()
        f.close()
        # if last char == '\n', delete it
        if s[-1] == "\n":
            s = s[:-1]
        l = s.split("\n")
        return l

    def get_asg_from_stack(self, stack_name=None):

        # returns a list of ASG names for a given stack

        self.asg = list()

        if stack_name is None:
            stack_name = self.stack_name

        # Debug
        ## print('Getting ASG name(s) from stack {0} (returns a list)'.format(stack_name))

        try:
            stk_response = self.client_cfn.describe_stack_resources(StackName=stack_name)
        except ClientError as e:
            raise ValueError(e)

        for resp in stk_response['StackResources']:
            for resrc_type in resp:
                if resrc_type == "ResourceType":
                    if resp[resrc_type] == "AWS::AutoScaling::AutoScalingGroup":
                        self.asg.append(resp['PhysicalResourceId'])

        return self.asg

    def get_inst_from_asg(self, asg=None):

        if asg is None:
            asg = self.asg

        # Debug
        ## print('Getting ASG instances from {0}'.format(asg))

        response = self.client_asg.describe_auto_scaling_groups(AutoScalingGroupNames=asg)

        self.instances = list()
        # Build instance IDs list
        for r in response['AutoScalingGroups']:
            for i in r['Instances']:
                self.instances.append(self.ec2.Instance(i['InstanceId']).instance_id)

        return self.instances

    def asg_enter_standby(self, instances=None):

        sleep_time=10
        print("Setting instances to ASG standby")

        if instances is None:
            instances = self.instances

        response = self.client_asg.enter_standby(InstanceIds=instances, AutoScalingGroupName=self.asg,
            ShouldDecrementDesiredCapacity=True
        )

        print("Sleeping for {0} seconds to allow for instances to enter standby".format(sleep_time))
        time.sleep(sleep_time)

        return response

    def asg_exit_standby(self, instances=None):

        sleep_time=30
        print("Instances are exiting from ASG standby")

        if instances is None:
            instances = self.instances

        response = self.client_asg.exit_standby(InstanceIds=instances, AutoScalingGroupName=self.asg, )

        print("Sleeping for {0} seconds to allow for instances to exit standby".format(sleep_time))
        time.sleep(sleep_time)

        return response

    def stop_instances(self, instances=None):

        sleep_time=300
        print("Stopping instances")

        if instances is None:
            instances = self.instances

        response = self.client_ec2.stop_instances(InstanceIds=instances,DryRun=False)
        print("Sleeping for {0} seconds to allow for instances to stop".format(sleep_time))
        time.sleep(sleep_time)

        return response

    def start_instances(self, instances=None):

        sleep_time=120
        print("Starting instances")

        if instances is None:
            instances = self.instances

        response = self.client_ec2.start_instances(InstanceIds=instances,DryRun=False)
        print("Sleeping for {0} seconds to allow for instances to start".format(sleep_time))
        time.sleep(sleep_time)

        return response

    def terminate_instances(self, instances=None):

        sleep_time=120
        print("Terminating instances")

        if instances is None:
            instances = self.instances

        response = self.client_ec2.terminate_instances(InstanceIds=instances,DryRun=False)
        print("Sleeping for {0} seconds to allow for instances to terminate".format(sleep_time))
        time.sleep(sleep_time)

        return response


    def ck_inst_status(self):

        response = self.client_ec2.describe_instance_status(InstanceIds=self.instances, IncludeAllInstances=True)

        running = list()
        not_running = list()

        for r in response['InstanceStatuses']:
            if (r['InstanceState']['Name']) == 'running':
                running.append(r['InstanceId'])
            else:
                not_running.append(r['InstanceId'])

        print("Instance Info:")
        print(" {0:3d}   instances are running".format(len(running)))
        print(" {0:3d}   instances are not running".format(len(not_running)))

    def ck_asg_status(self):

        response = self.client_asg.describe_auto_scaling_groups(AutoScalingGroupNames=[self.asg])
        in_standby = list()
        in_service = list()

        # Build instance IDs list
        for r in response['AutoScalingGroups']:
            for i in r['Instances']:
                if self.ec2.Instance(i['LifecycleState']).instance_id == 'Standby':
                    in_standby.append(self.ec2.Instance(i['InstanceId']).instance_id)
                else:
                    in_service.append(self.ec2.Instance(i['InstanceId']).instance_id)

        print("ASG instances status:")
        print(" {0:3d}   InService".format(len(in_service)))
        print(" {0:3d}   Standby".format(len(in_standby)))

        return in_service, in_standby

    def enable_ena_vfi(self, instances=None):

        if instances is None:
            all_instances = self.instances
        else:
            all_instances = instances

        inst_add_ena_vfi = list()

        print("Checking if instances are ENA/VFI enabled")

        for inst_id in all_instances:

           response_vfi = self.client_ec2.describe_instance_attribute(
               Attribute='sriovNetSupport',
               InstanceId=inst_id
           )

           try:
               if (response_vfi['SriovNetSupport']['Value']) == 'simple':
                   pass
           except KeyError:
               if inst_id not in inst_add_ena_vfi:
                   inst_add_ena_vfi.append(inst_id)

           # Attribute='enaSupport' is not currently supported

        if not inst_add_ena_vfi:
            print("All instances are VFI enabled (Can't check for ENA)")
            return

        print("Enabling ENA and VFI on instances")

        self.instances = inst_add_ena_vfi

        (inst_in_service, inst_in_standby) = self.ck_asg_status()

        if inst_in_service:
            self.asg_enter_standby(inst_in_service)

        self.stop_instances()

        for inst_id in self.instances:
            print('Enabling ENA/VFI on ' + inst_id)
            response_ec2_vfi = self.client_ec2.modify_instance_attribute(InstanceId=inst_id,
                                                                    SriovNetSupport={'Value': 'simple'}
                                                                    )
            response_ec2_ena = self.client_ec2.modify_instance_attribute(InstanceId=inst_id,
                                                                     EnaSupport={'Value': True},
                                                                     )

        self.start_instances()
        self.asg_exit_standby()
        if instances is None:
            self.instances = all_instances

    def get_config_files(self, dir='NULL'):

        try:
            return os.listdir(dir)
        except Exception as e:
            raise ValueError(e)

    def read_cfn_config_file(self, cfn_config_file='NULL'):

        parser = SafeConfigParser()
        parser.optionxform = str

        if cfn_config_file == 'NULL':
            parser.read(self.cfn_config_file)
        else:
            if os.path.isfile(os.path.join(self.cfn_config_file_dir, cfn_config_file + ".json.cf")):
                print("Using config file: {0}".format(
                    os.path.join(self.cfn_config_file_dir, cfn_config_file + ".json.cf"))
                )
                parser.read(os.path.join(self.cfn_config_file_dir, cfn_config_file + ".json.cf"))
            elif os.path.isfile(os.path.join(self.cfn_config_file_dir, cfn_config_file)):
                print("Using config file: {0}".format(
                    os.path.join(self.cfn_config_file_dir, cfn_config_file))
                )
                parser.read(os.path.join(self.cfn_config_file_dir, cfn_config_file))

        params = list()
        template_url = 'Null'

        self.cfn_config_file_values = dict()

        boolean_keys = ['EnableEnaVfi',
                        'AddNetInterfaces',
                        'CreateElasticIP'
                        ]

        not_cfn_param_keys = ['EnableEnaVfi',
                              'AddNetInterfaces',
                              'TotalNetInterfaces',
                              'TemplateUrl'
                             ]

        for section_name in parser.sections():
            for key, value in parser.items(section_name):
                ## print('key: {0}'.format(key))
                if key in boolean_keys:
                    value = parser.getboolean(section_name, key)

                if key == 'TemplateUrl':
                    self.TemplateUrl = value
                    # Debug
                    ## print('setting template_url {0}'.format(self.TemplateUrl))
                elif key in not_cfn_param_keys:
                    self.cfn_config_file_values[key] = value
                else:
                    self.cfn_config_file_values[key] = value
                    params.append(
                        {
                            'ParameterKey': key,
                            'ParameterValue': str(value),
                            'UsePreviousValue': False
                        }
                    )

        return params

    def cr_stack(self, stack_name, cfn_config_file, set_rollback='ROLLBACK'):

        cfn_params = self.read_cfn_config_file(cfn_config_file)
        self.cfn_config_file = cfn_config_file
        self.stack_name = stack_name

        try:
            template_url = self.TemplateUrl
            # Debug
            ##print('Using stack template {0}'.format(template_url))
            response = self.client_cfn.create_stack(
                StackName=stack_name,
                TemplateURL=template_url,
                Parameters=cfn_params,
                TimeoutInMinutes=600,
                Capabilities=['CAPABILITY_IAM'],
                OnFailure=set_rollback,
                Tags=[
                    {
                        'Key': 'Name',
                        'Value': stack_name
                    },
                ]
            )
        except ClientError as e:
            print(e.response['Error']['Message'])
            return

        stack_rc = self.stack_status(stack_name=stack_name)
        if stack_rc != 'CREATE_COMPLETE':
            print('Stack creation failed with {0}'.format(stack_rc))
            return

        self.asg = self.get_asg_from_stack(stack_name=stack_name)
        self.instances = self.get_inst_from_asg(self.asg)

        try:
            if self.cfn_config_file_values['EnableEnaVfi']:
                print("Instances finishing booting")
                time.sleep(60)
                self.enable_ena_vfi(self.instances)
        except KeyError:
            pass

        try:
            if self.cfn_config_file_values['AddNetInterfaces']:
                self.add_net_dev()
        except:
            pass

        stk_output = self.get_stack_output(stack_name)

        try:
            eip = stk_output['ElasticIP']
        except:
            raise

        self.set_elastic_ip(stack_eip=eip)
        self.get_stack_info()

        print("")

        return response

    def create_net_dev(self, subnet_id_n, desc, sg):
        """
        Creates a network device, returns the id
        :return: network device id
        """

        response = self.client_ec2.create_network_interface(SubnetId=subnet_id_n,Description=desc,Groups=[sg])

        return response['NetworkInterface']['NetworkInterfaceId']

    def attach_new_dev(self, i_id, dev_num, subnet_id, desc, sg):

        net_dev_to_attach = (self.create_net_dev(subnet_id, desc, sg))

        response = self.client_ec2.attach_network_interface(
            DeviceIndex=dev_num,
            InstanceId=i_id,
            NetworkInterfaceId=net_dev_to_attach
        )

        return response['AttachmentId']

    def add_net_dev(self):

        print("Adding network interfaces")

        for i in self.instances:

            instance = self.ec2.Instance(i)

            num_interfaces_b = (len(instance.network_interfaces))
            num_interfaces = num_interfaces_b

            num_int_count = 0

            while num_interfaces < int(self.cfn_config_file_values['TotalNetInterfaces']):

                attach_resp = self.attach_new_dev( i,
                                                   num_interfaces_b + num_int_count,
                                                   self.cfn_config_file_values['Subnet'],
                                                   self.stack_name + "-net_dev",
                                                   self.cfn_config_file_values['SecurityGroups']
                                                 )

                instance = self.ec2.Instance(i)

                num_interfaces = (len(instance.network_interfaces))
                num_int_count += 1

            print(" {0} {1} {2}".format(instance.id, num_interfaces_b, num_interfaces))
            time.sleep(10)

    def stack_status(self, stack_name=None):

        if stack_name is None:
            stack_name = self.stack_name

        res_id_old = 'NULL'
        res_status_old = 'NULL'

        while True:

            response = self.client_cfn.describe_stack_events(StackName=stack_name)

            r = response['StackEvents'][0]

            res_id_new = r['LogicalResourceId']
            res_status_new = r['ResourceStatus']

            if res_id_new == res_id_old and res_status_new == res_status_old:
                pass
            else:
                print("{0:<30} :  {1:<50}".format(res_id_new, res_status_new))
                res_id_old = r['LogicalResourceId']
                res_status_old = r['ResourceStatus']

            stack_return_list = [
                'CREATE_COMPLETE',
                'ROLLBACK_COMPLETE',
                'CREATE_FAILED'
            ]

            if r['LogicalResourceId'] == stack_name and r['ResourceStatus'] in stack_return_list:
                return r['ResourceStatus']

            time.sleep(1)

    def has_elastic_ip(self, inst_arg=None):

        if not self.instances and inst_arg is None:
            print("Instance list is null, exiting")
            return

        if inst_arg is not None:
            self.instances = inst_arg

        for i in self.instances:
            response = self.client_ec2.describe_instances(InstanceIds=[i],DryRun=False)
            for r in response['Reservations']:
                for s in (r['Instances']):
                    for interface in s['NetworkInterfaces']:
                        response = self.client_ec2.describe_network_interfaces(
                            NetworkInterfaceIds=[interface['NetworkInterfaceId']],
                            DryRun=False)

                        for r in response['NetworkInterfaces']:
                            try:
                                if (r['Association'].get('AllocationId')):
                                    return r['Association'].get('PublicIp')
                            except KeyError:
                                pass

    def get_netdev0_id(self, instance=None):

        if instance is None:
            print("Must specify one instance")
            return

        response = self.client_ec2.describe_instances(InstanceIds=[instance],DryRun=False)
        for r in response['Reservations']:
            for s in (r['Instances']):
                for interface in s['NetworkInterfaces']:
                    if interface['Attachment']['DeviceIndex'] == 0:
                        return interface['NetworkInterfaceId']

    def set_elastic_ip(self, instances=None, stack_eip=None):

        launch_time = dict()

        if instances is None:
            instances = self.instances

        has_eip = self.has_elastic_ip(instances)
        if has_eip:
            print('Elastic IP already allocated: ' + has_eip)
            return has_eip
        else:
            response = self.client_ec2.describe_instances(InstanceIds=instances,DryRun=False)
            for r in response['Reservations']:
                for resp_i in (r['Instances']):
                    i = resp_i['InstanceId']
                    time_tuple = (resp_i['LaunchTime'].timetuple())
                    launch_time_secs = time.mktime(time_tuple)
                    launch_time[i] = launch_time_secs

        launch_time_list = sorted(launch_time.items(), key=operator.itemgetter(1))
        inst_to_alloc_eip = launch_time_list[1][0]

        netdev0 = self.get_netdev0_id(inst_to_alloc_eip)

        if not netdev0:
            print("Couldn't get first device")
            return

        allocation = dict()

        try:
            if stack_eip is not None:
                allocation_id = self.get_net_alloc_id(stack_eip)
                ip_addr = stack_eip
            else:
                allocation = self.client_ec2.allocate_address(Domain='vpc')
                allocation_id = allocation['AllocationId']
                ip_addr = allocation['PublicIp']

            response = self.client_ec2.associate_address(
                                     AllocationId=allocation_id,
                                     NetworkInterfaceId=netdev0
                                     )

            print('{0} now has Elastic IP address {1}'.format(inst_to_alloc_eip, ip_addr))
            return ip_addr

        except ClientError as e:
            print(e)

    def get_stack_output(self, stack_name=None):

        if stack_name is None:
            stack_name = self.stack_name

        stk_response = None

        try:
            stk_response = self.client_cfn.describe_stacks(StackName=stack_name)
        except ClientError as e:
            print(e)

        stk_output = dict()

        for i in stk_response['Stacks']:
            for r in i['Outputs']:
                stk_output[r['OutputKey']] = r['OutputValue']

        return stk_output

    def get_net_alloc_id(self, ip=None):

        if ip is None:
            print("Must specify an IP address")
            return

        response = self.client_ec2.describe_addresses(PublicIps=[ip], DryRun=False)
        for r in response['Addresses']:
            return r['AllocationId']

    def get_stack_info(self, stack_name=None,):

        if stack_name is None: stack_name = self.stack_name

        response = self.client_cfn.describe_stacks(StackName=stack_name,)

        for i in response['Stacks']:

            print('[Parameters]')
            for p in i['Parameters']:
                print('{0:<35} = {1:<30}'.format(p['ParameterKey'], p['ParameterValue']))

            print("")

            print('[Outputs]')
            for o in i['Outputs']:
                print('{0:<35} = {1:<30}'.format(o['OutputKey'], o['OutputValue']))

    def get_bucket_and_key_from_url(self, url):

        path = urlparse.urlparse(url).path

        path_l = list()
        path_l =  path.split('/')

        bucket = path_l[1]
        key = ('/').join(path_l[2:])

        return bucket, key

    def get_cfnconfig_file(self, template_url='NULL'):

        self.cfn_config_file_basename = os.path.basename(template_url) + ".cf"
        self.cfn_config_file = os.path.join(self.cfn_config_file_dir, self.cfn_config_file_basename)

        return self.cfn_config_file

    def rm_cfnconfig_file(self, cfn_config_file):

        print('Removing incomplete config file {0}'.format(cfn_config_file))
        try:
            os.remove(cfn_config_file)
        except Exception as e:
            print(e)

        sys.exit(1)

    def set_vpc_cfn_config_file(self, cfn_config_file='NULL'):

        if cfn_config_file == 'NULL':
            cfn_config_file = self.cfn_config_file

        print('Getting VPC info...')

        all_vpcs = self.get_vpcs()

        vpc_ids = list()
        for vpc_k, vpc_values in all_vpcs.items():
            vpc_ids.append(vpc_k)

        ##print(vpc_ids)

        for vpc_id, vpc_info in all_vpcs.items():
            try:
                print('  {0} | {1} | {2} | {3}'.format(vpc_id, vpc_info['CidrBlock'], vpc_info['IsDefault'], vpc_info['Tag_Name']))
            except:
                print('  {0} | {1} | {2}'.format(vpc_id, vpc_info['CidrBlock'], vpc_info['IsDefault']))

        cli_val = raw_input("Select VPC: ")
        if cli_val not in vpc_ids:
            print("Valid VPC required.  Exiting... ")
            self.rm_cfnconfig_file(cfn_config_file)
            return

        vpc_id = cli_val

        return vpc_id

    def build_cfn_config(self, template_url, verbose=False):

        value_already_set = list()
        cfn_config_file_to_write = dict()
        cfn_config_file = self.get_cfnconfig_file(template_url)
        found_required_val = False
        vpc_id = 'NULL'

        if not os.path.isfile(cfn_config_file):
            # create config file and dir
            print("Creating config file {0}".format(cfn_config_file))
            if not os.path.isdir(self.cfn_config_file_dir):
                print("Creating config directory {0}".format(self.cfn_config_file_dir))
                try:
                    os.makedirs(self.cfn_config_file_dir)
                except OSError as e:
                    if e.errno != errno.EEXIST:
                        raise
        else:
            print("Config file {0} already exists, no changes made.  ".format(cfn_config_file))
            return

        print("Using config file {0}".format(cfn_config_file))

        (bucket, key) =  self.get_bucket_and_key_from_url(template_url)
        object = self.s3.Object(bucket, key)
        object_content = 'NULL'
        errmsg = "\nAre you using the correct CFN template and region for the CFN template?"
        try:
            object_content = object.get()['Body'].read().decode('utf-8')
        except ClientError as e:
            if "AccessDenied" in e[0]:
                raise ValueError(e[0] + errmsg)
            raise ValueError(e)

        json_content = json.loads(object_content)
        if verbose:
            pass

        #    cfn_out_file.write('[Paramters]\n')
        #    for p in sorted(json_content['Parameters']):

        #        print(json_content['Parameters'][p]['Type'])

        #        default_val = 'NULL'

        #        cfn_out_file.write('# {0}\n'.format(p))

        #        try:
        #            cfn_out_file.write('# Description: {0}\n'.format(json_content['Parameters'][p]['Description']))
        #        except KeyError:
        #            pass

        #        try:
        #            cfn_out_file.write('# Type: {0}\n'.format(json_content['Parameters'][p]['Type']))
        #        except KeyError:
        #            pass

        #        try:
        #            default_val = json_content['Parameters'][p]['Default']
        #            cfn_out_file.write('# Default: {0}\n'.format(json_content['Parameters'][p]['Default']))
        #        except KeyError:
        #            pass

        #        try:
        #            cfn_out_file.write('# ConstraintDescription: {0}\n'.format(json_content['Parameters'][p]['ConstraintDescription']))
        #        except KeyError:
        #            pass

        #        try:
        #            cfn_out_file.write('# AllowedValues: {0}\n'.format(', '.join((json_content['Parameters'][p]['AllowedValues']))))
        #        except KeyError:
        #            pass

        #        if default_val is not 'NULL':
        #            cfn_out_file.write('{0} = {1}\n'.format(p, default_val))
        #        else:
        #            cfn_out_file.write('{0} = \n'.format(p))
        #        cfn_out_file.write("\n")
        else:

            for p in sorted(json_content['Parameters']):

                default_val = 'NULL'
                cli_val = 'NULL'

                # Debug
                ##print('setting {0}'.format(p))

                # get and set AWS::EC2::KeyPair::KeyName
                try:
                    if json_content['Parameters'][p]['Type'] == 'AWS::EC2::KeyPair::KeyName':
                        if not self.key_pairs:
                            print('No EC2 keys found in {0}'.format(self.region))
                            self.rm_cfnconfig_file(cfn_config_file)
                            return
                        print('EC2 keys found in {0}:'.format(self.region))
                        ##print('  {0}'.format(', '.join(self.key_pairs)))
                        for k in self.key_pairs:
                            print('  {0}'.format(k))
                        cli_val = raw_input("Select EC2 Key: ")
                        if cli_val not in self.key_pairs:
                            print("Valid EC2 Key Pair required.  Exiting... ")
                            self.rm_cfnconfig_file(cfn_config_file)
                            return
                except Exception as e:
                    print(e)

                # get and set AWS::EC2::VPC::Id

                try:
                    if json_content['Parameters'][p]['Type'] == 'AWS::EC2::VPC::Id':
                        if vpc_id == 'NULL':
                            vpc_id = self.set_vpc_cfn_config_file(cfn_config_file)
                            cfn_config_file_to_write[p] = vpc_id
                            value_already_set.append(p)
                        else:
                            cfn_config_file_to_write[p] = vpc_id
                            value_already_set.append(p)

                except Exception as e:
                    print(e)

                # get and set List<AWS::EC2::Subnet::Id>
                try:
                    if json_content['Parameters'][p]['Type'] == 'List<AWS::EC2::Subnet::Id>':

                        if vpc_id == 'NULL':
                            try:
                                vpc_id = self.set_vpc_cfn_config_file(cfn_config_file)
                            except Exception as e:
                                print(e)

                        print('Getting subnets from {0}...'.format(vpc_id))

                        subnet_ids = list()
                        all_subnets = self.get_subnets_from_vpc(vpc_id)
                        for subnet_id, subnet_info in all_subnets.items():
                            subnet_ids.append(subnet_id)
                            try:
                                print('  {0} | {1} | {2}'.format(subnet_id, subnet_info['AvailabilityZone'], subnet_info['Tag_Name'][0:20]))
                            except KeyError:
                                print('  {0} | {1}'.format(subnet_id, subnet_info['AvailabilityZone']))
                        cli_val = raw_input("Select subnet: ")
                        if cli_val not in subnet_ids:
                            print("Valid subnet ID required.  Exiting... ")
                            self.rm_cfnconfig_file(cfn_config_file)
                            return
                except:
                    pass

                # get and set AWS::EC2::SecurityGroup::Id
                try:
                    if json_content['Parameters'][p]['Type'] == 'AWS::EC2::SecurityGroup::Id':
                        print('Getting security groups...')

                        security_group_ids = list()
                        all_security_group_info = self.get_security_groups()

                        for r in all_security_group_info:
                            security_group_ids.append(r['GroupId'])
                            print('  {0} | {1}'.format(r['GroupId'], r['GroupName'][0:20]))
                        cli_val = raw_input('Enter valid security group: ')
                        if cli_val not in security_group_ids:
                            print("Valid security group required.  Exiting... ")
                            self.rm_cfnconfig_file(cfn_config_file)
                except Exception as e:
                    print(e)


                try:
                    default_val = json_content['Parameters'][p]['Default']
                except KeyError:
                    pass

                try:
                    if cli_val == 'NULL' and default_val == 'NULL' and json_content['Parameters'][p]['ConstraintDescription']:
                        print('Parameter "{0}" is required, but can be changed in config file'.format(p))
                        cli_val = raw_input('Enter {0}: '.format(p))
                        if cli_val == "":
                            cli_val = "<VALUE_NEEDED>"
                            found_required_val = True
                except:
                    pass

                try:
                    if p not in value_already_set:
                        if cli_val is not 'NULL':
                            cfn_config_file_to_write[p] = cli_val
                            value_already_set.append(p)
                        elif default_val is not 'NULL':
                            cfn_config_file_to_write[p] = default_val
                            value_already_set.append(p)
                        else:
                            cfn_config_file_to_write[p] = ""
                            value_already_set.append(p)
                except KeyError:
                    pass

        if found_required_val:
            print('Some values are still needed, replace "<VALUE_NEEDED>" in {0}'.format(cfn_config_file))

        # Debug
        ## print (sorted(cfn_config_file_to_write.items()))
        with open(self.cfn_config_file, 'w') as cfn_out_file:

            cfn_out_file.write('[AWS-Config]\n')
            cfn_out_file.write('{0} = {1}\n'.format('TemplateUrl', template_url))
            cfn_out_file.write('\n')

            cfn_out_file.write('[Paramters]\n')

            for k, v in sorted(cfn_config_file_to_write.items()):
                cfn_out_file.write('{0:<35} = {1}\n'.format(k, v))

        print("Done building cfnctl config file.")

        return

    def get_instance_info(self, instance_state='running'):

        # returns a dictionary

        #  Instnace state can be:  pending | running | shutting-down | terminated | stopping | stopped

        running_instances = self.ec2.instances.filter(Filters=[{
            'Name': 'instance-state-name',
            'Values': ['running']}])

        inst_info = dict()
        for i in running_instances:
            tag_name = 'NULL'
            for tag in i.tags:
                if tag['Key'] == 'Name':
                    tag_name = tag['Value']
            inst_info[i.id] = {
                'TAG::Name': tag_name,
                'Type': i.instance_type,
                'State': i.state['Name'],
                'Private IP': i.private_ip_address,
                'Private DNS': i.private_dns_name,
                'Public IP': i.public_ip_address,
                'Launch Time': i.launch_time
            }

        return inst_info   # returns a dictionary

    def get_vpcs(self):

        response = self.client_ec2.describe_vpcs()
        vpc_name = dict()

        vpc_keys_all = [
            'Tag_Name',
            'VpcId',
            'InstanceTenancy',
            'Tags',
            'State',
            'DhcpOptionsId',
            'CidrBlock',
            'IsDefault'
        ]

        all_vpcs = dict()

        for v in response['Vpcs']:
            all_vpcs[v['VpcId']] = dict()
            try:
                for t in (v['Tags']):
                    if (t['Key']) == 'Name':
                        all_vpcs[v['VpcId']]['Tag_Name'] = t['Value']
            except KeyError:
                pass

            for vpc_key in self.vpc_keys_to_print:
                try:
                    all_vpcs[v['VpcId']][vpc_key] = v[vpc_key]
                except:
                    pass

        return all_vpcs

    def get_subnets_from_vpc(self,vpc_to_get):

        subnet_keys_all = [ 'Tag_Name',
                            'VpcId',
                            'Tags',
                            'AvailableIpAddressCount',
                            'MapPublicIpOnLaunch',
                            'DefaultForAz',
                            'Ipv6CidrBlockAssociationSet',
                            'State',
                            'AvailabilityZone',
                            'SubnetId',
                            'CidrBlock',
                            'AssignIpv6AddressOnCreation'
                            ]

        response = self.client_ec2.describe_subnets(Filters=[{'Name': 'vpc-id', 'Values': [vpc_to_get]}])

        all_subnets = dict()

        for r in response['Subnets']:
            all_subnets[r['SubnetId']] = dict()
            try:
                for t in (r['Tags']):
                    if (t['Key']) == 'Name':
                        all_subnets[r['SubnetId']]['Tag_Name'] = t['Value']
            except KeyError:
                pass

            for sn_key in subnet_keys_all:
                try:
                    all_subnets[r['SubnetId']][sn_key] = r[sn_key]
                except KeyError:
                    pass

        return all_subnets

    def get_security_groups(self):

        sec_groups_all_keys = [
            'IpPermissionsEgress',
            'Description',
            'GroupName',
            'VpcId',
            'OwnerId',
            'GroupId',
        ]

        response = self.client_ec2.describe_security_groups()

        return response['SecurityGroups']


    def setup(self):
        pass

    def teardown(self):
        pass


