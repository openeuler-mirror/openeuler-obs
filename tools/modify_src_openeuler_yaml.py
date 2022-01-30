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
import sys
import yaml
import shutil
import argparse


par = argparse.ArgumentParser()
par.add_argument("-pm", "--pckg_mgmt", default=None,
        help="pckg_mgmt.yaml file path", required=True)
args = par.parse_args()

if not os.path.exists(args.pckg_mgmt):
    print("The pckg_mgmt.yaml file is not exist!")
    sys.exit(1)

def git_clone(gitee_repo):
    repo_path = os.path.join(os.getcwd(), gitee_repo)
    if os.path.exists(repo_path):
        shutil.rmtree(repo_path)
    git_url = "https://gitee.com/openeuler/%s.git" % gitee_repo
    cmd = "git clone --depth 1 %s" % git_url
    if os.system(cmd) != 0:
        print("Git clone %s failed!" % gitee_repo)
        sys.exit(1)
 
def read_yaml(file_path):
    if os.path.exists(file_path):
        with open(file_path, "r", encoding='utf-8') as f:
            file_msg = yaml.load(f, Loader=yaml.FullLoader)
    return file_msg

def write_yaml(dict_msg, file_path):
    with open(file_path, "w", encoding='utf-8') as f:
        yaml.dump(dict_msg, f, default_flow_style=False, sort_keys=False)

def modify_file_msg(pckg_msg, yaml_path_dict):
    modify_list = []
    all_list = []
    baseos_pkg_list = pckg_msg['packages']['everything']['baseos'] 
    other_pkg_list = pckg_msg['packages']['everything']['other']
    epol_pkg_list = pckg_msg['packages']['epol']
    all_list.extend(baseos_pkg_list)
    all_list.extend(other_pkg_list)
    all_list.extend(epol_pkg_list)
    
    for pckg in all_list:
        flag = False
        pkg_name = pckg['name']
        add_msg = {'name': pckg['branch_to'], 'type': 'protected', 'create_from': pckg['branch_from']}
        openeuler_path = yaml_path_dict.get(pkg_name, "")
        openeuler_msg = read_yaml(openeuler_path)
                        
        for br in openeuler_msg['branches']:
            if br['name'] == pckg['branch_to']:
                flag = True
                break
        if not flag:
            openeuler_msg['branches'].append(add_msg)
            write_yaml(openeuler_msg, openeuler_path)
            print("Modify yaml: ", openeuler_path)
            modify_list.append(pkg_name)

    write_yaml(modify_list, './modify_pkg.txt')     # modify package name list
    print('modify yaml number: ', len(modify_list))


def get_yaml_path(yaml_root_dir):
    package_dict = {}
    for root, dirs, files in os.walk(yaml_root_dir):
        for each_file in files:
            file_path = os.path.join(root, each_file)
            if each_file.endswith('.yaml') and ('src-openeuler' in file_path):
                package_name = each_file[:-5]
                package_dict[package_name] = file_path

    return package_dict


def modify_yaml_file():
    git_clone("community")
    git_clone("release-management")
    src_openeuler_yaml_root = os.path.join(os.getcwd(), "community/sig")
    yaml_dict = get_yaml_path(src_openeuler_yaml_root)
    pckg_msg = read_yaml(args.pckg_mgmt)
    modify_file_msg(pckg_msg, yaml_dict)
 

modify_yaml_file()
