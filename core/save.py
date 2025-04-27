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
import yaml
import json
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
    def __init__(self, gitee_user, gitee_pwd, build_type):
        """
        init
        """
        parc = ParserConfigIni()
        self.file_name = parc.get_package_info_file()
        self.branch_prj = parc.get_branch_proj()
        self.obs_pkg_rpms_url = parc.get_repos_dict()["obs_pkg_rpms"]
        self.release_management_url = parc.get_repos_dict()["release_management"]
        self.obs_pkg_rpms_files_dir = None
        self.release_management_files_dir = None
        self.gitee_user = gitee_user
        self.gitee_pwd = gitee_pwd
        self.build_type = build_type
        self.csv_data = []

    def _download(self):
        """
        download obs_pkg_rpms
        """
        tmpdir = os.popen("mktemp").read().split("\n")[0]
        self.obs_pkg_rpms_files_dir = git_repo_src(self.obs_pkg_rpms_url, self.gitee_user, self.gitee_pwd, tmpdir)

    def _download_release_management(self):
        """
        download release-management
        """
        tmpdir = os.popen("mktemp").read().split("\n")[0]
        self.release_management_files_dir = git_repo_src(self.release_management_url, self.gitee_user, self.gitee_pwd, tmpdir)

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
            for i in range(5):
                if os.system(cmd) == 0:
                    break
        except AttributeError as e:
            log.error(e)
        finally:
            self._delete()

    def _get_pkg_rpmlist(self, prj, pkg):
        """
        get pkg rpms
        """
        tmp_pkg = pkg
        if pkg == "kernel":
            tmp_pkg = pkg + ":" + pkg
        cmd = f"ccb ls -p {prj} {tmp_pkg} 2>/dev/null | grep \"\.rpm\""
        log.debug(cmd)
        res=os.popen(cmd).read()
        rpms = ""
        if res:
            rpmlist = sorted(list(set(res.replace(" ", "").replace('"', '').replace(",", "").split("\n")) - set([''])))
            rpms = ' '.join(rpmlist)
        return rpms

    def _save_latest_info_specified(self, prj_list, latest_rpm_file):
        """
        save latest info of specified
        """
        for prj in prj_list:
            cmd = f"ccb select builds status=201,202 -f _id,create_time,build_type os_project={prj} build_target.architecture=x86_64 --sort create_time:desc --size 1 2>/dev/null"
            log.debug(cmd)
            res = os.popen(cmd).read()
            if res:
                data = json.loads(res)
                bt = data[0]['_source']['build_type']
                if bt == "specified":
                    log.info("build_type:%s" % bt)
                    code_update_time = data[0]['_source']['create_time'].partition('.')[0].replace("T", " ").replace("-", "").replace(":", "-")
                    log.info("code_update_time:%s" % code_update_time)
                    build_id = data[0]['_id']
                    log.info("build_id:%s" % build_id)

                    cmd = f"ccb select builds _id={build_id} -f select_pkgs"
                    log.debug(cmd)
                    res = os.popen(cmd).read()
                    if res:
                        result = json.loads(res)
                        select_pkgs = result[0]['_source']['select_pkgs']
                        log.info("select_pkgs:%s" % select_pkgs)
                        for pkg in select_pkgs:
                            rpms = self._get_pkg_rpmlist(prj, pkg)
                            str_info = f"{code_update_time},{pkg},${rpms}"
                            cmd = "sed -i '/,%s,/d' %s" % (pkg, latest_rpm_file)
                            ret = os.system(cmd)
                            log.info("ret: %s" % ret)
                            cmd = "sed -i '$a\%s\r\n' %s" % (str_info, latest_rpm_file)
                            ret = os.system(cmd)
                            log.info("ret: %s" % ret)
                else:
                    log.info("The last build of the %s project is not specified, but %s" % (prj, bt))

    def _save_latest_info_by_pkg(self, prj, pkg, code_update_time):
        """
        save latest info of package
        """
        if code_update_time == 0 or code_update_time:
            rpms = self._get_pkg_rpmlist(prj, pkg)
            data_list = [code_update_time, pkg, rpms]
            self.csv_data.append(data_list)

    def save_latest_info(self, branch_name):
        """
        save latest info of package, include update time of package code and rpms
        """
        self._download()
        code_update_time = 0
        try:
            prj_list = self.branch_prj[branch_name].split(" ")
            log.debug(prj_list)
            latest_rpm_file = os.path.join(self.obs_pkg_rpms_files_dir, "latest_rpm", "%s.csv" % branch_name)
            if self.build_type == "specified":
                self._save_latest_info_specified(prj_list, latest_rpm_file)
            else:
                for prj in prj_list:
                    var_list = []
                    pkg_list = []
                    cmd = f"ccb select builds build_type=full,incremental status=201,202 -f create_time,build_type os_project={prj} build_target.architecture=x86_64 --sort create_time:desc --size 1 2>/dev/null"
                    log.debug(cmd)
                    res = os.popen(cmd).read()
                    if res:
                        data = json.loads(res)
                        code_update_time = data[0]['_source']['create_time'].partition('.')[0].replace("T", " ").replace("-", "").replace(":", "-")
                        bt = data[0]['_source']['build_type']
                        log.info("code_update_time:%s" % code_update_time)
                        log.info("build_type:%s" % bt)

                        cmd = f"ccb select projects os_project={prj} submit_order -f my_specs 2>/dev/null | grep spec_url"
                        log.debug(cmd)
                        res = os.popen(cmd).read().split("\n")
                        spec_url = [x for x in res if x != '']
                        if spec_url:
                            for url in spec_url:
                                p = url.split("/")[-1].split(".git")[0]
                                if p not in pkg_list:
                                    pkg_list.append(p)
                        else:
                            if not self.release_management_files_dir:
                                self._download_release_management()
                            if "epol" in prj.lower():
                                standard_dirs = ['epol']
                            else:
                                standard_dirs = ['everything-exclude-baseos', 'baseos']
                            release_management_path = os.path.join(self.release_management_files_dir, branch_name)
                            for c_dir in standard_dirs:
                                yaml_path = os.path.join(release_management_path, c_dir, 'pckg-mgmt.yaml')
                                if os.path.exists(yaml_path):
                                    with open(yaml_path, 'r', encoding='utf-8') as f:
                                        result = yaml.safe_load(f)
                                    for line in result['packages']:
                                        name = line.get("name")
                                        if name not in pkg_list:
                                            pkg_list.append(name)
                    for pkg in pkg_list:
                        var_list.append(([prj, pkg, code_update_time], None))
                    try:
                        pool = threadpool.ThreadPool(20)
                        requests = threadpool.makeRequests(self._save_latest_info_by_pkg, var_list)
                        for req in requests:
                            pool.putRequest(req)
                        pool.wait()
                    except KeyboardInterrupt as e:
                        log.error(e)

            with open(latest_rpm_file, 'w', newline='', encoding='utf-8') as f:
                f_csv = csv.writer(f)
                for line in self.csv_data:
                    f_csv.writerow(line)
            cmd = f"sort -u -r {latest_rpm_file} -o {latest_rpm_file}"
            if os.system(cmd) != 0:
                log.error("sort file fail")
            cmd = f"cd {self.obs_pkg_rpms_files_dir} && git pull && git add * && git commit -m 'update file' && git push"
            log.debug(cmd)
            for i in range(5):
                if os.system(cmd) == 0:
                    break
        except AttributeError as e:
            log.error(e)
        finally:
            self._delete()


if __name__ == "__main__":
    s  = SaveInfo("xxx", "xxx")
    s.save_unsync_package("vim", "master")
    s.save_latest_info("openEuler-20.03-LTS-SP1")
