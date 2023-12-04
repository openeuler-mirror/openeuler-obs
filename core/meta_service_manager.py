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
# Author: dongjie
# Create: 2022-09-04
# ******************************************************************************

"""
align obs_meta pkg service and release_management yaml pkg
"""
import os
import re
import sys
import yaml
import shutil
import datetime
now_path = os.path.join(os.path.split(os.path.realpath(__file__))[0])
sys.path.append(os.path.join(now_path, ".."))
from common.log_obs import log
from common.parser_config import ParserConfigIni



class MetaServiceManager(object):
    def __init__(self, **kwargs):
        """
        giteeuser: gitee user name
        giteeuserpwd: gitee password
        branch: need check branchs
        obs_meta_path: repo obs_meta path
        release_management_path: repo release_management path
        """
        self.kwargs = kwargs
        self.giteeuser = self.kwargs['gitee_user']
        self.giteeuserpwd = self.kwargs['gitee_pwd']
        self.branch = self.kwargs['align_meta_service_branch']
        self.obs_meta_path = self.kwargs['obs_meta_path']
        self.release_management_path = self.kwargs['release_management_path']
        par = ParserConfigIni()
        self.release_maintenance_branchs = par.get_release_maintenance_branch()

    def get_pkgs_from_yaml(self, branch):
        """
        branch: branch name
        return: branch pkgs dict
        """
        all_branch_pkgs = []
        project_pkgs = {}
        if os.path.exists(os.path.join(self.release_management_path, branch)):
            standard_dirs = os.listdir(os.path.join(self.release_management_path, branch))
            for standard_dir in standard_dirs:
                file_path = os.path.join(self.release_management_path, branch, standard_dir)
                if not os.path.isdir(file_path):
                    standard_dirs.remove(standard_dir)
            if 'delete' in standard_dirs:
                standard_dirs.remove('delete')
            for c_dir in standard_dirs:
                release_path = os.path.join(self.release_management_path, branch, c_dir, 'pckg-mgmt.yaml')
                if os.path.exists(release_path):
                    with open(release_path, 'r', encoding='utf-8') as f:
                        result = yaml.load(f, Loader=yaml.FullLoader)
                        all_branch_pkgs.extend(result['packages'])
            if branch == 'multi_version':
                for pkg in all_branch_pkgs:
                    temp_key = '{}/{}'.format(pkg['destination_dir'], pkg['obs_to'])
                    project_pkgs.setdefault(temp_key, []).append(pkg['name'])
            else:
                for pkg in all_branch_pkgs:
                    project_pkgs.setdefault(pkg['obs_to'], []).append(pkg['name'])
        else:
            log.error("this branch {} not exist in repo release_management".format(branch))
        return project_pkgs

    def get_pkgs_from_meta(self, branch, project):
        """
        branch: branch name
        project: project name
        return: none
        """
        meta_pkglist = os.listdir(os.path.join(self.obs_meta_path, branch, project))
        if 'README.md' in meta_pkglist:
            meta_pkglist.remove('README.md')
        return meta_pkglist

    def compare_with_meta_yaml(self, branch, yaml_pkgs):
        """
        branch: branch name
        yaml_pkgs: branch pkgs info
        return: none
        """
        for project, yamlpkgs in yaml_pkgs.items():
            meta_pkglist = self.get_pkgs_from_meta(branch, project)
            need_del_pkg = set(meta_pkglist) - set(yamlpkgs)
            need_add_pkg = set(yamlpkgs) - set(meta_pkglist)
            log.info("obs_meta {} {} redundant pkg:{}".format(branch, project, list(need_del_pkg)))
            log.info("obs_meta {} {} lack pkg:{}".format(branch, project, list(need_add_pkg)))
            self.add_pkg_to_meta(branch, project, need_add_pkg)
            self.del_pkg_from_meta(branch, project, need_del_pkg)

    def add_pkg_to_meta(self, branch, project, add_pkgs):
        """
        branch: branch name
        project: project name
        add_pkgs: need add pkgs list
        return: none
        """
        if add_pkgs:
            if branch == 'multi_version':
                branch = project.split('/')[0]
                project_path = os.path.join(self.obs_meta_path, 'multi_version', project)
            else:
                project_path = os.path.join(self.obs_meta_path, branch, project)
            for add_pkg in add_pkgs:
                pkg_path = os.path.join(project_path, add_pkg)
                pkg_service_path = os.path.join(pkg_path, "_service")
                if not os.path.exists(pkg_path):
                    os.makedirs(pkg_path)
                self._write_service_file(pkg_path, add_pkg, branch)
                if os.path.exists(pkg_service_path):
                    log.info("add {} {} {} _service succeed!".format(branch, project, add_pkg))
                else:
                    log.error("add {} {} {} _service failed!".format(branch, project, add_pkg))



    def del_pkg_from_meta(self, branch, project, del_pkgs):
        """
        branch: branch name
        project: project name
        del_pkgs: need delete pkgs list
        return: none
        """
        if del_pkgs:
            for del_pkg in del_pkgs:
                if 'Multi-Version' in branch:
                    dir_name = '{}/{}'.format(branch, project)
                    pkg_path = os.path.join(self.obs_meta_path, 'multi_version', dir_name, del_pkg)
                else:
                    pkg_path = os.path.join(self.obs_meta_path, branch, project, del_pkg)
                if os.path.exists(pkg_path):
                    shutil.rmtree(pkg_path)
                    log.info("delete {} {} {} succeed!".format(branch, project, del_pkg))

    def _write_service_file(self, filepath, package, pkg_branch):
        '''
        write service file
        '''
        if pkg_branch == 'master':
            file_msg = """<services>
    <service name="tar_scm">
        <param name="scm">git</param>
        <param name="url">git@gitee.com:src-openeuler/{}.git</param>
        <param name="exclude">*</param>
        <param name="extract">*</param>
        <param name="revision">master</param>
    </service>
</services>""".format(package)
        else:
            file_msg = """<services>
            <service name="tar_scm_kernel_repo">
              <param name="scm">repo</param>
              <param name="url">next/{}/{}</param>
            </service>
    </services>""".format(pkg_branch, package)
        try:
            with open(os.path.join(filepath, '_service'), 'w') as f:
                f.write(file_msg)
        except Exception as e:
            log.info(e)

    def align_meta_yaml(self, branch):
        """
        branch: branch name
        return: code of status
        """
        project_pkgs = self.get_pkgs_from_yaml(branch)
        self.compare_with_meta_yaml(branch, project_pkgs)

    def run(self):
        """
        Function entry
        """
        if self.branch == 'all':
            need_align_branchs = self.release_maintenance_branchs
        else:
            need_align_branchs = self.branch.split(' ')
        log.info("align meta service by release_management pckg-mgmt.yaml {}".format(need_align_branchs))
        for branch in need_align_branchs:
            self.align_meta_yaml(branch)
        ret = self._push_code(self.obs_meta_path)
        return ret

    def _push_code(self, repo):
        """
        push code to gitee repo
        """
        if os.path.exists(repo):
            os.chdir(repo)
            cmd = "git status -s"
            if os.popen(cmd).read():
                cmd = "git pull && git add -A && git commit -m \"synchronize with pckg-mgmt.yaml file contents\""
                if os.system(cmd) == 0:
                    cmd = "git push -f"
                    for i in range(5):
                        if os.system(cmd) == 0:
                            log.info("push code to gitee repo succeed!")
                            return 0
                        else:
                            log.error("push code failed, try again...")
                    raise SystemExit("push code to gitee repo Failed!")
            else:
                log.info("No change, nothing to commit!")
                return "nothing to push"
        else:
            log.error("%s not exist!" % repo)
            return -1