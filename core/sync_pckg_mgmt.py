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
# Author: wangchong
# Create: 2021-06-08
# ******************************************************************************
"""
Synchronize the obs_meta file according to the pckg-mgmt.yaml file
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


class SyncPckgMgmt(object):
    """
    keep pckg-mgmt.yaml and obs_meta in sync
    """
    def __init__(self, **kwargs):
        """
        giteeuser: gitee user name
        giteeuserpwd: gitee password
        """
        self.kwargs = kwargs
        self.giteeuser = self.kwargs['gitee_user']
        self.giteeuserpwd = self.kwargs['gitee_pwd']
        self.obs_meta_path = self.kwargs['obs_meta_path']
        self.release_management_path = self.kwargs['release_management_path']
        par = ParserConfigIni()
        self.obs_ignored_package = par.get_obs_ignored_package()
        self.release_change_pkgs = dict()

    def _get_change_file(self):
        """
        get release-managemnet change file
        """
        if os.path.exists(self.release_management_path):
            os.chdir(self.release_management_path)
            cmd = "git diff --name-status HEAD~1 HEAD~0 | grep pckg-mgmt.yaml"
            result = os.popen(cmd).read().split('\n')
            change_file = [x for x in result if x != '']
            return change_file
        else:
            log.error("%s not exist!" % self.release_management_path)
            sys.exit(1)

    def _get_yaml_file_msg(self, file_path):
        """
        get pckg-mgmt.yaml file msg
        """
        file_msg = None
        if os.path.exists(file_path):
            with open(file_path, "r", encoding='utf-8') as f:
                file_msg = yaml.load(f, Loader=yaml.FullLoader)
        return file_msg
    
    def _check_pckg_yaml(self, file_msg, branch):
        """
        check pckg-mgmt.yaml file
        """
        proj = branch.replace("-", ":")
        flag = False
        for title in file_msg['packages']:
            for msg in file_msg['packages'][title]:
                if msg['branch_to'] != branch:
                    flag = True
                    log.error("%s branch_to is error, please check yaml." % msg['name'])
                if not msg['obs_to'].startswith(proj):
                    flag = True
                    log.error("%s obs_to is error, please check yaml." % msg['name'])
        return flag

    def _parse_yaml_msg(self, file_msg, yaml_type):
        """
        parse yaml file msg
        """
        tmp = {}
        msg = []
        del_msg = []
        prj_pkg = {}
        if yaml_type == "old":
            for pckg in file_msg['packages']['natural']:
                tmp = {'pkgname': pckg['name'], 'branch_from': pckg['branch_from'],
                        'branch_to': pckg['branch_to'], 'obs_from': pckg['obs_from'],
                        'obs_to': pckg['obs_to']}
                prj_pkg.setdefault(pckg['obs_to'], []).append(pckg['name'])
                prj_pkg['branch'] = pckg['branch_to']
                msg.append(tmp)
            for pckg in file_msg['packages']['recycle']:
                tmp = {'pkgname': pckg['name'], 'branch_from': pckg['branch_from'],
                        'branch_to': pckg['branch_to'], 'obs_from': pckg['obs_from'],
                        'obs_to': pckg['obs_to']}
                prj_pkg.setdefault(pckg['obs_to'], []).append(pckg['name'])
                msg.append(tmp)
            for pckg in file_msg['packages']['delete']:
                tmp = {'pkgname': pckg['name'], 'branch_to': pckg['branch_to'], 
                        'obs_to': pckg['obs_to']}
                del_msg.append(tmp)
        elif yaml_type == 'master':
            for pckg in file_msg['packages']:
                tmp = {'pkgname': pckg['name'], 'branch_from': 'master',
                        'branch_to': 'master', 'obs_from': pckg['obs_from'],
                        'obs_to': pckg['obs_to']}
                prj_pkg.setdefault(pckg['obs_to'], []).append(pckg['name'])
                prj_pkg['branch'] = 'master'
                msg.append(tmp)
        elif yaml_type == 'multi-new':
            for pckg in file_msg['packages']:
                tmp = {'pkgname': pckg['name'], 'branch_from': pckg['source_dir'],
                        'branch_to': pckg['destination_dir'], 'obs_from': pckg['obs_from'],
                        'obs_to': pckg['obs_to']}
                prj_pkg.setdefault(pckg['obs_to'], []).append(pckg['name'])
                prj_pkg['branch'] = pckg['destination_dir']
                msg.append(tmp)
        elif yaml_type == 'multi-new-delete':
            for pckg in file_msg['packages']:
                tmp = {'pkgname': pckg['name']}
                msg.append(tmp)
        else:
            for label in file_msg['packages']['everything']:
                for pckg in file_msg['packages']['everything'][label]:
                    tmp = {'pkgname': pckg['name'], 'branch_from': pckg['branch_from'],
                            'branch_to': pckg['branch_to'], 'obs_from': pckg['obs_from'],
                            'obs_to': pckg['obs_to']}
                    prj_pkg.setdefault(pckg['obs_to'], []).append(pckg['name'])
                    prj_pkg['branch'] = pckg['branch_to']
                    msg.append(tmp)
            for pckg in file_msg['packages']['epol']:
                tmp = {'pkgname': pckg['name'], 'branch_from': pckg['branch_from'],
                        'branch_to': pckg['branch_to'], 'obs_from': pckg['obs_from'],
                        'obs_to': pckg['obs_to']}
                prj_pkg.setdefault(pckg['obs_to'], []).append(pckg['name'])
                prj_pkg['branch'] = pckg['branch_to']
                msg.append(tmp)
            for pckg in file_msg['packages']['recycle']:
                tmp = {'pkgname': pckg['name'], 'branch_from': pckg['branch_from'],
                        'branch_to': pckg['branch_to'], 'obs_from': pckg['obs_from'],
                        'obs_to': pckg['obs_to']}
                prj_pkg.setdefault(pckg['obs_to'], []).append(pckg['name'])
                msg.append(tmp)
            for pckg in file_msg['packages']['delete']:
                tmp = {'pkgname': pckg['name'], 'branch_to': pckg['branch_to'], 
                        'obs_to': pckg['obs_to']}
                del_msg.append(tmp)
        return msg, del_msg, prj_pkg

    def _write_prj_meta_file(self, file_path, proj):
        """
        write project meta file
        """
        if "Epol" in proj:
            main_proj = proj.replace(':Epol', '')
            con_proj = main_proj.replace(':', '_').lower()
            epol_repo_aarch64 = "\n    <path project=\"%s:selfbuild:BaseOS\" repository=\"%s_epol_aarch64\"/>" % (
                    main_proj, con_proj)
            epol_repo_x86 = "\n    <path project=\"%s:selfbuild:BaseOS\" repository=\"%s_epol_x86_64\"/>" % (
                    main_proj, con_proj)
        else:
            main_proj = proj
            con_proj = main_proj.replace(':', '_').lower()
            epol_repo_aarch64 = ""
            epol_repo_x86 = ""
        if 'master' in file_path:
            file_msg = """<project name="{0}">
  <title/>
  <description/>
  <person userid="Admin" role="maintainer"/>
  <repository name="standard_aarch64" rebuild="direct">
    <path project="openEuler:selfbuild:BaseOS" repository="baseos_aarch64"/>
    <arch>aarch64</arch>
  </repository>
  <repository name="standard_x86_64" rebuild="direct">
    <path project="openEuler:selfbuild:BaseOS" repository="baseos_x86_64"/>
    <arch>x86_64</arch>
  </repository>
