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
# Create: 2020-10-22
# ******************************************************************************
"""
save package info
"""

import csv
import os
import sys
import time
import threadpool

current_path = os.path.join(os.path.split(os.path.realpath(__file__))[0])
sys.path.append(os.path.join(current_path, ".."))
from common.log_obs import log
from common.parser_config import ParserConfigIni
from common.common import git_repo_src


class SaveInfo(object):
    """
    save info
    """
    def __init__(self, gitee_user, gitee_pwd):
        """
        init
        """
        parc = ParserConfigIni()
        self.file_name = parc.get_package_info_file()
        self.branch_prj = parc.get_branch_proj()
        self.obs_pkg_rpms_url = parc.get_repos_dict()["obs_pkg_rpms"]
        self.obs_pkg_rpms_files_dir = None
        self.gitee_user = gitee_user
        self.gitee_pwd = gitee_pwd

    def _download(self):
        """
        download obs_pkg_rpms
        """
        tmpdir = os.popen("mktemp").read().split("\n")[0]
        self.obs_pkg_rpms_files_dir = git_repo_src(self.obs_pkg_rpms_url, self.gitee_user, self.gitee_pwd, tmpdir)

    def _delete(self):
        """
        delete obs_pkg_rpms
        """
        cmd = "rm -rf %s" % self.obs_pkg_rpms_files_dir
        os.system(cmd)

    def save_unsync_package(self, package_name, branch_name):
        """
        save info
        package_name: package which is not be updated
        branch_name: branch of package
        """
        self._download()
        try:
            timestr = time.strftime("%Y%m%d %H-%M-%S", time.localtime())
            file_path = os.path.join(self.obs_pkg_rpms_files_dir, "unsync.csv")
            log.info("package: %s, branch: %s" % (package_name, branch_name))
            with open(file_path, 'a') as f:
                csv_writer = csv.writer(f)
                csv_writer.writerow([timestr, package_name, branch_name])
            cmd="cd %s && git add * && git commit -m 'update package info' && git push" % self.obs_pkg_rpms_files_dir
            os.system(cmd)
        except AttributeError as e:
            log.error(e)
        finally:
            self._delete()

    def _save_latest_info_by_pkg(self, datestr_root_path, prj, pkg, file_list, f_csv):
        """
        save latest info of package
        """
        if pkg in file_list:
            cmd = "cat %s/%s" % (datestr_root_path, pkg)
            log.debug(cmd)
            timestr = os.popen(cmd).read().replace("\n", "")
        else:
            timestr = 0
        cmd = "osc list -b %s %s|grep rpm" % (prj, pkg)
        log.debug(cmd)
        rpms = ' '.join(list(set(os.popen(cmd).read().replace(" ", "").split("\n")) - set([''])))
        f_csv.writerow([timestr, pkg, rpms])

    def save_latest_info(self, branch_name):
        """
        save latest info of package, include update time of package code and rpms
        """
        self._download()
        try:
            datestr_root_path = os.path.join(self.obs_pkg_rpms_files_dir, branch_name)
            if not os.path.exists(datestr_root_path):
                os.makedirs(datestr_root_path)
            with open("%s.csv" % datestr_root_path, "w") as f:
                f_csv = csv.writer(f)
                file_list = os.listdir(datestr_root_path)
                prj_list = self.branch_prj[branch_name].split(" ")
                log.debug(prj_list)
                for prj in prj_list:
                    cmd = "osc list %s" % prj
                    log.debug(cmd)
                    pkgs = os.popen(cmd).read().split("\n")
                    var_list = []
                    for pkg in pkgs:
                        var_list.append(([datestr_root_path, prj, pkg, file_list, f_csv], None))
                try:
                    pool = threadpool.ThreadPool(20)
                    requests = threadpool.makeRequests(self._save_latest_info_by_pkg, var_list)
                    for req in requests:
                        pool.putRequest(req)
                    pool.wait()
                except KeyboardInterrupt as e:
                    log.error(e)
            cmd = "sort -u -r %s.csv > tmp && cat tmp > %s.csv" % (datestr_root_path, datestr_root_path)
            if os.system(cmd) != 0:
                log.error("sort file fail")
            cmd = "cd %s && git pull && git add %s.csv && git commit -m 'update file' && git push" % \
                    (self.obs_pkg_rpms_files_dir, datestr_root_path)
            os.system(cmd)
        except AttributeError as e:
            log.error(e)
        finally:
            self._delete()


if __name__ == "__main__":
    s  = SaveInfo("xxx", "xxx")
    s.save_unsync_package("vim", "master")
    s.save_latest_info("openEuler-20.03-LTS-SP1")

