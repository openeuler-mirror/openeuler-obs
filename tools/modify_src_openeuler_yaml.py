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
# Author: wangchong
# Create: 2021-06-04
# ******************************************************************************
"""
modify src-openeuler.yaml
"""

import os
import yaml
import shutil
import argparse


par = argparse.ArgumentParser()
par.add_argument("-pm", "--pckg_mgmt", default=None,
        help="pckg_mgmt.yaml file path", required=True)
args = par.parse_args()

if not os.path.exists(args.pckg_mgmt):
    print("The pckg_mgmt.yaml file is not exist!")
    exit(1)

def git_clone(gitee_repo):
    repo_path = os.path.join(os.getcwd(), gitee_repo)
    if os.path.exists(repo_path):
        shutil.rmtree(repo_path)
    git_url = "https://gitee.com/openeuler/%s.git" % gitee_repo
    cmd = "git clone --depth 1 %s" % git_url
    if os.system(cmd) != 0:
        print("Git clone %s failed!" % gitee_repo)
        exit(1)
 
def read_yaml(file_path):
    if os.path.exists(file_path):
        with open(file_path, "r", encoding='utf-8') as f:
            file_msg = yaml.load(f, Loader=yaml.FullLoader)
    return file_msg

def write_yaml(dict_msg, file_path):
    with open(file_path, "w", encoding='utf-8') as f:
        yaml.dump(dict_msg, f, default_flow_style=False, sort_keys=False)

def modify_file_msg(pckg_msg, openeuler_msg):
    for pckg in pckg_msg['packages']['natural']:
        flag = False
        add_msg = {'name': pckg['branch_to'], 'type': 'protected', 'create_from': pckg['branch_from']}
        for openeuler in openeuler_msg['repositories']:
            if openeuler['name'] == pckg['name']:
                for br in openeuler['branches']:
                    if br['name'] == pckg['branch_to']:
                        flag = True
                        break
                if not flag:
                    openeuler['branches'].append(add_msg)
                    break
    return openeuler_msg


def modify_yaml_file():
    git_clone("community")
    git_clone("release-management")
    src_openeuler_yaml = os.path.join(os.getcwd(), "community/repository/src-openeuler.yaml")
    openeuler_msg = read_yaml(src_openeuler_yaml)
    pckg_msg = read_yaml(args.pckg_mgmt)
    new_openeuler_msg = modify_file_msg(pckg_msg, openeuler_msg)
    new_src_openeuler_yaml = os.path.join(os.getcwd(), "src-openeuler.yaml")
    write_yaml(new_openeuler_msg, new_src_openeuler_yaml)
    print("The modified src-openeuler.yaml is in ", new_src_openeuler_yaml)
 

modify_yaml_file()
