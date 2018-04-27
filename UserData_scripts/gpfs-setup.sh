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

set -x


function ior_setup {

  # for build on local host
  yum groupinstall "Development Tools" -y

  echo "export PATH=$PATH:/usr/lib64/openmpi/bin" >> ~/.bash_profile
  echo "export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/lib64/openmpi/lib/" >> ~/.bash_profile

  echo "export PATH=$PATH:/usr/lib64/openmpi/bin" >> ~/.bashrc
  echo "export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/lib64/openmpi/lib/" >> ~/.bashrc

  source ~/.bash_profile
  export PATH=$PATH:/usr/lib64/openmpi/bin
  export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/lib64/openmpi/lib/

  pushd /tmp
  git clone https://github.com/chaos/ior.git
  cd ior
  ./bootstrap
  ./configure LIBS=/usr/lpp/mmfs/lib/libgpfs.so
  make
  sudo cp src/ior /usr/local/bin/
  popd

  ior_version=$(/usr/local/bin/ior | head -1)
  if [[ "$ior_version" == "IOR-3.0.1: MPI Coordinated Test of Parallel I/O" ]]; then
    echo "IOR Successfully build, copying binary to all hosts"
    pdcp /usr/local/bin/ior /usr/local/bin/ior
  else
    echo "IOR Failed to build"
  fi

}

function enable_root_ssh {

  echo "${0}: setting up root ssh"

  cp /home/$USER/.ssh/id_rsa /root/.ssh/
  cp /home/$USER/.ssh/id_rsa.pub /root/.ssh/
  cat /root/.ssh/id_rsa.pub >> /root/.ssh/authorized_keys
  sed -i.bak 's/PermitRootLogin.*/PermitRootLogin yes/g' /etc/ssh/sshd_config
  sed -i.bak2 's/#PermitRootLogin.*/PermitRootLogin yes/g' /etc/ssh/sshd_config
  service sshd restart

}

function create_nsddevices_file {

cat <<'EOF' >> /var/mmfs/etc/nsddevices
#!/bin/ksh

osName=$(/bin/uname -s)

if [[ $osName = Linux ]]
then
  : # Add function to discover disks in the Linux environment.
  ls -l /dev/mpath/ 2>/dev/null | awk '{print "mpath/"$9 " generic"}'
  ls -l /dev/mapper/ 2>/dev/null | awk '{print "mapper/"$9 " generic"}'
  ls -1 /dev/vd* 2>/dev/null | awk -F '/' '{print ""$3 " generic"}'
  ls -1 /dev/xvd* 2>/dev/null | awk -F '/' '{print ""$3 " generic"}'    ## ***Added for AWS devices***
  ls -1 /dev/nvme* 2>/dev/null | awk -F '/' '{print ""$3 " generic"}'    ## ***Added for AWS devices***
fi

# To bypass the GPFS disk discovery (/usr/lpp/mmfs/bin/mmdevdiscover),
return 0

# To continue with the GPFS disk discovery steps,
# return 1

EOF

pdcp /var/mmfs/etc/nsddevices /var/mmfs/etc/nsddevices
pdsh "chmod 544 /var/mmfs/etc/nsddevices"

}

function setup_gpfs {

  num_clients=$(cat $clients_file | wc -l)

  mmcrcluster -N $cluster_file -r /usr/bin/ssh -R /usr/bin/scp -C gpfs1 -A
  echo "Waiting for mmcrcluster to complete"
  sleep 5

  mmchlicense server --accept -N all

  mmchconfig maxMBpS=12000
  mmchconfig pagepool=32G
  mmchconfig nsdSmallThreadRatio=1
  mmchconfig nsdMaxWorkerThreads=2048
  mmchconfig nsdMultiQueue=512

  mmcrnsd -F $nsd_file
  echo "Waiting for nsd create"
  sleep 30

  create_nsddevices_file

  mmstartup -a
  echo "Waiting for start to complete"
  sleep 300


  mmcrfs gpfs1 -F $nsd_file -B 1M -j cluster -n $num_clients
  echo "Waiting for FS create"
  sleep 30

  mmmount all -a

}

