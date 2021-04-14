#!/bin/env python3
# -*- encoding=utf8 -*-
#******************************************************************************
# Copyright (c) Huawei Technologies Co., Ltd. 2021-2021. All rights reserved.
# licensed under the Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#     http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY OR FIT FOR A PARTICULAR
# PURPOSE.
# See the Mulan PSL v2 for more details.
# Author: yaokai
# Create: 2021-03-19
# ******************************************************************************
"""
check the format and URL of the service file
"""
import os
import sys
from common.log_obs import log
from xml.etree import ElementTree as ET

class CheckMetaPull(object):
    """
    Check the format of the service file and the correctness of its URL
    """
    def __init__(self, **kwargs):
        """
        kawrgs:dict,init dict by 'a': 'A' style
        prid: the pullrequest id
        """
        self.kwargs = kwargs
        self.prid = self.kwargs['pr_id']

    def _clean(self):
        """
        Cleanup the current directory of obs_meta
        """
        cmd = "if [ -d obs_meta ];then rm -rf obs_meta && echo 'Finish clean the obs_meta';fi"
        rm_result = os.popen(cmd).readlines()
        log.info(rm_result)

    def _get_latest_obs_meta(self):
        """
        Get the latest obs_meta
        """
        log.info("Get the latest obs_meta")
        clone_cmd = "git clone --depth=1 https://gitee.com/src-openeuler/obs_meta"
        for x in range(5):
            log.info("Try to clone %s" % x)
            clone_result = ""
            pull_result = ""
            clone_result = os.popen(clone_cmd).readlines()
            pull_result = os.popen("if [ -d obs_meta ];then echo 'Already up to date'; \
                    else echo 'Clone error';fi").readlines()
            if "Already" in pull_result[0]:
                log.info(pull_result)
                log.info("Success to clone obs_meta")
                break
            else:
                os.popen("if [ -d obs_meta ];then rm -rf obs_meta")

    def _get_new_pkg(self):
        """
        Gets a list of newly added files in obs_meta
        """
        fetch_cmd = "git fetch origin pull/%s/head:thispr" % self.prid
        branch_cmd = "git branch -a | grep 'thispr'"
        checkout_cmd = "git checkout thispr"
        changed_file_cmd = "git log --name-status -1"
        for x in range(5):
            os.chdir("obs_meta")
            fetch_result = os.popen(fetch_cmd).read()
            log.info(fetch_result)
            branch_result = os.popen(branch_cmd).readlines()
            if branch_result:
                log.info(branch_result)
                break
            else:
                os.chdir("../")
                self._clean()
                self._get_latest_obs_meta()
        show_result = os.popen(checkout_cmd).readlines()
        log.info(show_result)
        changed_file_result = os.popen(changed_file_cmd).readlines()
        log.info(changed_file_result)
        new_pkg_path = []
        for pkg in changed_file_result:
            if "A\t" in pkg:
                all_msg = pkg.replace("\n", "")
                log.info(all_msg)
                pkg_path = all_msg.replace("A\t", "")
                new_pkg_path.append(pkg_path)
        log.info("All_change_pkg:%s" % new_pkg_path)
        if not new_pkg_path:
            log.info("There have no Package add")
            sys.exit()
        else:
            return new_pkg_path

    def _check_pkg_services(self, pkg_path_list):
        """
        Function modules: Check the format of the service file and the correctness of its URL
        """
        error_flag = ""
        service_flag = "" 
        for pkg_path in pkg_path_list:
            if "_service" in pkg_path:
                service_flag = "exist"
                try:
                    ET.parse(pkg_path)
                    log.info("**************FORMAT CORRECT***************")
                    log.info("The %s has a nice _service" % pkg_path)
                    log.info("**************FORMAT CORRECT***************")
                except Exception as e:
                    log.error("**************FORMAT ERROR*****************")
                    log.error("MAY be %s has a bad _service format" % pkg_path)
                    log.error("%s/_service format bad Because:%s" % (pkg_path, e))
                    log.error("**************FORMAT ERROR*****************")
                    error_flag = "yes"
                service_path = pkg_path
                url_result = ""
                with open(service_path, "r") as f:
                    log.info('\n' + f.read())
                    f.seek(0, 0)
                    for url in f.readlines():
                        if "name=\"url\"" in url.replace("\n", ""):
                            all_url = url.replace("\n", "").split('/')
                            #log.info(all_url)
                            spkg_name = all_url[-2].replace("<", "")
                            spkg_url = all_url[-3]
                            pkg_name = pkg_path.split('/')[-2]
                            pkg_url = pkg_path.split('/')[0]
                            log.info("Service_pkgname:%s" % spkg_name)
                            log.info("Service_pkgurl:%s" % spkg_url)
                            log.info("Pkgname:%s" % pkg_name)
                            log.info("Pkg_url:%s" % pkg_url)
                            if spkg_url == "openEuler" and pkg_url == "master":
                                if spkg_name == pkg_name:
                                    log.info("Yes:The %s in _service url is correct" % pkg_name)
                                else:
                                    log.error("**************_Service URL ERROR*****************")
                                    log.error("FAILED The %s in _service pkgname is not same" % pkg_name)
                                    error_flag = "yes"
                            elif spkg_url == pkg_url:
                                if spkg_name == pkg_name:
                                    log.info("Yes:The %s in _service url is correct" % pkg_name)
                                else:
                                    log.error("**************_Service URL ERROR*****************")
                                    log.error("FAILED The %s in _service pkgname is not same" % pkg_name)
                                    error_flag = "yes"
                            else:
                                log.error("**************_Service URL ERROR*****************")
                                log.error("FAILED You need to check your %s _service again" % pkg_name)
                                error_flag = "yes"
                            break
        os.chdir("../")
        self._clean()
        if error_flag == "yes":
            raise SystemExit("*******PLEASE CHECK AGAIN*******")
        if service_flag == "":
            log.info("There has no pkg add to project")

    def do_all(self):
        """
        Assemble all inspection processes and provide external interfaces
        """
        self._clean()
        self._get_latest_obs_meta()
        changelist = self._get_new_pkg()
        self._check_pkg_services(changelist)
