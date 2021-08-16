#!/bin/env python3
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
# Author: yaokai
# Create: 2021/8/04
# ******************************************************************************
"""
check the software package for the corresponding project of thecorresponding branch of source
"""
import os
import sys
import yaml
import requests
Now_path = os.path.join(os.path.split(os.path.realpath(__file__))[0])
sys.path.append(os.path.join(Now_path, ".."))
from common.log_obs import log
from common.common import git_repo_src

class CheckReleaseManagement(object):
    """
    The entrance check for release-management
    """
    def __init__(self, **kwargs):
        """
        kawrgs: dict,init dict by 'a': 'A' style
        prid: the pullrequest id
        meta_path: The path for obs_meta
        manage_path : The path for release_management_path
        """
        self.kwargs = kwargs
        self.prid = self.kwargs['pr_id']
        self.current_path = os.getcwd()
        self.meta_path = self.kwargs['obs_meta_path']
        self.manage_path = self.kwargs['release_management_path']
        self.giteeuser = self.kwargs['gitee_user']
        self.giteeuserpwd = self.kwargs['gitee_pwd']

    def _clean(self, pkgname):
        """
        remove the useless pkg dir
        """
        cmd = "if [ -d {0} ];then rm -rf {0} && echo 'Finish clean the {0}';fi".format(pkgname)
        rm_result = os.popen(cmd).readlines()
        log.info(rm_result)

    def _get_latest_git_repo(self, owner, pkgname):
        """
        get the latest git repo
        """
        os.chdir(self.current_path)
        rpm_url = "https://gitee.com/{0}/{1}".format(owner, pkgname)
        pkg_path = git_repo_src(rpm_url, self.giteeuser, self.giteeuserpwd)
        if pkg_path:
            log.info("{0}:{1}".format(pkgname, pkg_path))
            return pkg_path
        else:
            raise SystemExit("Error:{0} Clone-error,Please check yournet.".format(pkgname))

    def _get_repo_change_file(self, owner=None, pkgname=None, repo_path=None):
        """
        Obtain the change for latest commit
        """
        changed_file_cmd = "git diff --name-status HEAD~1 HEAD~0"
        get_fetch = None
        if not repo_path:
            self._clean(pkgname)
            release_path = self._get_latest_git_repo(owner, pkgname)
            self.manage_path = release_path
            os.chdir(release_path)
        else:
            os.chdir(repo_path)
        fetch_cmd = "git fetch origin pull/%s/head:thispr" % self.prid
        checkout_cmd = "git checkout thispr"
        for x in range(5):
            fetch_result = os.system(fetch_cmd)
            checkout_result = os.system(checkout_cmd)
            log.debug(fetch_result)
            log.debug(checkout_result)
            if fetch_result == 0 and checkout_result == 0:
                get_fetch = True
                break
            else:
                os.chdir(self.current_path)
                self._clean(pkgname)
                path_release = self._get_latest_git_repo(owner, pkgname)
                os.chdir(path_release)
        changed_file = os.popen(changed_file_cmd).readlines()
        if get_fetch and changed_file:
            log.info(changed_file)
            return changed_file
        else:
            raise SystemExit("Error:can not obtain the content for this commit")

    def _parse_commit_file(self, change_file):
        """
        get the change file for latest commit
        """
        new_file_path = []
        for line in change_file:
            log.info("line:%s" % line)
            log_list = list(line.split())
            temp_log_type = log_list[0]
            if len(log_list) == 3:
                if "pckg-mgmt.yaml" in log_list[2]:
                    new_file_path.append(log_list[2])
            elif len(log_list) == 2:
                if temp_log_type != "D" and "pckg-mgmt.yaml" in log_list[1]:
                    new_file_path.append(log_list[1])
        if new_file_path:
            log.info(new_file_path)
            return new_file_path
        else:
            log.info("There are no file need to check!!!")
            sys.exit()

    def _get_yaml_msg(self, yaml_path_list):
        """
        get the pkg msg in pckg-mgmt.yaml
        """
        pack_msg = []
        yaml_msg = {}
        for yaml_path in yaml_path_list:
            pack_msg.clear()
            file_path = os.path.join(self.manage_path, yaml_path)
            with open(file_path, 'r', encoding='utf-8')as f:
                result = yaml.load(f, Loader=yaml.FullLoader)
            all_pack_msg = result['packages']['natural']
            for msg in all_pack_msg:
                pack_msg.append(os.path.join(msg['branch_from'], msg['obs_from'], msg['name']))
            yaml_msg[yaml_path] = pack_msg
        return yaml_msg
    
    def _check_pkg_from(self, yaml_path_list, meta_path, yaml_msg):
        """
        Detects the existence of file contents
        """
        error_flag = False
        for yaml_path in yaml_path_list:
            log.debug(yaml_path + ":")
            for pkg_path in yaml_msg[yaml_path]:
                pkg_dir_path = os.path.join(meta_path, pkg_path)
                if not os.path.exists(pkg_dir_path):
                    log.error("The {0} not exist in obs_meta".format(pkg_path))
                    error_flag = True
        if not error_flag:
            log.debug("All rpms exist")
        return error_flag

    def check_pckg_yaml(self):
        """
        check the obs_from branch_from in pckg-mgmt.yaml
        """
        change = self._get_repo_change_file('openeuler', 'release-management', repo_path = self.manage_path)
        change_file = self._parse_commit_file(change)
        yaml_msg = self._get_yaml_msg(change_file)
        error_flag = self._check_pkg_from(change_file, self.meta_path, yaml_msg)
        if error_flag:
            raise SystemExit("Please check your commit")

if __name__ == "__main__":
    kw = {"branch":"master",
            "gitee_user":"",
            "gitee_pwd":"",
            "pr_id":"108",
            "obs_meta_path":"/root/relese-management/openeuler-obs/core/obs_meta",
            "release_management_path":"/root/relese-management/openeuler-obs/core/release-management"}
    check = CheckReleaseManagement(**kw)
    check.check_pckg_yaml()