</project>
    """.format(proj)
        else:
            file_msg = """<project name="{0}">
  <title/>
  <description/>
  <person userid="Admin" role="maintainer"/>
  <useforbuild>
    <disable/>
  </useforbuild>
  <repository name="standard_aarch64">
    <path project="{1}:selfbuild:BaseOS" repository="{2}_standard_aarch64"/>{3}
    <arch>aarch64</arch>
  </repository>
  <repository name="standard_x86_64">
    <path project="{1}:selfbuild:BaseOS" repository="{2}_standard_x86_64"/>{4}
    <arch>x86_64</arch>
  </repository>
</project>
    """.format(proj, main_proj, con_proj, epol_repo_aarch64, epol_repo_x86)
        f = open(file_path, "w")
        f.write(file_msg)
        f.close()

    def _write_selfbuild_meta_file(self, file_path, proj):
        """
        write selfbuild project meta file
        """
        file_msg = """<project name="{0}:selfbuild:BaseOS">
  <title/>
  <description/>
  <person userid="Admin" role="maintainer"/>
  <repository name="{1}_standard_aarch64">
    <arch>aarch64</arch>
  </repository>
  <repository name="{1}_standard_x86_64">
    <arch>x86_64</arch>
  </repository>
  <repository name="{1}_epol_aarch64">
    <arch>aarch64</arch>
  </repository>
  <repository name="{1}_epol_x86_64">
    <arch>x86_64</arch>
  </repository>
