#@IgnoreInspection BashAddShebang

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

function ck_for_yum_lck {
  if [[ -f  /var/run/yum.pid ]]; then
    sleep 30
  fi
  killall -9 yum
}

function fix_cfn_init {
  # Setup CFN init and signal
  CFN_INIT=$(rpm -ql aws-cfn-bootstrap | grep "/opt/aws/apitools/.*/bin/cfn-init$")
  test_cfn_init_rc=$?

  if [[ "$test_cfn_init_rc" != 0 ]]; then
      if [[ "$operating_system" = "rhel7" ]]; then
          yum install -y https://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm
      else
          yum install epel-release -y
      fi

      yum install pystache python-daemon python-setuptools -y
      curl -O https://s3.amazonaws.com/cloudformation-examples/aws-cfn-bootstrap-latest.amzn1.noarch.rpm
      rpm -ivh aws-cfn-bootstrap-latest.amzn1.noarch.rpm
      export PYTHONPATH=$PYTHONPATH:/usr/local/lib/python2.7/site-packages
  fi
}

function install_awscli {

  pip install awscli

}

function install_pip {

  pushd /tmp
  curl -O https://bootstrap.pypa.io/get-pip.py
  python get-pip.py
  popd

}

function build_host_file {

  let max_wait_time=900  # in seconds
  let tot_wait_time=0
  let sleep_time=5

  export WCOLL=$home_dir/hosts.all
  let total_instances=$(/bin/su $login_user -c "pdsh date 2>/dev/null | wc -l")
  while [[ "$total_instances" -lt "$init_cluster_size" ]]; do
    echo "Updating host info ..."
    /bin/su $login_user -c $setup_tools_dir/updatehostinfo.sh
    #echo "Running 'pdsh date' to determine reachable instance count"
    #let total_instances=$(/bin/su $login_user -c "pdsh date 2>/dev/null | wc -l")
    #if [[ "$total_instances" -lt "$init_cluster_size" ]]; then
    #    /bin/su $login_user -c "pdsh date 2>&1 | grep 'Connection refused' | awk {'print $6'} > ~/hosts.unreachable"
    #fi
    sleep $sleep_time
    let "tot_wait_time=$tot_wait_time + $sleep_time"
    if [[ "$tot_wait_time" -ge "$max_wait_time" ]]; then
      echo "ERROR:  Could not reach all instances with pdsh"
      echo "Check ~/hosts.unreachable or run 'pdsh date' to find unreachable instances"
      echo "Exiting..."
      return
    fi
  done

  echo "All instances reachable"
  return

}

my_inst_file=$setup_tools_dir/my-instance-info.conf
source $my_inst_file

if [[ "$operating_system" = "rhel7" ]]; then
  install_awscli
fi

install_pip
ck_for_yum_lck
fix_cfn_init


yum install https://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm -y
yum install psmisc
yum update aws-cfn-bootstrap -y

CFN_INIT=$(rpm -ql aws-cfn-bootstrap | grep "/opt/aws/apitools/.*/bin/cfn-init$")
$CFN_INIT -v --stack $stack_name --resource $launch_config --region $region
cfn_init_rc=$?

if [[ "$cfn_init_rc" != 0 ]]; then
  shutdown now
fi

# run environment setup and main function
$setup_tools_dir/setup-main.sh $my_inst_file
setup_main_rc=$?

if [[ "$my_instance_id" = "$eip_instance" ]]; then
  build_host_file
fi

cfn_sig_error_code=$setup_main_rc

CFN_SIG=$(echo -n $(rpm -ql aws-cfn-bootstrap | grep "/opt/aws/apitools/.*/bin/cfn-signal$"))   # using echo -n to remove cr
$CFN_SIG -e $cfn_sig_error_code --stack $stack_name --resource $asg_name --region $region

curl http://169.254.169.254/latest/user-data > $setup_tools_dir/user-data.sh;

