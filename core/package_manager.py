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
# Author: wangchong
# Create: 2020-10-26
# ******************************************************************************

"""
action for package
"""

import os
import re
import sys
import yaml
import shutil
import configparser
from concurrent.futures import ThreadPoolExecutor
from collections import Counter
from core.gitee_to_obs import SYNCCode
current_path = os.path.join(os.path.split(os.path.realpath(__file__))[0])
sys.path.append(os.path.join(current_path, ".."))
from common.log_obs import log
from common.parser_config import ParserConfigIni

class OBSPkgManager(object):
    """
    obs project package add delete modify check
    """
    def __init__(self, **kwargs):
        """
        obs_meta_path: obs_meta dir path
        patch_file_path: diff_patch file path
        kwargs: dict include giteeUserName giteeUserPwd obs_meta_path
        """
        self.kwargs = kwargs
        self.init_path = self.kwargs["init_path"]
        self.commitid = self.kwargs["cm_id"]
        self.obs_meta_path = self.kwargs["obs_meta_path"]
        cmd = "cd %s && git reset --hard %s && cd -" % (self.obs_meta_path, self.commitid)
        ret = os.system(cmd)
        self.patch_file_path = os.path.join(self.init_path, "diff_patch")
        self.giteeUserName = self.kwargs["gitee_user"]
        self.giteeUserPwd = self.kwargs["gitee_pwd"]
        self.sync_code = self.kwargs["sync_code"]
        self.multi_version_dir = ''
        os.chdir(self.init_path)
        p = ParserConfigIni()
        self.branch_proj_dict = p.get_branch_proj()

    def _git_clone(self, git_house):
        """
        git clone function
        """
        if git_house == "obs_meta":
            os.system("cd %s && git diff --name-status HEAD~1 HEAD~0 > %s && cd -"
                        % (self.obs_meta_path, self.patch_file_path))
        if git_house == "community":
            community_path = os.path.join(self.init_path, "community")
            if os.path.exists(community_path):
                shutil.rmtree(community_path)
            git_url = "https://%s:%s@gitee.com/openeuler/community.git" % (
                       self.giteeUserName, self.giteeUserPwd)
            ret = os.popen("git lfs --depth 1 clone %s %s" % (git_url, community_path)).read()
            log.debug(ret)
 
    def _add_pkg(self, proj, pkg, branch_name):
        """
        add project package
        """
        pkg_path = os.path.join(self.obs_meta_path, self.multi_version_dir, branch_name, proj, pkg)
        _tmpdir = os.popen("mktemp -d").read().strip('\n')
        cmd = "cd %s && osc co %s `osc ls %s 2>/dev/null | sed -n '1p'` &>/dev/null && cd -" % (_tmpdir, proj, proj)
        ret = os.popen(cmd).read()
        proj_tmpdir = os.path.join(_tmpdir, proj)
        if not os.path.exists(proj_tmpdir):
            log.error("failed to exec cmd: %s" % (cmd))
            shutil.rmtree(_tmpdir)
            return -1
        pkg_tmpdir = os.path.join(proj_tmpdir, pkg)
        if os.path.exists(pkg_tmpdir):
            ret = os.system("cp -rf %s %s" % (pkg_path, proj_tmpdir))
            cmd = "cd %s && osc status | grep ^? | awk '{print 2}' && cd -" % proj_tmpdir
            new_file = os.popen(cmd).read()
            if len(new_file):
                ret = os.system("cd %s && osc add %s && cd -" % (proj_tmpdir, new_file))
        else:
            rm_dir = os.path.join(pkg_tmpdir, ".osc")
            cmd = "cp -rf %s %s && rm -rf %s && cd %s && osc add %s && cd -" % (pkg_path, 
                    proj_tmpdir, rm_dir, proj_tmpdir, pkg)
            ret = os.popen(cmd).read()
        new_file = os.popen("cd %s && osc status && cd -" % (proj_tmpdir)).read()
        if len(new_file):
            ret = os.system("cd %s && osc ci -m 'add %s by %s' && cd -" % (proj_tmpdir, pkg, self.giteeUserName))
            log.info("add %s %s by %s succeessful" % (proj, pkg, self.giteeUserName))
        shutil.rmtree(_tmpdir)
 
    def _add_pkg_service(self, proj, pkg, branch_name):
        """
        write and push _service file in obs_meta
        return 0 or -1
        """
        proj_path = os.path.join(self.obs_meta_path, self.multi_version_dir, branch_name, proj)
        service_file = os.path.join(proj_path, pkg, "_service")
        if not os.path.exists(proj_path):
            log.warning("obs_meta do not have %s %s %s" % (self.multi_version_dir, branch_name, proj))
            return -1
        if os.system("test -f %s" % service_file) == 0:
            log.warning("obs_meta haved %s %s %s %s _service file, no need to add."
                    % (self.multi_version_dir, branch_name, proj, pkg))
            return -1
        os.chdir(proj_path)
        if not os.path.exists(pkg):
            os.mkdir(pkg)
        os.chdir(pkg)
        f = open("_service", 'w')
        f.write('<services>\n')
        f.write('    <service name="tar_scm_kernel_repo">\n')
        f.write('      <param name="scm">repo</param>\n')
        if branch_name == "master":
            f.write('      <param name="url">next/openEuler/%s</param>\n' % pkg)
        else:    
            f.write('      <param name="url">next/%s/%s</param>\n' % (branch_name, pkg))
        f.write('    </service>\n')
        f.write('</services>\n')
        f.close()
        os.chdir("%s/%s/%s/%s" % (self.obs_meta_path, self.multi_version_dir, branch_name, proj))
        os.system("git add %s" % pkg)
        os.system("git commit -m 'add _service file by %s'" % self.giteeUserName)
        log.info("add %s %s _service file by %s" % (proj, pkg, self.giteeUserName))
        for i in range(5):
            if os.system("git push") == 0:
                break
        return 0
 
    def _del_pkg(self, proj, pkg):
        """
        delete the project package
        return 0 or -1
        """
        cmd = "osc api -X DELETE /source/%s/%s" % (proj, pkg)
        ret = os.popen(cmd).read()
        if "<summary>Ok</summary>" in ret:
            log.info("delete %s %s success!" % (proj, pkg))
            return 0
        else:
            log.error("delete %s %s failed!" % (proj, pkg))
            return -1
 
    def _del_obs_pkg_service(self, proj, pkg):
        """
        delete the obs project package service file
        return 0 or -1
        """
        cmd = "osc api -X DELETE /source/%s/%s/_service" % (proj, pkg)
        ret = os.popen(cmd).read()
        if "<summary>Ok</summary>" in ret:
            log.info("delete %s %s _service by %s successful!" % (proj, pkg, self.giteeUserName))
            return 0
        else:
            log.error("delete %s %s _service failed!" % (proj, pkg))
            return -1
 
    def _del_meta_pkg_service(self, branch, proj, pkg):
        """
        delete the obs_meta project pkg service file
        return 0 or -1
        """
        proj_path = os.path.join(self.obs_meta_path, self.multi_version_dir, branch, proj)
        service_file = os.path.join(proj_path, pkg, "_service")
        if os.system("test -f %s" % service_file) != 0:
            log.warning("obs_meta not have %s %s %s %s _service file" % (self.multi_version_dir, branch, proj, pkg))
            return -1
        os.chdir(proj_path)
        os.system("rm -rf %s" % pkg)
        os.system("git add -A && git commit -m 'delete %s by %s'" % (pkg, self.giteeUserName))
        log.info("delete obs_meta %s %s %s %s by %s" % (self.multi_version_dir, branch, proj, pkg, self.giteeUserName))
        for i in range(5):
            if os.system("git push") == 0:
                break
        os.chdir(self.init_path)
        return 0
 
    def _modify_pkg_service(self, proj, pkg, branch_name):
        """
        change the service file for the package
        return 0 or -1
        """
        service_file_path = os.path.join(self.obs_meta_path, self.multi_version_dir, 
                branch_name, proj, pkg, "_service")
        _tmpdir = os.popen("mktemp -d").read().strip('\n')
        pkg_tmpdir = os.path.join(_tmpdir, proj, pkg)
        cmd = "cd %s && osc co %s %s &>/dev/null && cd -" % (_tmpdir, proj, pkg)
        if os.system(cmd) == 0:
            cmd = "cd %s && cp -f %s %s && osc add _service && osc ci -m 'modify by %s' && cd -" \
                    % (pkg_tmpdir, service_file_path, pkg_tmpdir, self.giteeUserName)
            if os.system(cmd) == 0:
                log.info("modify %s %s _service success!" % (proj, pkg))
                shutil.rmtree(_tmpdir)
                return 0
            else:
                log.error("modify %s %s _service failed!" % (proj, pkg))
                shutil.rmtree(_tmpdir)
                return -1
        else:
            log.warning("%s %s not found" % (proj, pkg))
            shutil.rmtree(_tmpdir)
            return -1
 
    def _modify_pkg_meta(self, proj, pkg, branch_name):
        """
        change the package of the meta
        return 0 or -1
        """
        file_path = os.path.join(self.obs_meta_path, self.multi_version_dir, 
                branch_name, proj, pkg, ".osc/_meta")
        _tmpdir = os.popen("mktemp -d").read().strip('\n')
        cmd = "cd %s && osc meta pkg %s %s --file=%s | grep ^Done. && cd -" % (_tmpdir, proj, pkg, file_path)
        if os.system(cmd) != 0:
            log.error("modify %s %s _meta failed!" % (proj, pkg))
            shutil.rmtree(_tmpdir)
            return -1
        shutil.rmtree(_tmpdir)
 
    def _change_pkg_prj(self, proj, new_proj, pkg, branch_name):
        """
        change the package of the project
        """
        self._del_pkg(proj, pkg)
        self._add_pkg(new_proj, pkg, branch_name)

    def _sync_pkg_code(self, proj, pkg, branch_name):
        """
        when adding a new package to a project, sync code
        """
        os.chdir(self.kwargs["init_path"])
        log.info("Start synchronization code...")
        self.kwargs['project'] = proj
        self.kwargs['repository'] = pkg
        self.kwargs['branch'] = branch_name
        sy = SYNCCode(**self.kwargs)
        sy.sync_code_to_obs()

    def _parse_git_log(self, line):
        """
        deal diff_patch line mesg
        """
        log.info("line:%s" % line)
        new_proj = ''
        new_pkg = ''
        new_file_path = ''
        multi_version_dir = ''
        log_list = list(line.split())
        temp_log_type = log_list[0]
        file_path = log_list[1]
        if len(log_list) == 3:
            new_file_path = list(line.split())[2]
            tmp_str2 = str(new_file_path).split('/')
            if len(tmp_str2) == 5:
                new_proj = tmp_str2[2]
                new_pkg = tmp_str2[3]
            else:
                new_proj = tmp_str2[1]
                new_pkg = tmp_str2[2]
        tmp_str = str(file_path).split('/')
        if len(tmp_str) == 5:
            multi_version_dir, branch_name, proj, pkg, file_name = tmp_str
        else:
            branch_name, proj, pkg, file_name = tmp_str
        if len(new_file_path) != 0:
            if new_pkg != pkg:
                log_type = "Rename-pkg-name"
            else:
                log_type = "Change-pkg-prj"
        elif file_name == "_meta":
            if temp_log_type == "A" or temp_log_type == "M":
                log_type = "Mod-pkg-meta"
            else:
                log.error("%s failed" % line)
        elif file_name == "_service":
            if temp_log_type == "A":
                log_type = "Add-pkg"
            elif temp_log_type == "D":
                pkg_path = os.path.join(self.obs_meta_path, multi_version_dir, '%s/%s/%s' % (branch_name, proj, pkg))
                if os.path.exists(pkg_path):
                    log_type = "Del-pkg-service"
                else:
                    log_type = "Del-pkg"
                    line = line.replace('_service', '').replace('\n', '')
                    pattern_message = line.replace(' ', '\t').replace('/', '\\/')
                    os.system("sed -i '/%s/d' %s" % (pattern_message, self.patch_file_path))
            elif temp_log_type == "M":
                log_type = "Mod-pkg-service"
            else:
                log.error("%s failed" % line)
        else:
            log.error("%s failed" % line)
        mesg_list = [log_type, branch_name, proj, pkg, new_proj, new_pkg, multi_version_dir]
        return mesg_list
   
    def _obs_pkgs_action(self):
        """
        operate on packages
        """
        file_content = []
        data = open(self.patch_file_path, 'r')
        for line in data:
            file_content.append(line.strip('\n'))
        data.close()
        with ThreadPoolExecutor(10) as executor:
            for content in file_content:
                executor.submit(self._obs_pkg_action, content)
        
    def _obs_pkg_action(self, file_content):
        """
        operate on a package
        file_content: a line of the patch
        """
        msg = self._deal_some_param(file_content)
        self._action_type(msg)

    def _action_type(self, msg):
        """
        operate on the package according to the log_type
        """
        self.multi_version_dir = msg["multi_version_dir"]
        if msg["log_type"] == "Add-pkg":
            if msg["exist_flag"] == 0:
                ret = self._add_pkg(msg["proj"], msg["pkg"], msg["branch_name"])
                if self.sync_code and ret != -1:
                    self._sync_pkg_code(msg["proj"], msg["pkg"], msg["branch_name"])
        elif msg["log_type"] == "Del-pkg":
            self._del_pkg(msg["proj"], msg["pkg"])
        elif msg["log_type"] == "Del-pkg-service":
            self._del_obs_pkg_service(msg["proj"], msg["pkg"])
        elif msg["log_type"] == "Mod-pkg-service":
            self._modify_pkg_service(msg["proj"], msg["pkg"], msg["branch_name"])
        elif msg["log_type"] == "Mod-pkg-meta":
            self._modify_pkg_meta(msg["proj"], msg["pkg"], msg["branch_name"])
        elif msg["log_type"] == "Change-pkg-prj":
            self._change_pkg_prj(msg["proj"], msg["new_proj"], msg["pkg"], msg["branch_name"])
            if self.sync_code:
                self._sync_pkg_code(msg["new_proj"], msg["pkg"], msg["branch_name"])
        elif msg["log_type"] == "Rename-pkg-name":
            self._del_pkg(msg["proj"], msg["pkg"])
            ret = self._add_pkg(msg["new_proj"], msg["new_pkg"], msg["branch_name"])
            if self.sync_code and ret != -1:
                self._sync_pkg_code(msg["new_proj"], msg["new_pkg"], msg["branch_name"])

    def _deal_some_param(self, file_content):
        """
        deal with some data and relation
        return a dict
        """
        pattern_string = ['.meta', '.prjconf', '/_service', '/_meta']
        proj_list = os.listdir(os.path.join(self.obs_meta_path, "master"))
        proj_list.remove("openEuler:Mainline:RISC-V")
        for pattern in pattern_string:
            cmd = 'echo "%s" | grep "%s$"' % (file_content.strip(), pattern)
            if os.popen(cmd).read():
                tmp = {}
                log_type, branch_name, proj, pkg, new_proj, new_pkg, \
                        multi_version_dir = self._parse_git_log(file_content)
                tmp["log_type"] = log_type
                tmp["branch_name"] = branch_name
                tmp["proj"] = proj
                tmp["pkg"] = pkg
                tmp["new_proj"] = new_proj
                tmp["new_pkg"] = new_pkg
                tmp["exist_flag"] = 0
                tmp["multi_version_dir"] = multi_version_dir
                for p in proj_list:
                    cmd = "osc ls %s 2>&1 | grep -q -Fx %s" % (p, pkg)
                    if os.system(cmd) == 0:
                        if p == proj:
                            log.info("package %s hava existed in obs project %s" % (pkg, p))
                            tmp["exist_flag"] = 1
                return tmp
            else:
                continue

    def obs_pkg_admc(self):
        """
        obs project package add, delete, modify, check
        """
        self._copy_packages()
        if self.kwargs["check_yaml"]:
            self._check_obs_pkg()
        if self.kwargs["check_meta"]:
            self._check_obs_meta_pkg()
        self._git_clone("obs_meta")
        self._obs_pkgs_action()

    def _parse_yaml_data(self):
        """
        Preprocessing the data
        """
        yaml_dict = {}
        yaml_path = os.path.join(self.init_path, "community/repository/src-openeuler.yaml")
        f1 = open(yaml_path, 'r')
        y = yaml.load(f1)
        for tmp in y['repositories']:
            name = tmp['name']
            branch = tmp['protected_branches']
            if "openEuler1.0-base" in branch:
                branch.remove("openEuler1.0-base")
            if "openEuler1.0" in branch:
                branch.remove("openEuler1.0")
            if "riscv" in branch:
                branch.remove("riscv")
            yaml_dict.setdefault(name, []).extend(branch)
        f1.close()
        del yaml_dict["ci_check"]
        del yaml_dict["build"]
        return yaml_dict
    
    def _parse_meta_data(self):
        data_list = []
        meta_bp_dict = {}
        meta_pb_dict = {}
        pkg_branch_dict = {}
        proj_pkg_dict = {}
        cmd = "cd %s && find | grep _service | grep -Ev 'OBS_PRJ_meta|openEuler-EPOL-LTS' | \
                awk -F '/' '{print $2,$3,$(NF-1)}' | sort | uniq > %s/res.txt && cd - &>/dev/null" % (
                        self.obs_meta_path, self.init_path)
        while os.system(cmd) != 0:
            continue
        f2 = open("%s/res.txt" % self.init_path, 'r')
        for line in f2:
            br = line.strip().split()[0]
            proj = line.strip().split()[1]
            name = line.strip().split()[2]
            if proj.endswith(":Bak"):
                continue
            meta_bp_dict.setdefault(br, []).append(proj)
            meta_pb_dict[proj] = br
            pkg_branch_dict.setdefault(name, []).append(br)
            proj_pkg_dict.setdefault(proj, []).append(name)
        f2.close()
        for key, value in meta_bp_dict.items():
            meta_bp_dict[key] = list(set(value))
        os.remove("%s/res.txt" % self.init_path)
        data_list.append(meta_bp_dict)
        data_list.append(pkg_branch_dict)
        data_list.append(proj_pkg_dict)
        data_list.append(meta_pb_dict)
        return data_list

    def _get_samebranchpkg_and_pkgwithoutservice(self):
        """
        get same packages under same branch and packages without _service file
        """
        same_pkg_dict = {}
        no_service_dict = {}
        proj_pkg_dict = {}
        meta_pb_dict = {}
        all_data = []
        for branch, projs in self.branch_proj_dict.items():
            proj_pkg = {}
            tmp_list = []
            tmp = {}
            for proj in projs.split(' '):
                if proj.endswith(":Bak") and "RISC-V" in proj and "selfbuild" in proj:
                    continue
                proj_path = os.path.join(self.obs_meta_path, branch, proj)
                if os.path.exists(proj_path):
                    meta_pb_dict[proj] = branch
                    pkglist = os.listdir(os.path.join(self.obs_meta_path, branch, proj))
                    if "README.md" in pkglist:
                        pkglist.remove("README.md")
                    if "readme.md" in pkglist:
                        pkglist.remove("readme.md")
                    if pkglist:
                        proj_pkg[proj] = pkglist
                        proj_pkg_dict[proj] = pkglist
                        tmp_list.extend(pkglist)
                        for pkg in pkglist:
                            pkg_service_path = os.path.join(proj_path, pkg, "_service")
                            if not os.path.exists(pkg_service_path):
                                no_service_dict.setdefault(proj, []).append(pkg)
            if tmp_list:
                b = dict(Counter(tmp_list))
                for key, value in b.items():
                    if value > 1:
                        for proj, pkg in proj_pkg.items():
                            if key in pkg:
                                tmp.setdefault(key, []).append(proj)
            if tmp:
                same_pkg_dict[branch] = tmp
        all_data.append(same_pkg_dict)
        all_data.append(no_service_dict)
        all_data.append(proj_pkg_dict)
        all_data.append(meta_pb_dict)
        return all_data

    def _check_obs_meta_pkg(self):
        same_pkg_dict = {}
        no_service_dict = {}
        proj_pkg_dict = {}
        meta_pb_dict = {}
        same_pkg_dict, no_service_dict, proj_pkg_dict, meta_pb_dict = self._get_samebranchpkg_and_pkgwithoutservice()
        log.info("=====Check need add or delete packages=====")
        for proj, pkg in proj_pkg_dict.items():
            log.info("Project:%s" % proj)
            obs_pkg = os.popen("osc ls %s 2>/dev/null" % proj).read().strip()
            obs_pkg = obs_pkg.replace('\n', ',').split(',')
            log.info("Obs pkg total:%s" % len(obs_pkg))
            log.info("Meta pkg total:%s" % len(pkg))
            need_add = set(pkg) - set(obs_pkg)
            log.info("Need add pkg total:%s" % len(need_add))
            log.info("Need add pkgname:%s" % list(need_add))
            need_del = set(obs_pkg) - set(pkg)
            log.info("Need del pkg total:%s" % len(need_del))
            log.info("Need del pkgname:%s" % list(need_del))
            if proj in no_service_dict.keys():
                log.info("Without _service file pkgname:%s" % no_service_dict[proj])
            else:
                log.info("Without _service file pkgname:[]")
            if len(need_add):
                for pkgname in list(need_add):
                    self._add_pkg(proj, pkgname, meta_pb_dict[proj])
                    if self.sync_code:
                        self._sync_pkg_code(proj, pkgname, meta_pb_dict[proj])
            if len(need_del):
                for pkgname in list(need_del):
                    self._del_pkg(proj, pkgname)
            log.info("===========================")
        log.info("=====Check same package under same branch report=====")
        for branch, msg in same_pkg_dict.items():
            log.info("Branch : %s" % branch)
            log.info("Packagename\tPorjectname")
            for pkg, proj in msg.items():
                log.info("%s\t%s" % (pkg, proj))
            log.info("=====================================================")
        if same_pkg_dict or no_service_dict:
            log.info("Have some problems !!!")
            sys.exit(1)
        else:
            log.info("Have no problems !!!")
            sys.exit(0)

    def _check_yaml_meta_pkg(self, yaml_dict, meta_bp_dict, pkg_branch_dict):
        """
        check src-openeuler.yaml file and obs_meta, then add or del branch pkg.
        """
        p = ParserConfigIni()
        branch_proj_dict = p.get_branch_proj()
        log.info("check BEGIN")
        log.info("check stage 1:")
        for pkg, branch in yaml_dict.items():
            if pkg in pkg_branch_dict:
                branch.sort()
                pkg_branch_dict[pkg].sort()
                if branch == pkg_branch_dict[pkg]:
                    continue
                else:
                    diff_add_br = set(branch).difference(set(pkg_branch_dict[pkg]))
                    for diff in diff_add_br:
                        if diff == "master":
                            res = self._add_pkg_service(branch_proj_dict[diff].split(' ')[0], pkg, diff)
                            if res == 0:
                                self._add_pkg(branch_proj_dict[diff].split(' ')[0], pkg, diff)
                        else:
                            log.info("%s %s %s skip add"
                                    % (branch_proj_dict[diff].split(' ')[0], diff, pkg))
            else:
                for need_add_br in yaml_dict[pkg]:
                    if need_add_br == "master":
                        res = self._add_pkg_service(branch_proj_dict[need_add_br].split(' ')[0], pkg, need_add_br)
                        if res == 0:
                            self._add_pkg(branch_proj_dict[need_add_br].split(' ')[0], pkg, need_add_br)
                    else:
                        log.info("%s %s %s skip add"
                                % (branch_proj_dict[need_add_br].split(' ')[0], need_add_br, pkg))
        log.info("check stage 2:")
        for pkg, branch in pkg_branch_dict.items():
            if pkg in yaml_dict:
                branch.sort()
                yaml_dict[pkg].sort()
                if branch == yaml_dict[pkg]:
                    continue
                else:
                    diff_del_br = set(branch).difference(set(yaml_dict[pkg]))
                    for diff in diff_del_br:
                        if diff == "master":
                            for proj in meta_bp_dict[diff]:
                                self._del_meta_pkg_service(diff, proj, pkg)
                                self._del_pkg(proj, pkg)
                        else:
                            log.info("%s %s skip delete" % (diff, pkg))
            else:
                for need_del_br in pkg_branch_dict[pkg]:
                    if need_del_br == "master":
                        for proj in meta_bp_dict[need_del_br]:
                            self._del_meta_pkg_service(need_del_br, proj, pkg)
                            self._del_pkg(proj, pkg)
                    else:
                        log.info("%s %s skip delete" % (need_del_br, pkg))
        log.info("check END")

    def _check_obs_pkg(self):
        """
        check the obs project and operate according to the src-openeuler.yaml file
        """
        yaml_dict = {}
        self._git_clone("community")
        yaml_dict = self._parse_yaml_data()
        mylist = self._parse_meta_data()
        self._check_yaml_meta_pkg(yaml_dict, mylist[0], mylist[1])

    def _copy_package(self, pkg, from_path, to_path):
        """
        copy package from from_path to to_path
        from_path: path of package that will be copied
        to_path: path fo package that will go
        """
        if self.kwargs["branch"] == "master":
            cmd = "cp -r %s/%s %s && sed -i 's/openEuler/%s/g' %s/%s/_service" % \
                    (from_path, pkg, to_path, self.kwargs["branch2"], to_path, pkg)
        else:
            cmd = "cp -r %s/%s %s && sed -i 's/%s/%s/g' %s/%s/_service" % \
                    (from_path, pkg, to_path, self.kwargs["branch"], \
                    self.kwargs["branch2"], to_path, pkg)
        ret = os.popen(cmd).read()
        log.debug(ret)

    def _copy_packages(self):
        """
        copy some packages from obs project A to project B
        """
        if self.kwargs["branch2"] and self.kwargs["project2"]:
            os.chdir(self.kwargs["obs_meta_path"])
            from_path = os.path.join(self.kwargs["branch"], self.kwargs["project"])
            to_path = os.path.join(self.kwargs["branch2"], self.kwargs["project2"])
            pkgs = self.kwargs["pkglist"]
            if not pkgs:
                pkgs = os.listdir(from_path)
            for pkg in pkgs:
                self._copy_package(pkg, from_path, to_path)
            cmd = "git add %s && git commit -m 'add pkgs to project %s' && git push" % \
                    (to_path, self.kwargs["project2"])
            ret = os.popen(cmd).read()
            log.debug(ret)


if __name__ == "__main__":
    kw = {"gitee_user":sys.argv[1], "gitee_pwd":sys.argv[2],
            "obs_meta_path":sys.argv[3], "check_yaml":0,
            "check_meta":0}
    pm = OBSPkgManager(**kw)
    pm.obs_pkg_admc()