</project>
""".format(proj, proj.lower().replace(':', '_'))
        f = open(file_path, "w")
        f.write(file_msg)
        f.close()

    def _write_service_file(self, filepath, package, pkg_branch):
        '''
        write service file
        '''
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
            print (e)

    def _add_pkg_service(self, tmp):
        """
        add obs_meta packages _service file
        """
        success_pkg_name = ''
        if 'Multi-Version' in tmp['branch_from']:
            dir_name = '{}/{}'.format(tmp['branch_from'], tmp['obs_from'])
            from_pkg_path = os.path.join(self.obs_meta_path, 'multi_version', dir_name, tmp['pkgname'])
        else:
            from_pkg_path = os.path.join(self.obs_meta_path, tmp['branch_from'], tmp['obs_from'], tmp['pkgname'])
        if 'Multi-Version' in tmp['branch_to']:
            dir_name = '{}/{}'.format(tmp['branch_to'], tmp['obs_to'])
            pkg_path = os.path.join(self.obs_meta_path, 'multi_version', dir_name, tmp['pkgname'])
        else:
            pkg_path = os.path.join(self.obs_meta_path, tmp['branch_to'], tmp['obs_to'], tmp['pkgname'])
        pkg_service_path = os.path.join(pkg_path, "_service")
        if not os.path.exists(pkg_path):
            os.makedirs(pkg_path)
            if tmp['branch_from'] == "master" and tmp['pkgname'] not in self.obs_ignored_package:
                self._write_service_file(pkg_path, tmp['pkgname'], tmp['branch_to'])
                if os.path.exists(pkg_service_path):
                    success_pkg_name = tmp['pkgname']
                    log.info("add %s %s %s _service succeed!" % (tmp['branch_to'], tmp['obs_to'], tmp['pkgname']))
                else:
                    log.info("add %s %s %s _service failed!" % (tmp['branch_to'], tmp['obs_to'], tmp['pkgname']))
            else:
                if tmp['branch_from'] == "master":
                    branch = "openEuler"
                else:
                    branch = tmp['branch_from']
                if not os.path.exists(pkg_service_path) and os.path.exists(from_pkg_path):
                    cmd = "cp %s/_service %s/_service" % (from_pkg_path, pkg_path)
                    if os.system(cmd) == 0:
                        cmd = "sed -i 's/%s\//%s\//g' %s/_service" % (branch, tmp['branch_to'], pkg_path)
                        if os.system(cmd) == 0:
                            success_pkg_name = tmp['pkgname']
                            log.info("add %s %s %s _service succeed!" % (tmp['branch_to'], tmp['obs_to'], tmp['pkgname']))
                        else:
                            log.info("add %s %s %s _service failed!" % (tmp['branch_to'], tmp['obs_to'], tmp['pkgname']))
                    else:
                        log.error("copy %s service file failed!" % tmp['pkgname'])
                elif not os.path.exists(pkg_service_path) and not os.path.exists(from_pkg_path):
                    self._write_service_file(pkg_path, tmp['pkgname'], tmp['branch_to'])
                    if os.path.exists(pkg_service_path):
                        success_pkg_name = tmp['pkgname']
                        log.info("add %s %s %s _service succeed!" % (tmp['branch_to'], tmp['obs_to'], tmp['pkgname']))
                    else:
                        log.info("add %s %s %s _service failed!" % (tmp['branch_to'], tmp['obs_to'], tmp['pkgname']))
        return success_pkg_name

    def _move_pkg_service(self, tmp):
        """
        move obs_meta packages _service file
        """
        success_pkg_name = ''
        from_pkg_path = os.path.join(self.obs_meta_path, tmp['branch_from'], tmp['obs_from'], tmp['pkgname'])
        pkg_path = os.path.join(self.obs_meta_path, tmp['branch_to'], tmp['obs_to'], tmp['pkgname'])
        mv_to_path = os.path.join(self.obs_meta_path, tmp['branch_to'], tmp['obs_to'])
        if not os.path.exists(mv_to_path):
            os.makedirs(mv_to_path)
        if not os.path.exists(pkg_path):
            cmd = "mv %s %s" % (from_pkg_path, mv_to_path)
            if os.system(cmd) == 0:
                success_pkg_name = tmp['pkgname']
                log.info("move %s from %s to %s _service succeed!" % (tmp['pkgname'], tmp['obs_from'], tmp['obs_to']))
            else:
                log.info("move %s from %s to %s _service failed!" % (tmp['pkgname'], tmp['obs_from'], tmp['obs_to']))
        return success_pkg_name

    def _add_master_pkg_service(self, package):
        """
        create and add master service to repo obs_meta 
        """
        filepath = os.path.join(self.obs_meta_path, 'master', 'openEuler:Factory', package)
        if not os.path.exists(filepath):
            os.makedirs(filepath)
        file_msg = """<services>
    <service name="tar_scm">
        <param name="scm">git</param>
        <param name="url">git@gitee.com:src-openeuler/{}.git</param>
        <param name="exclude">*</param>
        <param name="extract">*</param>
        <param name="revision">master</param>
    </service>
