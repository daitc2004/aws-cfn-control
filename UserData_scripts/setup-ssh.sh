#!/usr/bin/env bash
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

set -x

function setup_ssh {

  # EFS mount check is already in setup-main

  ssh_key_dir=/mnt/efs/${stack_name}
  ssh_key_file=${ssh_key_dir}/id_rsa

  if [[ "$my_instance_id" = "$eip_instance" ]]; then
    echo "On the EIP instance, creating key $ssh_key_file"

    # make key dir
    mkdir -p $ssh_key_dir
    mkdir_rc=$?
    if [[ "$mkdir_rc" != 0 ]]; then
      echo "Could not create $ssh_key_dir"
      return
    fi

    # make keys
    ssh-keygen -b 2048 -t rsa -f $ssh_key_file -q -N ''
    ssh_rc=$?
    if [[ "$ssh_rc" != 0 ]]; then
      echo "Could not generate ssy key"
      return
    fi

  fi

  echo "Copying ssh keys to ${home_dir}/.ssh"

  let ssh_count=1
  let ssh_rc=0

  while [[ "$ssh_count" -lt 11 ]]; do
    if [[ -e "${ssh_key_dir}/id_rsa" ]]; then
      cp ${ssh_key_dir}/id_rsa $home_dir/.ssh/id_rsa
      ((ssh_rc=$ssh_rc+$?))

      cp ${ssh_key_dir}/id_rsa.pub $home_dir/.ssh/id_rsa.pub
      ((ssh_rc=$ssh_rc+$?))

      cat $home_dir/.ssh/id_rsa.pub >> $home_dir/.ssh/authorized_keys
      ((ssh_rc=$ssh_rc+$?))

      chown ${login_user}:${login_user} $home_dir/.ssh/id_rsa.pub $home_dir/.ssh/id_rsa $home_dir/.ssh/authorized_keys
      ((ssh_rc=$ssh_rc+$?))

      chmod 600 $home_dir/.ssh/id_rsa.pub $home_dir/.ssh/id_rsa
      ((ssh_rc=$ssh_rc+$?))

      if [[ "$ssh_rc" -gt 0 ]]; then
        echo "Problem when copying ssh key files"
        return
      fi
      echo "Successfully setup ssh keys in ${home_dir}/.ssh"
      return
    else
      echo "Can't see ssh key yet.  Waiting..."
      sleep 60
      if [[ "$ssh_count" -eq 11 ]]; then
        echo "Could not copy ssh key files"
        return
      fi
    fi
    ((ssh_count=$ssh_count+1))
  done
  return
}

function enable_root_ssh {

  echo "${0}: setting up root ssh"

  cp /home/$login_user/.ssh/id_rsa /root/.ssh/
  cp /home/$login_user/.ssh/id_rsa.pub /root/.ssh/
  cat /root/.ssh/id_rsa.pub >> /root/.ssh/authorized_keys
  sed -i.bak 's/PermitRootLogin.*/PermitRootLogin yes/g' /etc/ssh/sshd_config
  sed -i.bak2 's/#PermitRootLogin.*/PermitRootLogin yes/g' /etc/ssh/sshd_config
  service sshd restart

}

my_inst_file=/opt/aws/setup-tools/my-instance-info.conf

if [[ $1 ]]; then
  my_inst_file=$1
fi

if [[ ! -e "$my_inst_file" ]]; then
  echo "$my_inst_file does not exist.  Exiting..."
  exit 1
fi

source $my_inst_file
setup_ssh
enable_root_ssh

exit 0
