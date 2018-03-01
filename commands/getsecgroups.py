#!/Users/duff/Envs/boto3-144/bin/python

import sys
import boto3
sys.path.append('/Users/duff/Duff_code')
from modules.kumo import Kumo

progname = 'getsubnets'

def main():

    rc = 0

    try:
        region = sys.argv[1]
    except:
        print('Must give region e.g. {0} us-east-1'.format(progname))
        sys.exit(0)

    kumo_c = Kumo(region=region)

    kumo_c.get_security_groups()


    return rc

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print '\nReceived Keyboard interrupt.'
        print 'Exiting...'