</services>""".format(package)
        try:
            with open(os.path.join(filepath,'_service'),'w') as f:
                f.write(file_msg)
                log.info("add openEuler:Factory {} _service success!".format(package))
        except Exception as e:
            log.error(e)
            log.error("add openEuler:Factory {} _service failed!".format(package))

    def _move_master_pkg_service(self, msg):
        """
        copy branch master obs_meta packages _service file
        """
        change_pkgs = []
        for tmp in msg:
            if tmp['obs_to'] == 'openEuler:Factory':
                if tmp['obs_from']:
                    pkg_name = self._move_pkg_service(tmp)
                    if pkg_name:
                        change_pkgs.append(pkg_name)
                else:
                    pkg_path = os.path.join(self.obs_meta_path, tmp['branch_to'], tmp['obs_to'], tmp['pkgname'])
                    if not os.path.exists(pkg_path):
                        self._add_master_pkg_service(tmp['pkgname'])
                        change_pkgs.append(tmp['pkgname'])
            else:
                pkg_name = self._move_pkg_service(tmp)
                if pkg_name:
                    change_pkgs.append(pkg_name)
        return change_pkgs

        
    def _add_prj_meta_pkgs_service(self, msg, branch_infos):
        pkg_names = []
        for tmp in msg:
            if 'multi_version' not in branch_infos:
                prj_meta_br = os.path.join(self.obs_meta_path, "OBS_PRJ_meta/%s"
                            % tmp['branch_to'])
                if not os.path.exists(prj_meta_br):
                    os.makedirs(prj_meta_br)
                prj_meta_path = os.path.join(prj_meta_br, tmp['obs_to'])
                if not os.path.exists(prj_meta_path):
                    self._write_prj_meta_file(prj_meta_path, tmp['obs_to'])
                selfbuild_meta_path = os.path.join(prj_meta_br,
                        "%s:selfbuild:BaseOS" % tmp['obs_to'])
                if not os.path.exists(selfbuild_meta_path):
                    if "Epol" not in tmp['obs_to'] and 'master' not in branch_infos:
                        self._write_selfbuild_meta_file(selfbuild_meta_path, tmp['obs_to'])
            if 'master' not in branch_infos:
                if tmp['branch_from'] == tmp['branch_to'] and tmp['obs_from'] != tmp['obs_to']:
                    pkg_name = self._move_pkg_service(tmp)
                else:
                    pkg_name = self._add_pkg_service(tmp)
                if pkg_name:
                    pkg_names.append(pkg_name)
        return pkg_names

    def _clear_msg_delete(self, msg, branch):
        """
        clear pkg if this pkg already in delete yaml
        """
        branch_delete_path = os.path.join(self.release_management_path, branch, 'delete', 'pckg-mgmt.yaml')
        delete_yaml_msg = self._get_yaml_file_msg(branch_delete_path)
        delete_packages = [pkg['name'] for pkg in delete_yaml_msg['packages']]
        if delete_packages:
            for i in range(len(msg)-1, -1, -1):
                if msg[i]['pkgname'] in delete_packages:
                    msg.pop(i)
        return msg

    def _del_pkg(self, tmp):
        """
        delete obs_meta packages
        """
        if 'Multi-Version' in tmp['branch_to']:
            dir_name = '{}/{}'.format(tmp['branch_to'], tmp['obs_to'])
            pkg_path = os.path.join(self.obs_meta_path, 'multi_version', dir_name, tmp['pkgname'])
        else:
            pkg_path = os.path.join(self.obs_meta_path, tmp['branch_to'], tmp['obs_to'], tmp['pkgname'])
        if os.path.exists(pkg_path):
            shutil.rmtree(pkg_path)
            log.info("delete %s %s %s succeed!" % (tmp['branch_to'], tmp['obs_to'], tmp['pkgname']))
            return tmp['pkgname']

    def _del_pkg_new(self, pkgs, branch):
        """
        find in branch dirs and delete pkg 
        """
        need_del_path = []
        correct_del_pkgs = []
        release_changes = {}
        branch_dir = os.path.join(self.obs_meta_path, branch)
        for root, dirs, files in os.walk(branch_dir, True):
            for name in dirs:
                c_path = os.path.join(root, name)
                if name in pkgs and 'Bak' not in c_path and 'bringInRely' not in c_path and 'RISC-V' not in c_path:
                    correct_del_pkgs.append(name)
                    need_del_path.append(c_path)
        for pkg_path in need_del_path:
            if os.path.exists(pkg_path):
                pkg_path_infos = pkg_path.split('/')
                shutil.rmtree(pkg_path)
                log.info("delete %s %s succeed!" % (branch, pkg_path_infos[-1]))
                release_branch = pkg_path_infos[-3]
                if release_branch == 'master':
                    obs_project = pkg_path_infos[-2].replace(":", "-")
                    release_path = os.path.join(self.release_management_path, release_branch, obs_project)
                    if release_changes.get(release_path):
                        release_changes[release_path].append(pkg_path_infos[-1])
                    else:
                        release_changes[release_path] = [pkg_path_infos[-1]]
                else:
                    standard_dirs = ['epol', 'everything-exclude-baseos', 'baseos']
                    for c_dir in standard_dirs:
                        release_path = os.path.join(self.release_management_path, release_branch, c_dir)
                        if release_changes.get(release_path):
                            release_changes[release_path].append(pkg_path_infos[-1])
                        else:
                            release_changes[release_path] = [pkg_path_infos[-1]]
        return correct_del_pkgs, release_changes

    def _del_pckg_from_yaml(self, release_delete_changes):
        """
        find pkg and delete pkgs from pckg-mgmt.yaml
        """
        if release_delete_changes:
            for release_changes in release_delete_changes:
                for pkgs_path, pkgs in release_changes.items():
                    result = {}
                    change_flag = False
                    complete_path = os.path.join(pkgs_path, 'pckg-mgmt.yaml')
                    old_yaml = self._get_yaml_file_msg(complete_path)
                    pkgs_list = old_yaml['packages']
                    for i in range(len(pkgs_list)-1, -1, -1):
                        if pkgs_list[i]['name'] in pkgs:
                            pkgs_list.pop(i)
                            change_flag = True
                    if change_flag:
                        result['packages'] = pkgs_list
                        with open(complete_path, "w", encoding='utf-8') as f:
                            yaml.dump(result, f, default_flow_style=False, sort_keys=False)


    def _verify_meta_file(self, prj_pkg):
        """
        verify obs_meta with pckg-mgmt.yaml
        """
        for proj, pkg in prj_pkg.items():
            if proj != "branch":
                if 'Multi-Version' in prj_pkg['branch']:
                    dir_name = '{}/{}'.format(prj_pkg['branch'], proj)
                    meta_path = os.path.join(self.obs_meta_path, 'multi_version', dir_name)
                    meta_pkglist = os.listdir(meta_path)
                else:
                    meta_pkglist = os.listdir(os.path.join(self.obs_meta_path, prj_pkg['branch'], proj))
                if 'README.md' in meta_pkglist:
                    meta_pkglist.remove('README.md')
                if len(list(prj_pkg.keys())) >= 3:
                    need_del_pkg = []
                else:
                    need_del_pkg = set(meta_pkglist) - set(pkg)
                log.info("obs_meta %s %s redundant pkg:%s" % (prj_pkg['branch'], proj, list(need_del_pkg)))
                if need_del_pkg:
                    for del_pkg in need_del_pkg:
                        tmp = {'pkgname': del_pkg, 'branch_to': prj_pkg['branch'], 'obs_to': proj}
                        self._del_pkg(tmp)
        return list(need_del_pkg)

    def _align_meta_yaml(self, change_lists):
        '''
        align meta file service same with branch yaml info
        '''
        for branch in change_lists:
            all_branch_pkgs = []
            project_pkgs = {}
            if os.path.exists(os.path.join(self.release_management_path, branch)):
                standard_dirs = os.listdir(os.path.join(self.release_management_path, branch))
                for standard_dir in standard_dirs:
                    file_path = os.path.join(self.release_management_path, branch, standard_dir)
                    if not os.path.isdir(file_path) or standard_dir == 'delete':
                        standard_dirs.remove(standard_dir)
                for c_dir in standard_dirs:
                    release_path = os.path.join(self.release_management_path, branch, c_dir, 'pckg-mgmt.yaml')
                    if os.path.exists(release_path):
                        with open(release_path, 'r', encoding='utf-8') as f:
                            result = yaml.load(f, Loader=yaml.FullLoader)
                            all_branch_pkgs.extend(result['packages'])
            for pkg in all_branch_pkgs:
                project_pkgs.setdefault(pkg['obs_to'], []).append(pkg['name'])
            for project, yamlpkgs in project_pkgs.items():
                meta_pkglist = os.listdir(os.path.join(self.obs_meta_path, branch, project))
                need_del_pkg = set(meta_pkglist) - set(yamlpkgs)
                need_add_pkg = set(yamlpkgs) - set(meta_pkglist)
                log.info("obs_meta %s %s redundant pkg:%s" % (branch, project, list(need_del_pkg)))
                log.info("obs_meta %s %s lack pkg:%s" % (branch, project, list(need_add_pkg)))
                if need_del_pkg:
                    for del_pkg in need_del_pkg:
                        tmp = {'pkgname': del_pkg, 'branch_to': branch, 'obs_to': project}
                        self._del_pkg(tmp)
                if need_add_pkg:
                    temp_lists = []
                    for pkg_all in all_branch_pkgs:
                        if pkg_all['name'] in list(need_add_pkg):
                            temp_dict = {
                                    'pkgname':pkg_all['name'],
                                    'branch_from':pkg_all['source_dir'],
                                    'branch_to':pkg_all['destination_dir'],
                                    'obs_from':pkg_all['obs_from'],
                                    'obs_to':pkg_all['obs_to'],
                            }
                            temp_lists.append(temp_dict)
                    for temp in temp_lists:
                        self._add_pkg_service(temp)


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

    def _collect_release_change_pkgs(self, branch, pkgs):
        """
        record change pkgs in dict
        """
        if pkgs:
            if self.release_change_pkgs.get(branch,[]):
                self.release_change_pkgs[branch].extend(pkgs)
            else:
                self.release_change_pkgs[branch] = pkgs

    def _do_git_pull(self):
        """
        makesure local repo same with origin master
        """
        os.chdir(self.release_management_path)
        commit_cmd = 'git rev-parse HEAD'
        commitid = os.popen(commit_cmd).read().split('\n')[0]
        content_cmd = "git log --oneline -1"
        content = os.popen(content_cmd).read().split('\n')[0]
        reg=re.compile(r"(?<=!)\d+")
        match=reg.search(content)
        try:
            pull_cmd = "cd {} && git pull".format(self.release_management_path)
            if os.system(pull_cmd) == 0:
                log.info("git pull repo success")
                code = 0
            else:
                log.error("git pull repo failed")
                code = -1
        except OSError as e:
            log.error(e)
            code = -1
        if code == -1:
            raise SystemExit("git pull last release_management repo failed")
        else:
            pull_result = {'match':match, 'content':content}
            return pull_result

    def _write_release_yaml(self, pull_request):
        '''
        write change info to release_change.yaml
        '''
        match = pull_request['match']
        content = pull_request['content']
        if self.release_change_pkgs:
            if match:
                pr_id = match.group(0)
                pull_request = "https://gitee.com/openeuler/release-management/pulls/{}".format(pr_id)
                datestr = datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
                for branch, change_pkgs in self.release_change_pkgs.items():
                    if len(change_pkgs) < 50:
                        change_str = " ".join(change_pkgs)
                        release_change_yaml = os.path.join(self.release_management_path, branch, "release-change.yaml")
                        with open(release_change_yaml, encoding='utf-8') as file:
                            result = yaml.load(file, Loader=yaml.FullLoader)
                            change_dic = {
                                            'pr':pull_request,
                                            'description':content,
                                            'changed_packages':change_str,
                                            'date':datestr
                                }
                            result['release-change'].append(change_dic)
                        with open(release_change_yaml, "w", encoding='utf-8') as f:
                            yaml.dump(result, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
                        log.info("write {} release change yaml file success".format(branch))
                    else:
                        log.info("{} init pkg ignore write release change".format(branch))
            else:
                log.info("ignore write release change yaml file success")


    def sync_yaml_meta(self):
        """
        integration of functions
        """
        change_file = self._get_change_file()
        yaml_dict = {}
        release_delete_changes = []
        for line in change_file:
            log.info("line:%s" % line)
            name = list(line.split())[1]
            file_path = os.path.join(self.release_management_path, name)
            yaml_dict = self._get_yaml_file_msg(file_path)
            branch_infos = name.split('/')
            if 'master' in branch_infos:
                branch = branch_infos[1]
                if branch != 'delete':
                    msg, del_msg, prj_pkg = self._parse_yaml_msg(yaml_dict, "master")
                    pkg_names = self._add_prj_meta_pkgs_service(msg, branch_infos)
                    msg = self._clear_msg_delete(msg, branch_infos[0])
                    move_change_pkgs = self._move_master_pkg_service(msg)
                    self._collect_release_change_pkgs(branch_infos[0],move_change_pkgs)
                else:
                    msg, del_msg, prj_pkg = self._parse_yaml_msg(yaml_dict, "multi-new-delete")
                    pkgs = [tmp['pkgname'] for tmp in msg]
                    del_change_pkgs, yaml_changes = self._del_pkg_new(pkgs, '{}'.format(branch_infos[0]))
                    release_delete_changes.append(yaml_changes)
                    self._collect_release_change_pkgs(branch_infos[0], del_change_pkgs)
            elif 'multi_version' in branch_infos:
                msg, del_msg, prj_pkg = self._parse_yaml_msg(yaml_dict, "multi-new")
                pkg_names = self._add_prj_meta_pkgs_service(msg, branch_infos)
                del_change_pkgs = self._verify_meta_file(prj_pkg)
                change_pkgs = pkg_names + del_change_pkgs
                complete_path = os.path.join(branch_infos[0], branch_infos[1])
                self._collect_release_change_pkgs(complete_path, change_pkgs)
            else:
                if not yaml_dict:
                    log.info("%s file content is empty!" % name)
                elif isinstance(yaml_dict['packages'], list):
                    if 'delete' not in branch_infos:
                        msg, del_msg, prj_pkg = self._parse_yaml_msg(yaml_dict, "multi-new")
                        msg = self._clear_msg_delete(msg, branch_infos[0])
                        pkg_names = self._add_prj_meta_pkgs_service(msg, branch_infos)
                        self._collect_release_change_pkgs(branch_infos[0], pkg_names)
                    else:
                        msg, del_msg, prj_pkg = self._parse_yaml_msg(yaml_dict, "multi-new-delete")
                        pkgs = [tmp['pkgname'] for tmp in msg]
                        del_change_pkgs, yaml_changes = self._del_pkg_new(pkgs, branch_infos[0])
                        release_delete_changes.append(yaml_changes)
                        self._collect_release_change_pkgs(branch_infos[0], del_change_pkgs)
                else:
                    if "everything" in yaml_dict['packages'].keys():
                        msg, del_msg, prj_pkg = self._parse_yaml_msg(yaml_dict, "new")
                        pkg_names = self._add_prj_meta_pkgs_service(msg, branch_infos)
                    else:
                        msg, del_msg, prj_pkg = self._parse_yaml_msg(yaml_dict, "old")
                        pkg_names = self._add_prj_meta_pkgs_service(msg, branch_infos)
                    for tmp in del_msg:
                        self._del_pkg(tmp)
                    del_change_pkgs = self._verify_meta_file(prj_pkg)
        pull_result = self._do_git_pull()
        self._del_pckg_from_yaml(release_delete_changes)
        self._write_release_yaml(pull_result)
        ret = self._push_code(self.obs_meta_path)
        self._push_code(self.release_management_path)
        return ret


if __name__ == "__main__":
    kw = {'gitee_user':sys.argv[1], 'gitee_pwd':sys.argv[2]}
    mgmt = SyncPckgMgmt(**kw)
    mgmt.sync_yaml_meta()