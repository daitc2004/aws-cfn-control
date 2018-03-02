#!/usr/bin/env python

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


def AddAMIMap(t):

    t.add_mapping('AWSRegionAMI', {
        "ap-northeast-1": {
            "alinux": "ami-ceafcba8",
            "alinux2": "ami-c2680fa4",
            "centos6": "ami-88b923ee",
            "centos7": "ami-25bd2743",
            "rhel7": "ami-eb50cd8d",
            "suse11": "ami-f7960a91",
            "suse12": "ami-bddd41db",
            "ubuntu14": "ami-15e58f73",
            "ubuntu16": "ami-48630c2e"
        },
        "ap-northeast-2": {
            "alinux": "ami-863090e8",
            "alinux2": "ami-3e04a450",
            "centos6": "ami-7146e61f",
            "centos7": "ami-7248e81c",
            "rhel7": "ami-26f75748",
            "suse11": "ami-afc565c1",
            "suse12": "ami-2eff5f40",
            "ubuntu14": "ami-70c0621e",
            "ubuntu16": "ami-ab77d4c5"
        },
        "ap-south-1": {
            "alinux": "ami-531a4c3c",
            "alinux2": "ami-3b2f7954",
            "centos6": "ami-3d9ec952",
            "centos7": "ami-5d99ce32",
            "rhel7": "ami-e60e5a89",
            "suse11": "ami-d22b7fbd",
            "suse12": "ami-f7267298",
            "ubuntu14": "ami-916c3ffe",
            "ubuntu16": "ami-84e3b2eb"
        },
        "ap-southeast-1": {
            "alinux": "ami-68097514",
            "alinux2": "ami-4f89f533",
            "centos6": "ami-74fb8908",
            "centos7": "ami-d2fa88ae",
            "rhel7": "ami-5ae89f26",
            "suse11": "ami-2644325a",
            "suse12": "ami-ce7006b2",
            "ubuntu14": "ami-e355129f",
            "ubuntu16": "ami-b7f388cb"
        },
        "ap-southeast-2": {
            "alinux": "ami-942dd1f6",
            "alinux2": "ami-38708c5a",
            "centos6": "ami-b0ba46d2",
            "centos7": "ami-b6bb47d4",
            "rhel7": "ami-1987757b",
            "suse11": "ami-05d62467",
            "suse12": "ami-15e81a77",
            "ubuntu14": "ami-c625dda4",
            "ubuntu16": "ami-33ab5251"
        },
        "ca-central-1": {
            "alinux": "ami-a954d1cd",
            "alinux2": "ami-7549cc11",
            "centos6": "ami-29ac294d",
            "centos7": "ami-dcad28b8",
            "rhel7": "ami-c1cb4ea5",
            "suse11": "ami-0bd85d6f",
            "suse12": "ami-61dc5905",
            "ubuntu14": "ami-bb8206df",
            "ubuntu16": "ami-173db873"
        },
        "eu-central-1": {
            "alinux": "ami-5652ce39",
            "alinux2": "ami-1b2bb774",
            "centos6": "ami-347be65b",
            "centos7": "ami-337be65c",
            "rhel7": "ami-194cdc76",
            "suse11": "ami-2b3cac44",
            "suse12": "ami-7215851d",
            "ubuntu14": "ami-fa2fb595",
            "ubuntu16": "ami-5055cd3f"
        },
        "eu-west-1": {
            "alinux": "ami-d834aba1",
            "alinux2": "ami-db1688a2",
            "centos6": "ami-a625b8df",
            "centos7": "ami-6e28b517",
            "rhel7": "ami-c90195b0",
            "suse11": "ami-974cdbee",
            "suse12": "ami-32b6214b",
            "ubuntu14": "ami-78d2be01",
            "ubuntu16": "ami-1b791862"
        },
        "eu-west-2": {
            "alinux": "ami-403e2524",
            "alinux2": "ami-6d263d09",
            "centos6": "ami-3d6b7059",
            "centos7": "ami-ee6a718a",
            "rhel7": "ami-c1d2caa5",
            "suse11": "ami-3dc2da59",
            "suse12": "ami-fbcad29f",
            "ubuntu14": "ami-aca2b8c8",
            "ubuntu16": "ami-941e04f0"
        },
        "eu-west-3": {
            "alinux": "ami-8ee056f3",
            "alinux2": "ami-5ce55321",
            "centos6": "ami-66fd4b1b",
            "centos7": "ami-bfff49c2",
            "rhel7": "ami-dc13a4a1",
            "suse11": "ami-2e1aad53",
            "suse12": "ami-f312a58e",
            "ubuntu14": "ami-88a412f5",
            "ubuntu16": "ami-c1cf79bc"
        },
        "sa-east-1": {
            "alinux": "ami-84175ae8",
            "alinux2": "ami-f1337e9d",
            "centos6": "ami-e3b2f08f",
            "centos7": "ami-f9adef95",
            "rhel7": "ami-0e88cb62",
            "suse11": "ami-59a8eb35",
            "suse12": "ami-b1a1e2dd",
            "ubuntu14": "ami-2a82cd46",
            "ubuntu16": "ami-bb9bd7d7"
        },
        "us-east-1": {
            "alinux": "ami-97785bed",
            "alinux2": "ami-428aa838",
            "centos6": "ami-e3fdd999",
            "centos7": "ami-4bf3d731",
            "rhel7": "ami-26ebbc5c",
            "suse11": "ami-3881d042",
            "suse12": "ami-a03869da",
            "ubuntu14": "ami-a22323d8",
            "ubuntu16": "ami-66506c1c"
        },
        "us-east-2": {
            "alinux": "ami-f63b1193",
            "alinux2": "ami-710e2414",
            "centos6": "ami-ff48629a",
            "centos7": "ami-e1496384",
            "rhel7": "ami-0b1e356e",
            "suse11": "ami-22e2c947",
            "suse12": "ami-75143f10",
            "ubuntu14": "ami-35a09550",
            "ubuntu16": "ami-965e6bf3"
        },
        "us-west-1": {
            "alinux": "ami-824c4ee2",
            "alinux2": "ami-4a787a2a",
            "centos6": "ami-ade6e5cd",
            "centos7": "ami-65e0e305",
            "rhel7": "ami-77a2a317",
            "suse11": "ami-034f4f63",
            "suse12": "ami-934242f3",
            "ubuntu14": "ami-77050a17",
            "ubuntu16": "ami-07585467"
        },
        "us-west-2": {
            "alinux": "ami-f2d3638a",
            "alinux2": "ami-7f43f307",
            "centos6": "ami-8b44f2f3",
            "centos7": "ami-a042f4d8",
            "rhel7": "ami-223f945a",
            "suse11": "ami-7eb31906",
            "suse12": "ami-6bc56f13",
            "ubuntu14": "ami-8f78c2f7",
            "ubuntu16": "ami-79873901"
        }
    })


