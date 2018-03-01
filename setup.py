"""
aws-cfn-control
---------------
"""

# Copyright 2018 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You may not
# use this file except in compliance with the License. A copy of the License is
# located at
#
#     http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is distributed on
# an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
# express or implied. See the License for the specific language governing
# permissions and limitations under the License.

# setup.py classifiers
# https://pypi.python.org/pypi?%3Aaction=list_classifiers

import os
from setuptools import setup
from aws_cfn_control import __version__


def open_file(fname):
    return open(os.path.join(os.path.dirname(__file__), fname))


setup(
    name='aws_cfn_control',
    version=__version__,
    url='https://github.com/awslabs/aws-cfn-control',
    license="Apache License 2.0",
    author='Mark Duffield',
    author_email='duff@amazon.com',
    description='Command line launch and management tool for AWS CloudFormation',
    long_description=open_file("README.md").read(),
    py_modules=['aws_cfn_control'],
    zip_safe=False,
    include_package_data=True,
    install_requires=['boto3>=1.4.7', ],
    packages=["aws_cfn_control"],
    keywords='aws cfn control cloudformation stack',
    entry_points='''
        [console_scripts]
        aws_cfn_control=aws_cfn_control:main
    ''',
    classifiers=[
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Environment :: Web Environment',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Development Status :: 1 - Planning',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Utilities'
    ]
)