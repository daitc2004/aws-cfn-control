#!/usr/bin/python

import os,sys
import json
import boto3
import argparse

def main():

    rc = 0

    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.Table('test-stack2-DynamoDBTable-HELROGX3SF8B')

    response = table.scan()
    items = (response['Items'])

    for i in items:
        print("{} {} {}".format(i['instanceId'], i['priv_dns'], i['priv_ip']))


    return rc

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print '\nReceived Keyboard interrupt.'
        print 'Exiting...'

