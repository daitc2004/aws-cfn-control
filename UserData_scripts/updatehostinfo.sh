#!/bin/bash

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