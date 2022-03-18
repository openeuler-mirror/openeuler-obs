#!/bin/env python3
# -*- encoding=utf8 -*-
#******************************************************************************
# Copyright (c) Huawei Technologging.es Co., Ltd. 2020-2020. All rights reserved.
# licensed under the Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#     http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY OR FIT FOR A PARTICULAR
# PURPOSE.
# See the Mulan PSL v2 for more details.
# Author: zhouxiaxiang
# Create: 2022-02-24
# ******************************************************************************

import os
import re
import shutil
import argparse
import logging
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed

current_path = os.path.join(os.path.split(os.path.realpath(__file__))[0])
LOG_FORMAT = "%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
logging.basicConfig(level=logging.DEBUG, format=LOG_FORMAT, datefmt=DATE_FORMAT)


class GiteeTagManager:
    """gitee tag manager"""

    def __init__(self, **kwargs):
        """param init"""
        self.kwargs = kwargs
        self.gitee_user = self.kwargs["user"]
        self.gitee_pwd = self.kwargs["pwd"]
        self.project = self.kwargs["project"]
        self.branch = self.kwargs["branch"]
        self.pkgs = self.kwargs["pkgs"]
        self.pkgs_file = self.kwargs["pkgs_file"]
        self.tag_name = self.kwargs["tag_name"]
        self.tag_manage_type = self.kwargs["tag_manage_type"]  # add, delete
        self.failed_list = []

    def run(self, cmd, timeout=600):
        """run shell cmd"""
        ret = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding="utf-8",
                             timeout=timeout)
        logging.info("cmd: {}".format(cmd))
        if ret.stdout:
            logging.info("ret.stdout: {}".format(ret.stdout))
        if ret.stderr:
            logging.info("ret.stderr: {}".format(ret.stderr))
        return ret.returncode, ret.stdout, ret.stderr

    def param_check(self):
        """param check"""
        result = True
        if self.pkgs_file and (not os.path.exists(self.pkgs_file)):
            logging.error("pkgs_file: {} not exists".format(self.pkgs_file))
            result = False
        if not self.tag_name:
            logging.error("tag_name should not be empty")
            result = False
        if self.tag_manage_type.lower() not in ["add", "delete"]:
            logging.error("tag_manage_type should be add or delete, but got {}".format(self.tag_manage_type))
            result = False
        return result

    def get_pkg_list(self):
        """get package list"""
        if self.pkgs_file:
            with open(self.pkgs_file, "r") as pkg_file:
                pkgs = pkg_file.read()
        else:
            if self.pkgs:
                pkgs = self.pkgs
                pkgs = ",".join(pkgs)
            else:
                list_pkg_cmd = "osc list {}".format(self.project)
                _, pkgs, _ = self.run(list_pkg_cmd)

        pkg_list = re.split(r"[', \n]", pkgs)
        pkg_list = list(filter(None, pkg_list))

        return pkg_list

    def clone_package(self, pkg):
        """clone package"""
        logging.info("start clone package: {}".format(pkg))
        clone_flag = False
        _, temp_path, _ = self.run("mktemp -d")
        temp_path = temp_path.strip()
        pkg_path = os.path.join(temp_path, pkg)
        clone_cmd = "git clone --depth=1 https://%s:%s@gitee.com/src-openeuler/%s -b %s %s" % (
            self.gitee_user, self.gitee_pwd, pkg, self.branch, pkg_path)
        pull_cmd = "git -C %s pull" % pkg_path
        for i in range(5):
            self.run(clone_cmd)
            _, out, err = self.run(pull_cmd)
            if ("Already up to date" in out) or ("Already up to date" in err):
                clone_flag = True
                break
            else:
                self.run("rm -rf {}".format(pkg_path))
        logging.info("finish clone package: {}".format(pkg))
        if (not clone_flag) and (os.path.exists(temp_path)):
            shutil.rmtree(temp_path)
        return clone_flag, temp_path

    def add_tag(self, pkg, pkg_path):
        """pkg add tag"""
        logging.info("start add tag for package: {}".format(pkg))
        tag_flag = False

        # 1. tag already exist
        _, tags, _ = self.run(f"cd {pkg_path} && git tag && cd - > /dev/null")
        if self.tag_name in tags:
            logging.warning("package: {} tag already exist!".format(pkg))
            tag_flag = True
            return tag_flag

        # 2. add tag
        cmd = f"cd {pkg_path} && git tag -a {self.tag_name} -m 'new tag' && git push origin {self.tag_name} && cd - > /dev/null"
        code_push, _, _ = self.run(cmd)
        if code_push:
            return tag_flag

        # 3. check result
        _, tags, _ = self.run(f"cd {pkg_path} && git tag && cd - > /dev/null")
        if self.tag_name in tags:
            logging.info("package: {} add tag: {} ok!".format(pkg, self.tag_name))
            tag_flag = True

        logging.info("finish add tag for package: {}".format(pkg))
        return tag_flag

    def delete_tag(self, pkg):
        """pkg delete tag"""
        pass

    def tag_manage(self, pkg, temp_path):
        """add or delete tag for pkg"""
        pkg_path = os.path.join(temp_path, pkg)
        tag_flag = True
        if self.tag_manage_type.lower() == "add":
            if not self.add_tag(pkg, pkg_path):
                logging.error("pkg: {} add tag: {} failed!".format(pkg, self.tag_name))
                tag_flag = False
        else:
            if not self.delete_tag(pkg):
                logging.error("pkg: {} delete tag: {} failed!".format(pkg, self.tag_name))
                tag_flag = False
        self.run("rm -rf {}".format(temp_path))
        return tag_flag

    def pkg_tag_manage(self, pkg):
        """tag manager for every package"""
        # 1. clone package
        try:
            clone_flag, temp_path = self.clone_package(pkg)
            if not clone_flag:
                logging.error("clone pkg: {} failed!".format(pkg))
                self.failed_list.append(pkg)
                return
        except Exception as e:
            logging.error("clone pkg: {} Exception: {}!".format(pkg, e))
            self.failed_list.append(pkg)
            self.run("rm -rf {}".format(temp_path))
            return

        # 2. tag manage
        try:
            if not self.tag_manage(pkg, temp_path):
                logging.error("tag pkg: {} failed!".format(pkg))
                self.failed_list.append(pkg)
        except Exception as e:
            logging.error("tag pkg: {} Exception: {}!".format(pkg, e))
            self.failed_list.append(pkg)
            self.run("rm -rf {}".format(temp_path))

    def manage(self):
        """tag manager main function"""
        # 1. param check
        if not self.param_check():
            raise SystemExit("ERROR: param check error")
        # 2. get package list
        pkg_list = self.get_pkg_list()
        if not pkg_list:
            raise SystemExit("ERROR: there is no package to deal with")
        # 3. manage tag with ThreadPoolExecutor
        logging.info("start tag manager!")
        with ThreadPoolExecutor(max_workers=30) as job:

            obj_list = []
            for pkg in pkg_list:
                obj = job.submit(self.pkg_tag_manage, pkg)
                obj_list.append(obj)

            result = []
            for future in as_completed(obj_list):
                res = future.result()
                result.append(res)

        # 4. print result
        self.failed_list = list(set(self.failed_list))
        pkg_num = len(pkg_list)
        failed_num = len(self.failed_list)
        logging.info("all package number: {}".format(pkg_num))
        logging.info("tag success package number: {}".format(pkg_num - failed_num))
        logging.info("tag failed package number: {}".format(failed_num))
        logging.info("tag failed package list: {}".format(self.failed_list))

        if self.failed_list:
            raise SystemExit("ERROR: some packages failed!")


if __name__ == "__main__":
    par = argparse.ArgumentParser()
    par.add_argument("-u", "--user", default=None, help="gitee user", required=True)
    par.add_argument("-p", "--pwd", default=None, help="gitee password", required=True)
    par.add_argument("-proj", "--project", default=None, help="obs project", required=True)
    par.add_argument("-br", "--branch", default=None, help="gitee branch", required=True)
    par.add_argument("-pkgs", "--pkgs", default=None, nargs="+", help="package list", required=False)
    par.add_argument("-pkgs_f", "--pkgs_file", default=None, help="package list file", required=False)
    par.add_argument("-tag_n", "--tag_name", default=None, help="tag name", required=True)
    par.add_argument("-tag_t", "--tag_manage_type", default=None, help="tag manage type: add, delete", required=True)
    args = par.parse_args()

    kw = {
        "user": args.user,
        "pwd": args.pwd,
        "project": args.project,
        "branch": args.branch,
        "pkgs": args.pkgs,
        "pkgs_file": args.pkgs_file,
        "tag_name": args.tag_name,
        "tag_manage_type": args.tag_manage_type,
    }
    tag_manager = GiteeTagManager(**kw)
    tag_manager.manage()
