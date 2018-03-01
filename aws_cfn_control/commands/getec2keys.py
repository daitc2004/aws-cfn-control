#!/Users/duff/Envs/boto3-144/bin/python

import boto3

ec2 = boto3.client('ec2')
response = ec2.describe_key_pairs()
for pair in (response['KeyPairs']):
    print(pair['KeyName'])
