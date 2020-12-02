#!/bin/evn python3
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
# Create: 2020-11-27
# ******************************************************************************

"""
update obs repo rpms
"""
import os
import sys
import shutil
import time
import yaml
import threadpool
current_path = os.path.join(os.path.split(os.path.realpath(__file__))[0])
sys.path.append(os.path.join(current_path, ".."))
from common.common import git_repo_src
from common.log_obs import log
from common.common import Pexpect
from common.parser_config import ParserConfigIni


class RPMManager(object):
    """
    update for obs repo rpms
    """
    def __init__(self, **kwargs):
        """
        obs_project: obs project name
        repo: obs project repo where store all packages
        arch: 
        pkgs:
        """
        self.kwargs = kwargs
        par = ParserConfigIni()
        self.obs_project_repo_dict = par.get_obs_repos_dict()
        print(self.obs_project_repo_dict)
        self.obs_project_root_path = par.get_obs_prj_root_path()
        self.obs_pkg_rpms_url = par.get_repos_dict()["obs_pkg_rpms"]
        self.obs_project = self.kwargs["project"]
        self.rpms_to_repo_path = None
        self.old_pkg_rpms = None
        self.repo = self.kwargs["repo"]
        self.arch = self.kwargs["arch"]
        self.pkgs = self.kwargs["pkglist"]
        self.old_pkg_rpms = {}
        self._set_rpms_to_repo()
        self.pex = Pexpect(self.kwargs["repo_server_user"], self.kwargs["repo_server_ip"], 
                self.kwargs["repo_server_pwd"], self.kwargs["repo_server_port"])
        log.info(self.rpms_to_repo_path)
        self.obs_pkg_rpms_files_dir = None
        self._download_obs_pkg_rpms_file(self.obs_pkg_rpms_url, self.kwargs["gitee_user"], \
                self.kwargs["gitee_pwd"], dest_dir = "/tmp/obs_pkg_rpms")
        self.obs_pkg_rpms_file = os.path.join(self.obs_pkg_rpms_files_dir, "%s_%s.yaml" \
                % (self.obs_project.replace(":", "-"), self.arch))
        self.get_old_rpms_list_from_file(self.obs_pkg_rpms_file)

    def _set_rpms_to_repo(self):
        """
        set rpms repo where new rpm go
        """
        rpms_to_repo_list = self.obs_project_repo_dict[self.obs_project].split(" ")
        for rpms_to_repo in rpms_to_repo_list:
            if rpms_to_repo.endswith(self.arch):
                self.rpms_to_repo_path = rpms_to_repo
                break 

    def _download_obs_pkg_rpms_file(self, url, gitee_user, gitee_pwd, dest_dir=None):
        """
        download file by gitee repo
        """
        self.obs_pkg_rpms_files_dir = git_repo_src(url, gitee_user, gitee_pwd, dest_dir=dest_dir)

    def get_old_rpms_list_from_file(self, file_path):
        """
        get old pkg rpms dict
        file_path: yaml file which store all packages's rpms
        """
        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                self.old_pkg_rpms = yaml.load(f, Loader=yaml.FullLoader)
        else:
            log.error("no file for get rpms")

    def get_new_rpms_by_pkg(self, pkg):
        """
        get new rpms by package name
        pkg: name of packages
        """
        try:
            cmd = "ls %s/%s/%s/%s/%s | grep 'rpm' | grep -v 'src.rpm'" \
                    % (self.obs_project_root_path, self.obs_project, self.repo, self.arch, pkg)
            ret = self.pex.ssh_cmd(cmd)
            rpm_list = []
            for p in ret:
                p = str(p, encoding = 'utf8')
                if "rpm" in p:
                    rpm_list.append(p.replace("\r\n", ""))
        except ValueError as e:
            log.error(e)
        except SystemError as e:
            log.error(e)
        except TypeError as e:
            log.error(e)

        return rpm_list
       
    def backup_old_rpms_by_pkg(self, pkg):
        """
        backup old rpms by package name
        pkg: name of packages
        """
        try:
            if pkg in self.old_pkg_rpms and not self.old_pkg_rpms[pkg]:
                return None
            t = time.strftime("%Y-%m-%d-%H-%M", time.localtime())
            backup_dir =  os.path.join(self.obs_project_root_path, self.rpms_to_repo_path, "backup")
            pkg_bak = os.path.join(backup_dir, "%s-%s" % (pkg, t))
            cmd = "rm -r %s/%s-*; mkdir -p %s" % (backup_dir, pkg, pkg_bak)
            log.debug(cmd)
            ret = self.pex.ssh_cmd(cmd)
            log.debug(ret)
            old_rpms_list = self.old_pkg_rpms[pkg]
            for f in old_rpms_list:
                cmd = "mv %s/%s/%s/:full/%s %s/" % (self.obs_project_root_path, \
                        self.rpms_to_repo_path, self.arch, f, pkg_bak)
                log.debug(cmd)
                self.pex.ssh_cmd(cmd)
        except ValueError as e:
            log.error(e)
            return False
        except SystemError as e:
            log.error(e)
            return False
        except TypeError as e:
            log.error(e)
            return False
        except KeyError as e:
            log.error(e)
            return False
        return True

    def copy_new_rpms_to_repo(self, pkg):
        """
        copy new rpms by package name to repo
        pkg: name of package
        """
        try:
            rpms_list = self.get_new_rpms_by_pkg(pkg)
            log.debug(rpms_list)
            self.old_pkg_rpms[pkg] = rpms_list
            for r in rpms_list:
                cmd = "cp %s/%s/%s/%s/%s/%s %s/%s/%s/:full/" \
                        % (self.obs_project_root_path, self.obs_project, self.repo, \
                        self.arch, pkg, r, self.obs_project_root_path, \
                        self.rpms_to_repo_path, self.arch)
                log.debug(cmd)
                self.pex.ssh_cmd(cmd)
        except ValueError as e:
            log.error(e)
        except SystemError as e:
            log.error(e)
        except TypeError as e:
            log.error(e)
        except KeyError as e:
            log.error(e)

    def update_pkg(self, pkg):
        """
        update one package
        pkg: name of package
        """
        self.backup_old_rpms_by_pkg(pkg)
        self.copy_new_rpms_to_repo(pkg)
    
    def update_pkgs(self):
        """
        update packages
        """
        if not self.pkgs:
            self.pkgs = list(set(os.popen("osc list %s" % self.obs_project).read().split("\n")) - set(['']))
        pool = threadpool.ThreadPool(10)
        requests = threadpool.makeRequests(self.update_pkg, self.pkgs)
        for req in requests:
            pool.putRequest(req)
        pool.wait()
        self.write_new_pkg_rpms_to_file()
        self.update_repos_db()

    def write_new_pkg_rpms_to_file(self):
        """
        write new pkg rpms to yaml and git push for storing
        """
        with open(self.obs_pkg_rpms_file, "w", encoding="utf-8") as f:
            yaml.dump(self.old_pkg_rpms, f)
        cmd = "cd %s && git add %s && git commit -m 'update rpms' && git push" \
                % (self.obs_pkg_rpms_files_dir, self.obs_pkg_rpms_file)
        os.system(cmd)

    def update_repos_db(self):
        """
        update obs repos db
        """
        cmd = "chown -R obsrun:obsrun %s/%s/%s/:full; obs_admin --rescan-repository %s %s %s" \
                % (self.obs_project_root_path, self.rpms_to_repo_path, self.arch, \
                self.rpms_to_repo_path.split("/")[0], self.rpms_to_repo_path.split("/")[1], self.arch)
        log.debug(cmd)
        self.pex.ssh_cmd(cmd)

    #def get_hdr(rpm_path):
    #    ts = rpm.ts()
    #    try:
    #        fdno = os.open(rpm_path, os.O_RDONLY)
    #        hdr = ts.hdrFromFdno(fdno)
    #        os.close(fdno)
    #    except:
    #        log.error("ERROR: Init rpm error!")
    #    return hdr

    #def get_rpm_info(self, rpm_path):
    #    """
    #    rpm_path: rpm package's path
    #    """
    #    cmd = "rpm -qp --info %s | grep -E 'Name|Version|Release|Architecture' | awk -F '[:]' '{print $2}'" % rpm_path
    #    res = os.popen(cmd).read().split("\n")
    #    #logger.info(res)
    #    return res[0].strip(), res[1].strip(), res[2].strip(), res[3].strip()

                    
if __name__ == "__main__":
    kw = {
            "project": "openEuler:20.03:LTS",
            "repo": "standard_x86_64",
            "arch": "x86_64",
            "repo_server_user": "root",
            "repo_server_ip": "127.0.0.1",
            "repo_server_pwd": "1234",
            "repo_server_port": "22233",
            "gitee_user": "xxxxxxxxx",
            "gitee_pwd": "xxxxxxxxx",
            "pkglist": ["zip", "zsh"]
            }
    test = RPMManager(**kw)
    test.update_pkgs()
