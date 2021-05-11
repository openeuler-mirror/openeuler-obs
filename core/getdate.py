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
import calendar
import subprocess
current_path = os.path.join(os.path.split(os.path.realpath(__file__))[0])
sys.path.append(os.path.join(current_path, ".."))
from common.common import Pexpect
from common.log_obs import log
from concurrent.futures import ThreadPoolExecutor

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
            if rpm.decode("utf-8").replace('\r\n', '') != ": ":
                rpmlist.append(rpm.decode("utf-8").replace('\r\n', ''))
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
        cmd = "show -s --format=%ad"
        pkg_dir = os.path.join(self.realdir, rpm)
        show_result = self.cmd.ssh_cmd("git -C %s %s" % (pkg_dir, cmd))
        log.info("%s : %s" % (rpm, show_result[1].decode("utf-8").replace('\r\n', '')))
        str_day = show_result[1].decode("utf-8").replace('\r\n', '').split()[2]
        year = show_result[1].decode("utf-8").replace('\r\n', '').split()[4]
        timestr = show_result[1].decode("utf-8").replace('\r\n', '').split()[3]
        eng_month = show_result[1].decode("utf-8").replace('\r\n', '').split()[1]
        int_month = list(calendar.month_abbr).index(eng_month)
        day = self._get_two_digis(int(str_day))
        month = self._get_two_digis(int_month)
        log.info("year:%s month:%s day:%s timestr:%s" % (year, month, day, timestr))
        datestr = year + month + day + ' ' + timestr.replace(':', '-')
        log.info(datestr)
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
        print(self.pkg_time)

    def _echo_to_git_thread(self):
        """
        use the thread pool to echo time str
        """
        all_time = self.pkg_time
        with ThreadPoolExecutor(10) as executor:
            for rpm, time in all_time.items():
                time_args = [rpm, time]
                executor.submit(self._echo_to_obs_pkg_rpms, time_args)

    def _clone_obs_pkg_rpms(self):
        """
        clone the obs_pkg_rpms repository
        """
        clone_path = os.getcwd()
        log.info("Git clone the obs_pkg_rpms %s" % clone_path)
        remove_git = os.popen("rm -rf ./obs_pkg_rpms").read()
        log.info("rm result: %s" % remove_git)
        repo_url = "https://%s:%s@gitee.com/unsunghero/obs_pkg_rpms" \
                % (self.giteeuser, self.giteeuserpwd)
        clone_cmd = "git clone --depth=1 %s" % repo_url
        for i in range(5):
            clone_result = subprocess.getstatusoutput(clone_cmd)
            log.info(clone_result)
            if clone_result[0] == 0:
                clone_flag = "yes"
                break
            else:
                rm_repo = os.popen("rm -rf obs_pkg_rpms").read()
        if clone_flag != "yes":
            raise SystemExit('Please check you internet!!!!!')

    def _echo_to_obs_pkg_rpms(self, all_time):
        """
        echo the time str to a package
        all_time: the list for rpm name and timestr
        """
        echo_cmd = "echo %s > ./obs_pkg_rpms/%s/%s" % (all_time[1], \
                self.branch, all_time[0])
        log.info(echo_cmd)
        cmd_result = os.system(echo_cmd)
        if cmd_result != 0:
            raise SystemExit("This %s echo error to %s" % (all_time[0], self.branch))
            
    def _push_to_pkg_rpms(self):
        """
        push the latest obs_pkg_rpms to origin
        """
        for i in range(5):
            push_cmd = "cd obs_pkg_rpms && git add * && \
                    git commit -m 'update for package' && git push && cd -"
            push_result = subprocess.getstatusoutput(push_cmd)
            log.info(push_result)
            if "nothing to commit" in push_result[1]:
                sys.exit("SUCCESS:All the package date in <<%s>> 
                        already be latest!!" % self.branch)
            elif push_result[0] == 0:
                sys.exit("SUCCESS:Push success for latest date to obs_pkg_rpms")
            else:
                log.debug("Try Push to obs_pkg_rpms: %s" % i)
        raise SystemExit("Failed: Push to obs_pkg_rpms failed")

    def update_to_obs_pkg_rpms(self):
        """
        Assemble all the processes that get the latest data
        """
        self._clone_obs_pkg_rpms()
        self._get_all_time_thread()
        self._echo_to_git_thread()
        self._push_to_pkg_rpms()

if __name__ == "__main__":
    
    kw = {'branch': "master",
            'source_server_user': "root",
            'source_server_ip': "127.0.0.1",
            'source_server_pwd': "112233",
            'source_server_port': "2222",
            'gitee_user': "***",
            'gitee_pwd': "***"}
    get = GETDate(**kw)
    get.update_to_obs_pkg_rpms()
