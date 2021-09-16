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
import datetime
Now_path = os.path.join(os.path.split(os.path.realpath(__file__))[0])
sys.path.append(os.path.join(Now_path, ".."))
from common.log_obs import log
from collections import Counter
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
        fetch_cmd = "git fetch origin pull/%s/head:thispr" % self.prid
        checkout_cmd = "git checkout thispr"
        get_fetch = None
        if not repo_path:
            self._clean(pkgname)
            release_path = self._get_latest_git_repo(owner, pkgname)
            self.manage_path = release_path
            os.chdir(release_path)
        else:
            os.chdir(repo_path)
        for x in range(5):
            fetch_result = os.system(fetch_cmd)
            checkout_result = os.system(checkout_cmd)
            log.debug("STATUS:{0} and {1}".format(fetch_result, checkout_result))
            if fetch_result == 0 and checkout_result == 0:
                get_fetch = True
                break
            else:
                os.chdir(self.current_path)
                self._clean(pkgname)
                path_release = self._get_latest_git_repo(owner, pkgname)
                os.chdir(path_release)
                self.manage_path = os.path.join(self.current_path, pkgname)
        changed_file = os.popen(changed_file_cmd).readlines()
        if get_fetch and changed_file:
            log.info(changed_file)
            return changed_file
        else:
            raise SystemExit("Error:can not obtain the content for this commit")

    def _rollback_get_msg(self, repo_path):
        """
        rollback to last commit
        """
        os.chdir(repo_path)
        roll = os.system("git reset --hard HEAD^")
        if roll == 0:
            log.info("Already rollback to last commit")
        else:
            raise SystemExit("Error: fail to rollback to last commit")

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

    def _get_yaml_msg(self, yaml_path_list, manage_path, rollback=None):
        """
        get the pkg msg in pckg-mgmt.yaml
        """
        if rollback == True:
            self._rollback_get_msg(manage_path)
        all_pack_msg = {}
        for yaml_path in yaml_path_list:
            file_path = os.path.join(manage_path, yaml_path)
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8')as f:
                    result = yaml.load(f, Loader=yaml.FullLoader)
                all_pack_msg[yaml_path] = result['packages']['natural'] + \
                        result['packages']['recycle'] + result['packages']['delete']
            else:
                all_pack_msg[yaml_path] = []
        return all_pack_msg

    def _check_key_in_yaml(self, all_pack_msg, change_file):
        """
        check the key in your yaml compliance with rules
        """
        error_flag = ""
        keylist = ['branch_from', 'obs_from', 'name', 'branch_to', 'obs_to', 'date']
        for change in change_file:
            log.info("{0} key check".format(change))
            for msg in all_pack_msg[change]:
                if len(msg.keys()) == 6:
                    for key in msg.keys():
                        if key not in keylist:
                            error_flag = True
                            log.error(msg)
                            log.error("ERROR:<<<<<<{0}:>>>>>> should not in there".format(key))
                else:
                     error_flag = True
                     log.error("Please check {0}".format(msg))
        if error_flag:
            raise SystemExit("ERROR: Please ensure the following key values in your yaml")

    def _check_date_time(self, yaml_msg, change_file):
        """
        check date and ensure the date to the same day as the commit time
        """
        error_flag = False
        date = datetime.date.today()
        today = date.day
        for change in change_file:
            log.info("{0} date check".format(change))
            for msg in yaml_msg[change]:
                yaml_date = int(msg['date'].split('-')[2])
                if today != yaml_date:
                    error_flag = True
                    log.error(msg)
                    log.error("Wrong Date: <date:{0}>!!!".format(msg['date']))
        if error_flag:
            log.error("Please set your date to the same day as the commit time!!!")
        return error_flag

    def _check_pkg_from(self, meta_path, yaml_msg, change_file):
        """
        Detects the existence of file contents
        """
        error_flag = False
        for change in change_file:
            log.info("{0} pkg_from check".format(change))
            for msg in yaml_msg[change]:
                msg_path = os.path.join(meta_path, msg['branch_from'],
                        msg['obs_from'], msg['name'])
                if not os.path.exists(msg_path):
                    yaml_key = os.path.join(msg['branch_from'],
                            msg['obs_from'], msg['name'])
                    log.error("The {0} not exist in obs_meta".format(yaml_key))
                    error_flag = True
        return error_flag

    def _get_diff_msg(self, old_msg, new_msg, change_file_list):
        """
        Get the content of this submission
        """
        change_list = {}
        for change in change_file_list:
            change_list[change] = []
            for new in new_msg[change]:
                if new not in old_msg[change]:
                    change_list[change].append(new)
        for change in change_file_list:
            if change_list[change]:
                log.debug("Change in {0}:".format(change))
                for msg in change_list[change]:
                    log.debug(msg)
            else:
                del change_list[change]
                log.info("The are no new msg in {0}!!!".format(change))
        if change_list:
            return change_list
        else:
            log.info("The are no new msg in your yaml!!!")
            sys.exit()

    def _check_yaml_format(self, yaml_path_list, manage_path):
        """
        check the format for the yaml file
        """
        for yaml_path in yaml_path_list:
            manage_yaml_path = os.path.join(manage_path, yaml_path)
            try:
                with open(manage_yaml_path, 'r', encoding='utf-8') as f:
                    result = yaml.load(f, Loader=yaml.FullLoader)
                    log.info("{0} format check".format(yaml_path))
            except Exception as e:
                log.error("**********FORMAT ERROR***********")
                log.error("%s format bad Because:%s" % (yaml_path, e))
                raise SystemExit("May be %s has a bad format" % yaml_path)

    def _check_same_pckg(self, change_file_path, yaml_msg):
        """
        check the repeat pkg for the yaml file
        """
        all_pkg_name = {}
        for change_file in change_file_path:
            pkg_name = []
            log.info("{0} repeat pkg check".format(change_file))
            for msg in yaml_msg[change_file]:
                pkg_name.append(msg['name'])
            dict_pkg_name = dict(Counter(pkg_name))
            repeat_pkg = [key for key, value in dict_pkg_name.items() if value > 1]
            if repeat_pkg:
                all_pkg_name[change_file] = repeat_pkg
        if all_pkg_name:
            log.error("The following packages are duplicated in the YAML files")
            log.error(all_pkg_name)
            return True
        else:
            return False

    def _check_branch_msg(self, change_msg, yaml_path_list, manage_path):
        """
        check the branch msg in your commit
        """
        error_msg = {}
        branch_msg_path = os.path.join(manage_path, "valid_release_branches.yaml")
        with open(branch_msg_path, 'r', encoding='utf-8') as f:
            branch_result = yaml.load(f, Loader=yaml.FullLoader)
        for yaml_path in yaml_path_list:
            log.info("{0} branch check".format(yaml_path))
            error_msg[yaml_path] = []
            yaml_branch = yaml_path.split("/")[-2]
            for msg in change_msg[yaml_path]:
                if msg['branch_to'] == yaml_branch and \
                        msg['branch_from'] in branch_result['branch'].keys() and \
                        msg['branch_to'] in branch_result['branch'][msg['branch_from']]:
                            continue
                else:
                    error_msg[yaml_path].append(msg)
            if not error_msg[yaml_path]:
                del error_msg[yaml_path]
            else:
                log.error("Wrong branch msg in there:")
                for msg in error_msg[yaml_path]:
                    log.error(msg)
        if error_msg:
            return True
        else:
            return False

    def check_pckg_yaml(self):
        """
        check the obs_from branch_from in pckg-mgmt.yaml
        """
        change = self._get_repo_change_file('openeuler',
                'release-management', self.manage_path)
        change_file = self._parse_commit_file(change)
        self._check_yaml_format(change_file, self.manage_path)
        change_yaml_msg = self._get_yaml_msg(change_file, self.manage_path)
        old_yaml_msg = self._get_yaml_msg(change_file, self.manage_path, True)
        change_msg_list = self._get_diff_msg(old_yaml_msg, change_yaml_msg, change_file)
        log.info(len(change_msg_list))
        self._check_key_in_yaml(change_msg_list, change_file)
        error_flag1 = self._check_pkg_from(self.meta_path, change_msg_list, change_file)
        error_flag2 = self._check_date_time(change_msg_list, change_file)
        error_flag3 = self._check_same_pckg(change_file, change_yaml_msg)
        error_flag4 = self._check_branch_msg(change_msg_list, change_file, self.manage_path)
        if error_flag1 or error_flag2 or error_flag3 or error_flag4:
            raise SystemExit("Please check your commit")

if __name__ == "__main__":
    kw = {"branch":"master",
            "gitee_user":"",
            "gitee_pwd":"",
            "pr_id":"108",
            "obs_meta_path":"***",
            "release_management_path":"***"}
    check = CheckReleaseManagement(**kw)
    check.check_pckg_yaml()
