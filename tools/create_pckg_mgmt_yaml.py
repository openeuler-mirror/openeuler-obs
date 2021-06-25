#/bin/env python3
# -*- encoding=utf8 -*-
#******************************************************************************
# Copyright (c) Huawei Technologies Co., Ltd. 2020-2020. All rights reserved.
# licensed under the Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#     http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY OR FIT FOR A PARTICULAR
# PURPOSE.
# See the Mulan PSL v2 for more details.
# Author: miao_kaibo
# Create: 2021-06-03
# ******************************************************************************
"""
create pckg-mgmt.yaml
"""

import argparse
import os
import sys
import yaml
import datetime


par = argparse.ArgumentParser()
par.add_argument("-fp", "--from_project", default=None, nargs='+', 
        help="old projects, new projects's packages will be from them", required=True)
par.add_argument("-fb", "--from_branch", default=None, 
        help="old branch, new branch will be created from it", required=True)
par.add_argument("-tp", "--to_project", default=None, nargs='+', help="new projects", required=True)
par.add_argument("-tb", "--to_branch", default=None, help="new branch will be created", required=True)
args = par.parse_args()
args.from_project.sort()
args.to_project.sort()

if len(args.from_project) != len(args.to_project):
    print("length of list from_project and to_project not equal")
    sys.exit(1)

pckg_mgmt_yaml = os.path.join(os.getcwd(), "pckg-mgmt.yaml")
pkgs_dict = {"packages": {"natural": [], "recycle": [], "delete": []}}
datestr = datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S') 

def write_yaml(dict_msg, file_path):
    with open(file_path, "w", encoding='utf-8') as f:
        yaml.dump(dict_msg, f, default_flow_style=False, sort_keys=False)


def create_dict(from_project, to_project, from_branch, to_branch):
    packages = list(set(os.popen("osc list {}".format(from_project)).read().split("\n")) - set([])) 
    for pkg in packages:
        if not pkg:
            continue
        pkgs_dict["packages"]["natural"].append({
                "name": pkg, 
                "branch_from": from_branch,
                "branch_to": to_branch,
                "obs_from": from_project,
                "obs_to": to_project,
                "date": datestr})


def create_yaml():
    for i in range(len(args.from_project)):
        create_dict(args.from_project[i], args.to_project[i], args.from_branch, args.to_branch)
    write_yaml(pkgs_dict, pckg_mgmt_yaml)


create_yaml()


