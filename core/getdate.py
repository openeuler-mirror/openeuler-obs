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
# Create: 2021/5/11
# ******************************************************************************
"""
get the latest date to obs_pkg_rpms
"""
import os
import sys
import shutil
import calendar
current_path = os.path.join(os.path.split(os.path.realpath(__file__))[0])
sys.path.append(os.path.join(current_path, ".."))
from common.common import Pexpect, run
from common.log_obs import log
from concurrent.futures import ThreadPoolExecutor
from common.parser_config import ParserConfigIni


class GETDate(object):
    """
    get the latest date to obs_pkg_rpms
    """
    def __init__(self, **kwargs):
        """
        kwargs: dict, init dict by 'a': 'A' style
        The dict key_value as the following:
            branch: which you wangt to get the package date from
            source_server_user: The user name for you use in server
            source_server_pwd: The password for your ip
            source_server_port: The port for your ip
            giteeuser: The gitee account
            giteeuserpwd: The gitee passwd
        """
        self.branch = kwargs["branch"]
        self.cmd = Pexpect(kwargs["source_server_user"],
                kwargs["source_server_ip"],
                kwargs["source_server_pwd"],
                kwargs["source_server_port"])
        self.giteeuser = kwargs["gitee_user"]
        self.giteeuserpwd = kwargs["gitee_pwd"]
        self.sourcedir = "/srv/cache/obs/tar_scm/repo/next/"
        par = ParserConfigIni()
        self.obs_pkg_rpms_url = par.get_repos_dict()["obs_pkg_rpms"]
        self.gitee_repo_name = self.obs_pkg_rpms_url.split('/')[-1]
        self.pkg_time = {}
        self.realdir = None

    def _get_realdir(self):
        """
        get the path where the branch in
        """
        if self.branch == "master":
            realbranch = "openEuler"
        else:
            realbranch = self.branch
        branchdir = os.path.join(self.sourcedir, realbranch)
        self.realdir = branchdir
        return branchdir

    def _get_branch_rpmlist(self, realdir):
        """
        get the rpmlist for corresponding branch
        """
        rpmlist = []
        log.info("rpmlist_dir: %s" % realdir)
        cmd = "ls %s" % realdir 
        cmd_result = self.cmd.ssh_cmd(cmd)
        log.info("ssh_cmd_for_ls: %s" % cmd_result)
        for rpm in cmd_result:
            tmp = rpm.decode("utf-8").replace('\r\n', '')
            if tmp != ": ":
                rpmlist.append(tmp)
        log.info("rpmlist: %s", ",".join(rpmlist))
        return rpmlist

    def _get_two_digis(self, int_num):
        """
        make one digit into two digits
        """
        if int_num < 10:
            str_num = "0" + str(int_num)
        else:
            str_num = str(int_num)
        return str_num
    
    def _get_latest_time(self, rpm):
        """
        get a fixed format date
        rpm: which package you want to get
        """
        pkg_dir = os.path.join(self.realdir, rpm)
        res = "show -s --format=%ad --date=local"
        cmd = f"git -C {pkg_dir} {res}"
        show_result = self.cmd.ssh_cmd(cmd)
        log.info("%s : %s" % (rpm, show_result[1].decode("utf-8").replace('\r\n', '')))
        result_list = show_result[1].decode("utf-8").replace('\r\n', '').split()
        int_month = list(calendar.month_abbr).index(result_list[1])
        month = self._get_two_digis(int_month)
        day = self._get_two_digis(int(result_list[2]))
        timestr = result_list[3].replace(':', '-')
        year = result_list[4]
        datestr = year + month + day + ' ' + timestr
        log.info("%s : %s" % (rpm, datestr))
        self.pkg_time[rpm] = datestr

    def _get_all_time_thread(self):
        """
        use the thread pool to get the time
        """
        realdir = self._get_realdir()
        rpmlist = self._get_branch_rpmlist(realdir)
        with ThreadPoolExecutor(10) as executor:
            for pkg in rpmlist:
                executor.submit(self._get_latest_time, pkg)
        log.info(self.pkg_time)

    def _echo_to_git_thread(self):
        """
        use the thread pool to echo time str
        """
        with ThreadPoolExecutor(10) as executor:
            for rpm, time in self.pkg_time.items():
                time_args = [rpm, time]
                executor.submit(self._echo_to_obs_pkg_rpms, time_args)

    def _clone_obs_pkg_rpms(self):
        """
        clone the obs_pkg_rpms repository
        """
        log.info("Git clone the %s" % self.gitee_repo_name)
        repo_path = os.path.join(os.getcwd(), self.gitee_repo_name)
        if os.path.exists(repo_path):
            shutil.rmtree(repo_path)
        tmp = self.obs_pkg_rpms_url.split("//")
        repo_url = "%s//%s:%s@%s" % (tmp[0], self.giteeuser, self.giteeuserpwd, tmp[1])
        clone_cmd = "git clone --depth=1 %s" % repo_url
        clone_flag = False
        for i in range(5):
            clone_result, _, _ = run(clone_cmd)
            log.info(clone_result)
            if clone_result == 0:
                clone_flag = True
                break
            else:
                if os.path.exits(repo_path):
                   shutil.rmtree(repo_path)
        if not clone_flag:
            raise SystemExit('Please check you internet!!!!!')

    def _echo_to_obs_pkg_rpms(self, all_time):
        """
        echo the time str to a package
        all_time: the list for rpm name and timestr
        """
        echo_cmd = "echo %s > ./%s/%s/%s" % (all_time[1], \
                self.gitee_repo_name, self.branch, all_time[0])
        log.info(echo_cmd)
        cmd_result, _, _ = run(echo_cmd)
        if cmd_result != 0:
            raise SystemExit("This %s echo error to %s" % (all_time[0], self.branch))
            
    def _push_to_pkg_rpms(self):
        """
        push the latest obs_pkg_rpms to origin
        """
        os.chdir(self.gitee_repo_name)
        status_cmd = "git status -s"
        commit_cmd = "git add -A && git commit -m 'update for package'"
        _, result, _ = run(status_cmd)
        if result:
            result, _, _ = run(commit_cmd)
            if result == 0:
                for i in range(5):
                    push_cmd = "git push -f"
                    push_result, _, _ = run(push_cmd)
                    log.info(push_result)
                    if push_result == 0:
                        log.info("SUCCESS:Push success for latest date to %s" % self.gitee_repo_name)
                        return
                    else:
                        log.debug("Try Push to %s: %s" % (self.gitee_repo_name, i))
                raise SystemExit("Failed: Push failed")
            else:
                raise SystemExit("Failed: git add and commit failed")
        else:
            log.info("NO CHAGE,nothing to commit")

    def update_to_obs_pkg_rpms(self):
        """
        Assemble all the processes that get the latest data
        """
        self._clone_obs_pkg_rpms()
        self._get_all_time_thread()
        self._echo_to_git_thread()
        self._push_to_pkg_rpms()
