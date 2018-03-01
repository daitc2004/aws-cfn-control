#!/bin/bash -x

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
