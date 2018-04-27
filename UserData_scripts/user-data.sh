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
  /usr/bin/killall -9 yum
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

      while :
      do
        rpm -q pystache python-daemon python-setuptools
        rpm_ck=$?

        if [[ "$rpm_ck" != 0 ]]; then
          yum install pystache python-daemon python-setuptools -y
          curl -O https://s3.amazonaws.com/cloudformation-examples/aws-cfn-bootstrap-latest.amzn1.noarch.rpm
          rpm -ivh aws-cfn-bootstrap-latest.amzn1.noarch.rpm
          export PYTHONPATH=$PYTHONPATH:/usr/local/lib/python2.7/site-package
        else
          return
        fi
        sleep 1
      done
  fi
}

function install_awscli {

  while :
  do
    aws --version
    aws_ck=$?

    if [[ "$aws_ck" != 0 ]]; then
      pip install awscli
    else
      return
    fi
    sleep 1
  done

}

function install_pip {

  while :
  do
    pip -V
    pip_ck=$?

    if [[ "$pip_ck" != 0 ]]; then
      pushd /tmp
      curl -O https://bootstrap.pypa.io/get-pip.py
      python get-pip.py
      popd
    else
      return
    fi
    sleep 1
  done

}

function build_host_file {

  let max_wait_time=900  # in seconds
  let tot_wait_time=0
  let sleep_time=5

  export WCOLL=$home_dir/hosts.all
  let running_instances=$(/bin/su $login_user -c "pdsh date 2>/dev/null | wc -l")
  while [[ "$running_instances" -lt "$total_instances" ]]; do
    echo "Updating host info ..."
    /bin/su $login_user -c $setup_tools_dir/updatehostinfo.sh
    echo "Running 'pdsh date' to determine reachable instance count"
    let running_instances=$(/bin/su $login_user -c "pdsh date 2>/dev/null | wc -l")
    if [[ "$runnin_instances" -lt "$total_instances" ]]; then
        /bin/su $login_user -c "pdsh date 2>&1 | grep 'Connection refused' | awk {'print $6'} > ~/hosts.unreachable"
    fi
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

function mount_efs {
  let mount_count=1
  if [[ "$efs_id" == "" ]]; then
       efs_id=$new_efs
  fi
  efs_mount_pt="/mnt/efs"
  mkdir -p $efs_mount_pt
  nfs_opts="nfsvers=4.1,rsize=1048576,wsize=1048576,hard,timeo=600,retrans=2  0  0"
  echo "${efs_id}.efs.${region}.amazonaws.com:/ $efs_mount_pt   nfs4 $nfs_opts" >> /etc/fstab
  while [[ "$mount_count" -lt 11 ]]; do
    mount $efs_mount_pt
    mount_rc=$?
    if [[ "$mount_rc" != 0 ]]; then
      echo "EFS is not available, waiting..."
      sleep 60
      ((mount_count=$mount_count+1))
    else
      return
    fi
  done
  echo "Could not mount EFS, exiting."
  return
}

function inst_pkgs {
  echo "${0}: Installing additional packages"
  yum -y install https://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm
  yum -y install vim screen dstat htop strace perf pdsh openmpi openmpi-devel psmisc nfs-utils ksh
  yum -y update aws-cfn-bootstrap
  pip install boto3
}

function inst_dev_pkgs {
  echo "${0}: Installing development packages"
  yum -y groupinstall "Development Tools"
  yum -y install kernel-devel cpp gcc gcc-c++ rpm-build kernel-headers
  yum -y install "kernel-devel-uname-r == $(uname -r)"
}

function fix_boot_disable_ht() {

  echo "${0} Updating kernel line"

  if [[ -x /sbin/grubby ]] ; then
      /sbin/grubby --update-kernel=ALL --args=maxcpus=$total_cores
  fi

  if [ -e /etc/default/grub ]; then

      if grep -q maxcpus /etc/default/grub; then
          sed -i "s/maxcpus=[0-9]*/maxcpus=$total_cores/g" /etc/default/grub
      else
          sed -i "/^GRUB_CMDLINE_LINUX_DEFAULT=/ s/\"$/ maxcpus=$total_cores\"/" /etc/default/grub
          sed -i "/^GRUB_CMDLINE_LINUX=/ s/\"$/ maxcpus=$total_cores\"/" /etc/default/grub
      fi

      if [ -e /etc/grub2.cfg ]; then
          grub2-mkconfig > /etc/grub2.cfg
      fi

      if which update-grub; then
          update-grub
      fi
  fi

}

function disable_ht {
  echo "${0}: disabling HT"

  parent_cores=$(cat /sys/devices/system/cpu/cpu*/topology/thread_siblings_list | cut -d, -f1 | cut -d- -f1 | tr '-' '\n' | tr ',' '\n'| sort -un)

  # If there are no parents, HT is probably already disabled.
  if [ "$parent_cores" == "" ]; then
              parent_cores=$(cat /sys/devices/system/cpu/cpu*/topology/thread_siblings_list)
  fi

  total_cores=$(cat /sys/devices/system/cpu/cpu*/topology/thread_siblings_list | cut -d, -f1 | cut -d- -f1 | tr '-' '\n' | tr ',' '\n'| sort -un | wc -l)
  sibling_cores=$(cat /sys/devices/system/cpu/cpu*/topology/thread_siblings_list | cut -d, -f2- | cut -d- -f2- | tr '-' '\n' | tr ',' '\n'| sort -un)

  # Ensure enabled cores are enabled - starting at 1, cpu0 can't be changed
  for p in $parent_cores; do
      if [ $p -ne 0 ]; then
          echo 1 > /sys/devices/system/cpu/cpu${p}/online
      fi
  done

  if [ "$parent_cores" == "$sibling_cores" ]; then
      echo "Hyperthreading already disabled"
  else
      # Ensure disabled threads are actually disabled
      for s in $sibling_cores; do
          echo 0 > /sys/devices/system/cpu/cpu${s}/online
      done
  fi

  fix_boot_disable_ht

}

function fix_boot_clocksource() {

    echo "${0} Updating kernel line with clocksource=tsc"

    if [[ -x /sbin/grubby ]] ; then
        /sbin/grubby --update-kernel=ALL --args=clocksource=tsc
    fi

    if [ -e /etc/default/grub ]; then

        if grep -q "clocksource=tsc" /etc/default/grub; then
            exit 0
        else
            sed -i '/^GRUB\_CMDLINE\_LINUX_DEFAULT/s/\"$/\ clocksource=tsc\"/' /etc/default/grub
            sed -i '/^GRUB\_CMDLINE\_LINUX/s/\"$/\ clocksource=tsc\"/' /etc/default/grub
        fi

        if [ -e /etc/grub2.cfg ]; then
            grub2-mkconfig > /etc/grub2.cfg
        fi

        if [ -e /boot/grub2/grub.cfg ]; then
            grub2-mkconfig -o /boot/grub2/grub.cfg
        fi

        if which update-grub; then
            update-grub
        fi
    fi
}

function fix_boot_net_iname() {

    echo "${0} Updating kernel line with net.ifnames=0"

    if [[ -x /sbin/grubby ]] ; then
        /sbin/grubby --update-kernel=ALL --args=net.ifnames=0
    fi

    if [ -e /etc/default/grub ]; then

        if grep -q "net.ifnames" /etc/default/grub; then
            exit 0
        else
            sed -i '/^GRUB\_CMDLINE\_LINUX_DEFAULT/s/\"$/\ net\.ifnames\=0\"/' /etc/default/grub
            sed -i '/^GRUB\_CMDLINE\_LINUX/s/\"$/\ net\.ifnames\=0\"/' /etc/default/grub
        fi

        if [ -e /etc/grub2.cfg ]; then
            grub2-mkconfig > /etc/grub2.cfg
        fi

        if [ -e /boot/grub2/grub.cfg ]; then
            grub2-mkconfig -o /boot/grub2/grub.cfg
        fi

        if which update-grub; then
            update-grub
        fi
    fi
}

function change_tsc {
  echo "${0}: changing tsc"
  # Switch the clock source to TSC
  echo "tsc" > /sys/devices/system/clocksource/clocksource0/current_clocksource
  fix_boot_clocksource
}

function net_settings {
echo "${0}: changing network settings"
# Set TCP windows
cat >>/etc/sysctl.conf << EOF


## Custom network settings
net.core.netdev_max_backlog   = 1000000

net.core.rmem_default = 124928
net.core.rmem_max     = 67108864
net.core.wmem_default = 124928
net.core.wmem_max     = 67108864

net.ipv4.tcp_keepalive_time   = 1800
net.ipv4.tcp_mem      = 12184608        16246144        24369216
net.ipv4.tcp_rmem     = 4194304 8388608 67108864
net.ipv4.tcp_syn_retries      = 5
net.ipv4.tcp_wmem     = 4194304 8388608 67108864
EOF

sysctl -p

}

function set_custom_ulimts {

echo "${0}: setting ulimits"

# Set ulimits
cat >>/etc/security/limits.conf << EOF
# core file size (blocks, -c) 0
*           hard    core           0
*           soft    core           0

# data seg size (kbytes, -d) unlimited
*           hard    data           unlimited
*           soft    data           unlimited

# scheduling priority (-e) 0
*           hard    priority       0
*           soft    priority       0

# file size (blocks, -f) unlimited
*           hard    fsize          unlimited
*           soft    fsize          unlimited

# pending signals (-i) 256273
*           hard    sigpending     1015390
*           soft    sigpending     1015390

# max locked memory (kbytes, -l) unlimited
*           hard    memlock        unlimited
*           soft    memlock        unlimited

# open files (-n) 1024
*           hard    nofile         65536
*           soft    nofile         65536

# POSIX message queues (bytes, -q) 819200
*           hard    msgqueue       819200
*           soft    msgqueue       819200

# real-time priority (-r) 0
*           hard    rtprio         0
*           soft    rtprio         0

# stack size (kbytes, -s) unlimited
*           hard    stack          unlimited
*           soft    stack          unlimited

# cpu time (seconds, -t) unlimited
*           hard    cpu            unlimited
*           soft    cpu            unlimited

# max user processes (-u) 1024
*           soft    nproc          16384
*           hard    nproc          16384

# file locks (-x) unlimited
*           hard    locks          unlimited
*           soft    locks          unlimited
EOF

}

function setup_shell {
echo "${0}: shell setupt"

# setup shell
cat >>/home/$USER/.bash_profile << EOF

set -o vi
export EDITOR=vi

EOF

}

### Main ###

OS=$(cat /etc/redhat-release  | awk {'print $1'})

if [[ "$OS" = "CentOS" ]]; then
  USER=centos
else
  USER=ec2-user
fi


my_inst_file=$setup_tools_dir/my-instance-info.conf
source $my_inst_file

install_pip
ck_for_yum_lck
fix_cfn_init

if [[ "$operating_system" = "rhel7" ]]; then
  install_awscli
fi

if [[ ! -e /opt/aws/setup-tools/pre_installed ]]; then
  inst_pkgs
  ##inst_dev_pkgs
fi

mount_efs
disable_ht
change_tsc
net_settings
set_custom_ulimts
setup_shell

CFN_INIT=$(rpm -ql aws-cfn-bootstrap | grep "/opt/aws/apitools/.*/bin/cfn-init$")
$CFN_INIT -v --stack $stack_name --resource $launch_config --region $region
cfn_init_rc=$?

if [[ "$cfn_init_rc" != 0 ]]; then
  echo "Could not run cfn-init command"
  echo "Shutting down now"
  shutdown now
fi

# run environment setup and main function, to include assigning and saving EIP
#  includes ssh_setup
$setup_tools_dir/setup-main.sh $my_inst_file
setup_main_rc=$?

source $my_inst_file

if [[ "$my_instance_id" = "$eip_instance" ]]; then
  echo "Should have $total_instances instances"
  build_host_file
fi

$setup_tools_dir/gpfs-setup.sh
gpfs_rc=$?

cfn_sig_error_code=$gpfs_rc

CFN_SIG=$(echo -n $(rpm -ql aws-cfn-bootstrap | grep "/opt/aws/apitools/.*/bin/cfn-signal$"))   # using echo -n to remove cr
$CFN_SIG -e $cfn_sig_error_code --stack $stack_name --resource $asg_name --region $region

curl http://169.254.169.254/latest/user-data > $setup_tools_dir/user-data.sh;