function ior_runs {

  # IOR shown with two instances, each has two sockets
  # large file
  mpirun --allow-run-as-root --map-by node --report-bindings --hostfile /root/gpfs.clients -wdir /gpfs/gpfs1 -np 16 ior -v -g -e -w -b 10g -F -z -t 1M

  # small file
  mpirun --allow-run-as-root --map-by node --report-bindings --hostfile /root/gpfs.clients -wdir /gpfs/gpfs1 -np 16 ior -v -g -e -w -b 10g -F -t 4k

}

function build_host_files {

echo "Building host files"

  servers=$(pdsh "grep AutoScalingGroup01 /opt/aws/setup-tools/my-instance-info.conf" 2>/dev/null | awk {'print $1'} | sed s/://)
  clients=$(pdsh "grep AutoScalingGroup02 /opt/aws/setup-tools/my-instance-info.conf" 2>/dev/null | awk {'print $1'} | sed s/://)

  cluster_file=/root/gpfs.cluster
  servers_file=/root/gpfs.servers
  clients_file=/root/gpfs.clients

  rm $cluster_file $servers_file $clients_file

  let count=1
  for s in $servers; do
    if [[ "$count" -lt 8 ]]; then
      echo ${s}:manager-quorum >> $cluster_file
    else
      echo ${s} >>  $cluster_file
    fi
    echo ${s} >> $servers_file
    ((count=$count+1))
  done

  let count=1
  for c in $clients; do
    if [[ "$count" -eq 1 ]]; then
      echo ${c}:quorum >> $cluster_file
    else
      echo ${c} >> $cluster_file
    fi
    echo ${c} >> $clients_file
    ((count=$count+1))
  done

}

function build_nsd_file {

  nsd_file=/root/gpfs.nsd
  rm $nsd_file

  let tot_disks=8
  let nsd_num=0
  fg=100

  for s in $servers; do
    let disk_num=0
    while [[ "$disk_num" -lt "$tot_disks" ]]; do
      echo "%nsd: device=/dev/nvme${disk_num}n1 nsd=nsd${nsd_num} servers=${s} usage=dataAndMetadata failureGroup=${fg} pool=system" >> $nsd_file
      ((disk_num=$disk_num+1))
      ((nsd_num=$nsd_num+1))
    done

    if [[ "$fg" == "100" ]]; then
       fg=200
    else
       fg=100
    fi

  done
}

function add_keys {

  for h in $(cat /root/hosts.all); do
    ssh -o StrictHostKeyChecking=no $h date > /dev/null
    ssh -o StrictHostKeyChecking=no ${h}.ec2.internal date > /dev/null
  done

  pdcp /root/.ssh/known_hosts /root/.ssh/known_hosts

}

source /opt/aws/setup-tools/my-instance-info.conf

OS=$(cat /etc/redhat-release  | awk {'print $1'})
my_pub_ip=$(curl http://169.254.169.254/latest/meta-data/public-ipv4)

if [[ "$OS" = "CentOS" ]]; then
  USER=centos
else
  USER=ec2-user
fi

echo "export WCOLL=/root/hosts.all" >> /root/.bashrc
echo "export PATH=$PATH:/usr/lpp/mmfs/bin" >> /root/.bashrc
source /root/.bashrc

cp /home/$USER/hosts.all /root

enable_root_ssh

if [[ "$eip_address" == "$my_pub_ip" ]]; then

  echo "GPFS Setup and Config"
  add_keys
  build_host_files
  build_nsd_file
  setup_gpfs
  ior_setup
  pdcp /root/.bash_profile /root/.bash_profile
  pdcp /root/.bashrc /root/.bashrc
#  #ior_runs

fi
