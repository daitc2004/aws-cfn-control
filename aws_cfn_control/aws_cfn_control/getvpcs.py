#!/Users/duff/Envs/boto3-144/bin/python

import sys
import boto3
sys.path.append('/Users/duff/Duff_code')
from modules.kumo import Kumo

progname = 'getvpcs'

def main():

    rc = 0

    try:
        region = sys.argv[1]
    except:
        print('Must give region name, e.g. {0} us-east-1'.format(progname))
        sys.exit(0)

    kumo_c = Kumo(region=region)

    vpc_keys_to_print = [
        'Tag_Name',
        'IsDefault',
        'CidrBlock',
    ]

    all_vpcs = kumo_c.get_vpcs()

    for vpc_id, vpc_info in all_vpcs.items():
        print('{0}'.format(vpc_id))
        for vpc_k in vpc_keys_to_print:
            try:
                print('  {0} = {1}'.format(vpc_k, vpc_info[vpc_k]))
            except KeyError:
                pass

    return rc

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print '\nReceived Keyboard interrupt.'
        print 'Exiting...'








