#!/Users/duff/Envs/boto3-144/bin/python

import sys
import argparse
sys.path.append('/Users/duff/Duff_code')
from modules.kumo import Kumo

progname = 'asgctl'

def arg_parse():

    parser = argparse.ArgumentParser(prog=progname,
                                     description='Control the instances in an ASG',
                                     epilog='Example:  {} <action> -a <asg_name> -r <region>'.format(progname)
                                     )
    req_group = parser.add_argument_group('required arguments')

    # required arguments
    req_group.add_argument('action', help='Action to take: '
                                          'status, enter-stby, exit-stby, stop, start (stop will enter standby first, '
                                          'and start will exit standby after start is complete')
    req_group.add_argument('-a', dest='asg', required="True")
    req_group.add_argument('-r', dest='region', required="True")

    return parser.parse_args()


def main():

    args = arg_parse()

    region = args.region
    asg = args.asg
    action = args.action

    i = Kumo(region=region, asg=asg)

    if action == 'enter-stby':
        i.asg_enter_standby()
    elif action == 'stop':
        i.asg_enter_standby()
        i.stop_instances()
    elif action == 'start':
        i.start_instances()
        i.asg_exit_standby()
    elif action == 'exit-stby':
        i.asg_exit_standby()
    elif action == 'status':
        i.ck_asg_status()
        i.ck_inst_status()



if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print '\nReceived Keyboard interrupt.'
        print 'Exiting...'