def AddOSInfoMap(t):

    t.add_mapping('OSInfo', {
        "LoginID": {
            "alinux": "ec2-user",
            "alinux2": "ec2-user",
            "rhel7": "ec2-user",
            "centos6": "centos",
            "centos7": "centos",
            "suse11": "root",
            "suse12": "root",
            "ubuntu14": "ubuntu",
            "ubuntu16": "ubuntu"
        }
    })


def AddEBSOptMap(t):

    t.add_mapping('EbsOptimized', {
        "cc2.8xlarge": {"EBSOpt": "False"},
        "cr1.8xlarge": {"EBSOpt": "False"},
        "g2.2xlarge": {"EBSOpt": "True"},
        "g2.8xlarge": {"EBSOpt": "True"},
        "p2.xlarge": {"EBSOpt": "True"},
        "p2.8xlarge": {"EBSOpt": "True"},
        "p2.16xlarge": {"EBSOpt": "True"},
        "m3.medium": {"EBSOpt": "False"},
        "m3.large": {"EBSOpt": "False"},
        "m3.xlarge": {"EBSOpt": "True"},
        "m3.2xlarge": {"EBSOpt": "True"},
        "c3.8xlarge": {"EBSOpt": "False"},
        "c3.4xlarge": {"EBSOpt": "True"},
        "c3.2xlarge": {"EBSOpt": "True"},
        "c3.xlarge": {"EBSOpt": "True"},
        "c3.large": {"EBSOpt": "False"},
        "c4.8xlarge": {"EBSOpt": "True"},
        "c4.4xlarge": {"EBSOpt": "True"},
        "c4.2xlarge": {"EBSOpt": "True"},
        "c4.xlarge": {"EBSOpt": "True"},
        "c4.large": {"EBSOpt": "True"},
        "c5.large": {"EBSOpt": "True"},
        "c5.xlarge": {"EBSOpt": "True"},
        "c5.2xlarge": {"EBSOpt": "True"},
        "c5.4xlarge": {"EBSOpt": "True"},
        "c5.9xlarge": {"EBSOpt": "True"},
        "c5.18xlarge": {"EBSOpt": "True"},
        "r3.8xlarge": {"EBSOpt": "False"},
        "r3.4xlarge": {"EBSOpt": "True"},
        "r3.2xlarge": {"EBSOpt": "True"},
        "r3.xlarge": {"EBSOpt": "True"},
        "r3.large": {"EBSOpt": "False"},
        "r4.large": {"EBSOpt": "True"},
        "r4.xlarge": {"EBSOpt": "True"},
        "r4.2xlarge": {"EBSOpt": "True"},
        "r4.4xlarge": {"EBSOpt": "True"},
        "r4.8xlarge": {"EBSOpt": "True"},
        "r4.16xlarge": {"EBSOpt": "True"},
        "i2.8xlarge": {"EBSOpt": "False"},
        "i2.4xlarge": {"EBSOpt": "True"},
        "i2.2xlarge": {"EBSOpt": "True"},
        "i2.xlarge": {"EBSOpt": "True"},
        "i2.large": {"EBSOpt": "False"},
        "i3.large": {"EBSOpt": "True"},
        "i3.xlarge": {"EBSOpt": "True"},
        "i3.2xlarge": {"EBSOpt": "True"},
        "i3.4xlarge": {"EBSOpt": "True"},
        "i3.8xlarge": {"EBSOpt": "True"},
        "i3.16xlarge": {"EBSOpt": "True"},
        "cg1.4xlarge": {"EBSOpt": "False"},
        "t2.nano": {"EBSOpt": "False"},
        "t2.micro": {"EBSOpt": "False"},
        "t2.small": {"EBSOpt": "False"},
        "t2.medium": {"EBSOpt": "False"},
        "t2.large": {"EBSOpt": "False"},
        "t2.xlarge": {"EBSOpt": "False"},
        "t2.2xlarge": {"EBSOpt": "False"},
        "d2.8xlarge": {"EBSOpt": "True"},
        "d2.4xlarge": {"EBSOpt": "True"},
        "d2.2xlarge": {"EBSOpt": "True"},
        "d2.xlarge": {"EBSOpt": "True"},
        "x1.16xlarge": {"EBSOpt": "True"},
        "x1.32xlarge": {"EBSOpt": "True"},
        "f1.2xlarge": {"EBSOpt": "True"},
        "f1.16xlarge": {"EBSOpt": "True"},
        "m4.16xlarge": {"EBSOpt": "True"},
        "m4.10xlarge": {"EBSOpt": "True"},
        "m4.4xlarge": {"EBSOpt": "True"},
        "m4.2xlarge": {"EBSOpt": "True"},
        "m4.xlarge": {"EBSOpt": "True"},
        "m4.large": {"EBSOpt": "True"}
    })


def AddGpfsAmiMap(t):

    t.add_mapping('GpfsAmiMap', {
        "ap-northeast-1": { "rhel7": "ami-c8ca3fae" },
        "ap-northeast-2": { "rhel7": "ami-c4459caa" },
        "ap-south-1": { "rhel7": "ami-08750f67" },
        "ap-southeast-1": { "rhel7": "ami-07eb7064" },
        "ap-southeast-2": { "rhel7": "ami-6aa6bf09" },
        "ca-central-1": { "rhel7": "ami-5dc97739" },
        "eu-central-1": { "rhel7": "ami-66e74e09" },
        "eu-west-1": { "rhel7": "ami-6299691b" },
        "eu-west-2": { "rhel7": "ami-9a9081fe" },
        "sa-east-1": { "rhel7": "ami-4731402b" },
        "us-east-1": { "rhel7": "ami-18b09b63" },
        "us-east-2": { "rhel7": "ami-f4af8f91" },
        "us-west-1": { "rhel7": "ami-d3aa81b3" },
        "us-west-2": { "rhel7": "ami-c16c8cb9" }
    })

