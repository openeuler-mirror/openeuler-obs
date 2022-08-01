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
# Create: 2022-06-23
# ******************************************************************************

import os
import argparse
import logging
import subprocess
import xml.etree.ElementTree as ET


current_path = os.path.join(os.path.split(os.path.realpath(__file__))[0])
LOG_FORMAT = "%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
logging.basicConfig(level=logging.DEBUG, format=LOG_FORMAT, datefmt=DATE_FORMAT)


def run(cmd, timeout=600, print_out=False):
    """run shell cmd"""
    ret = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding="utf-8",
                         timeout=timeout)
    logging.info("cmd: {}".format(cmd))
    if ret.stdout and print_out:
        logging.info("ret.stdout: {}".format(ret.stdout))
    if ret.stderr:
        logging.warning("ret.stderr: {}".format(ret.stderr))
    return ret.returncode, ret.stdout, ret.stderr


class ProjectRepo:
    """project repo update"""

    def __init__(self, **kwargs):
        """param init"""
        self.kwargs = kwargs
        self.guser = self.kwargs["guser"]
        self.gpwd = self.kwargs["gpwd"]
        self.backend_ip = self.kwargs["backend_ip"]
        self.backend_user = self.kwargs["backend_user"]
        self.backend_pwd = self.kwargs["backend_pwd"]
        self.project = self.kwargs["project"]
        self.all = self.kwargs["all"]
        self.repo_update_script = self.kwargs["repo_update_script"]
        self.published_repo_list = []   # published repository list   eg: [standard_aarch64, standard_x86_64]
        self.succeeded_pkg_dict = {}
        self.failed_pkg_dict = {}

    def parse_build_result(self):
        """parse build result, update project status and packages status"""
        cmd = f"osc results {self.project} --xml"
        _, out, _ = run(cmd)
        if self.project not in out:
            logging.error(f"parse {self.project} build result failed!")
            return False

        root = ET.fromstring(out)
        for repo_result in root:
            repo = repo_result.attrib["repository"]       # "standard_x86_64", "standard_aarch64"
            build_status = repo_result.attrib["code"]     # "published"

            # if published, append self.published_repo_list
            if build_status == "published":
                logging.info(f"project: {self.project} repository {repo} is published")
                self.published_repo_list.append(repo)

            # update package build result
            succeeded_pkg_list = []
            failed_pkg_list = []
            for pkg_result in repo_result:
                pkg_name = pkg_result.attrib["package"]
                pkg_status = pkg_result.attrib["code"]
                if pkg_status == "succeeded":
                    succeeded_pkg_list.append(pkg_name)
                elif pkg_status == "failed":
                    failed_pkg_list.append(pkg_name)

            if succeeded_pkg_list:
                self.succeeded_pkg_dict[repo] = succeeded_pkg_list
            if failed_pkg_list:
                self.failed_pkg_dict[repo] = failed_pkg_list

        logging.info(f"succeeded_pkg_dict: {self.succeeded_pkg_dict}")
        logging.info(f"failed_pkg_dict: {self.failed_pkg_dict}")
        return True

    def check_project_is_published(self):
        """check project repository is published or not"""
        try:
            if not self.parse_build_result():
                return False
        except Exception as e:
            logging.error(f"parse {self.project} build result Exception: {e}")
            return False
        if self.published_repo_list:
            return True
        return False

    def update_repo(self):
        """update repo for project"""
        update_flag = True
        if not self.published_repo_list:
            return update_flag
        for repo in self.published_repo_list:
            succeeded_pkg_list = self.succeeded_pkg_dict.get(repo, [])
            if not succeeded_pkg_list:
                continue
            pkgs = " ".join(succeeded_pkg_list)
            arch = repo.replace("standard_", "")
            cmd = f"./{self.repo_update_script} -up True -a {self.all} -cmp True -p {self.project} -repo {repo} " \
                  f"-arch {arch} -rsip {self.backend_ip} -rsu {self.backend_user} -rsup {self.backend_pwd} " \
                  f"-guser {self.guser} -gpwd {self.gpwd} --pkglist "
            cmd += pkgs
            code, out, err = run(cmd)
            if code:
                logging.error(f"{self.project} {repo} {pkgs} update repo failed!")
                update_flag = False

            run("rm -rf /tmp/tmp.*")
        return update_flag


if __name__ == "__main__":
    par = argparse.ArgumentParser()
    par.add_argument("-u", "--guser", default="", help="gitee user", required=True)
    par.add_argument("-p", "--gpwd", default="", help="gitee password", required=True)
    par.add_argument("-ip", "--backend_ip", default="", help="obs backend_ip", required=True)
    par.add_argument("-bu", "--backend_user", default="", help="backend user", required=True)
    par.add_argument("-bp", "--backend_pwd", default="", help="backend password", required=True)
    par.add_argument("-s", "--repo_update_script", default="", help="repo update script", required=True)
    par.add_argument("-prj", "--project", default="", nargs="+", help="obs project", required=True)
    par.add_argument("-a", "--all", default="False", help="update package all rpm", required=False)
    args = par.parse_args()

    kw = {
        "guser": args.guser,
        "gpwd": args.gpwd,
        "backend_ip": args.backend_ip,
        "backend_user": args.backend_user,
        "backend_pwd": args.backend_pwd,
        "repo_update_script": args.repo_update_script,
        "all": args.all,
    }

    exit_code = 0
    for project in args.project:
        kw["project"] = project
        project_repo = ProjectRepo(**kw)
        if project_repo.check_project_is_published():
            if not project_repo.update_repo():
                exit_code = 1
    exit(exit_code)
