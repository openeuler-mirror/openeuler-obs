#!/bin/env python3

"""
created by: wangchong
date: 2020-10-26
"""

import os
import re
import sys
import git
import shutil
import configparser
current_path = os.path.join(os.path.split(os.path.realpath(__file__))[0])
sys.path.append(os.path.join(current_path, ".."))
from common.log_obs import log
from common.parser_config import ParserConfigIni

class OBSPkgManager(object):
    """
    obs project package add delete modify check
    """
    def __init__(self, kargs):
        """
        obs_meta_path: obs_meta dir path
        patch_file_path: diff_patch file path
        kargs: dict include giteeUserName giteeUserPwd obs_meta_path
        """
        self.work_dir = "/jenkins_home/workspace/obs_meta_update/openeuler_jenkins"
        self.obs_meta_path = os.path.join(self.work_dir, kargs["obs_meta_path"])
        self.patch_file_path = os.path.join(self.work_dir, "diff_patch")
        self.giteeUserName = kargs["giteeUserName"]
        self.giteeUserPwd = kargs["giteeUserPwd"]
        self.import_list = []

    def _pre_env(self):
        """
        initialize the workdir
        """
        if os.path.exists(self.work_dir):
            shutil.rmtree(self.work_dir)
        os.makedirs(self.work_dir)
        os.chdir(self.work_dir)
    
    def _git_clone(self, git_house):
        """
        git clone function
        """
        if git_house == "obs_meta":
            if os.path.exists(self.obs_meta_path):
                shutil.rmtree(self.obs_meta_path)
            git_url = "https://%s:%s@gitee.com/src-openeuler/obs_meta.git" % (
                       self.giteeUserName, self.giteeUserPwd)
            git.Repo.clone_from(url = git_url, to_path = self.obs_meta_path)
            os.chdir(self.obs_meta_path)
            os.system("git diff --name-status HEAD~1 HEAD~0 > %s"
                        % self.patch_file_path)
        if git_house == "community":
            community_path = os.path.join(self.work_dir, "community")
            if os.path.exists(community_path):
                shutil.rmtree(community_path)
            git_url = "https://%s:%s@gitee.com/openeuler/community.git" % (
                       self.giteeUserName, self.giteeUserPwd)
            git.Repo.clone_from(url = git_url, to_path = community_path)
        os.chdir(self.work_dir)
    
    def _add_pkg(self, proj, pkg, branch_name):
        """
        add project package
        """
        os.chdir(self.work_dir)
        if os.path.exists(proj):
            shutil.rmtree(proj)
        if os.system("osc ls %s %s &>/dev/null" % (proj, pkg)) == 0:
            os.system("osc co %s %s &>/dev/null" % (proj, pkg))
        else:
            os.system("osc co %s `osc ls %s | sed -n '1p'` &>/dev/null" % (proj, proj))
        pkg_path = os.path.join(self.obs_meta_path, '%s/%s/%s' % (branch_name, proj, pkg))
        os.chdir(proj)
        if os.path.exists(pkg):
            os.system("cp -rf %s ." % pkg_path)
            cmd = "osc status | grep ^? | awk '{print 2}'"
            new_file = os.popen(cmd).read()
            if len(new_file):
                os.system("osc add %s" % new_file)
        else:
            os.system("cp -rf %s ." % pkg_path)
            rm_dir = os.path.join('%s/.osc' % pkg)
            if os.path.exists(rm_dir):
                os.system("rm -rf %s" % rm_dir)
            os.system("osc add %s" % pkg)
        new_file = os.popen("osc status").read()
        if len(new_file):
            os.system("osc ci -m 'add by %s'" % self.giteeUserName)
        os.chdir(self.work_dir)
    
    def _add_pkg_service(self, proj, pkg, branch_name):
        """
        write and push _service file in obs_meta
        return 0 or -1
        """
        proj_path = os.path.join(self.obs_meta_path, branch_name, proj)
        service_file = os.path.join(proj_path, pkg, "_service")
        if not os.path.exists(proj_path):
            log.warning("obs_meta do not have %s %s" % (branch_name, proj))
            return -1
        if os.system("test -f %s" % service_file) == 0:
            log.warning("obs_meta haved %s %s %s _service file, no need to add." % (branch_name, proj, pkg))
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
        os.chdir("%s/%s/%s" % (self.obs_meta_path, branch_name, proj))
        os.system("git add %s" % pkg)
        os.system("git commit -m 'add %s _service file by %s'" % (pkg, self.giteeUserName))
        os.system("git push")
        return 0
    
    def _del_pkg(self, proj, pkg):
        """
        delete the project package
        return 0 or -1
        """
        os.chdir(self.work_dir)
        proj_path = os.path.join(self.work_dir, proj)
        if os.system("osc ls %s %s &>/dev/null" % (proj, pkg)) == 0:
            if os.path.exists(proj_path):
                shutil.rmtree(proj)
            os.system("osc co %s %s &>/dev/null" % (proj, pkg))
            os.chdir(proj)
            os.system("osc rm %s" % pkg)
            os.system("osc ci -m 'delete by %s'" % self.giteeUserName)
        else:
            log.warning("obs %s %s not found" % (proj, pkg))
            return -1
        os.chdir(self.work_dir)
        return 0
    
    def _del_obs_pkg_service(self, proj, pkg):
        """
        delete the obs project package service file
        return 0 or -1
        """
        if os.system("osc ls %s %s &>/dev/null" % (proj, pkg)) != 0:
            log.warning("obs %s %s not found" % (proj, pkg))
            return -1
        os.chdir(self.work_dir)
        proj_path = os.path.join(self.work_dir, proj)
        pkg_path = os.path.join(proj_path, pkg)
        if os.path.exists(proj_path):
            shutil.rmtree(proj)
        os.system("osc co %s %s &>/dev/null" % (proj, pkg))
        os.chdir(pkg_path)
        os.system("test -f _service && osc rm _service")
        os.system("osc ci -m 'delete by %s'" % self.giteeUserName)
        os.chdir(self.work_dir)
        return 0
    
    def _del_meta_pkg_service(self, branch, proj, pkg):
        """
        delete the obs_meta project pkg service file
        return 0 or -1
        """
        proj_path = os.path.join(self.obs_meta_path, branch, proj)
        service_file = os.path.join(proj_path, pkg, "_service")
        if os.system("test -f %s" % service_file) != 0:
            log.warning("obs_meta not have %s %s %s _service file" % (branch_name, proj, pkg))
            return -1
        os.chdir(proj_path)
        os.system("rm -rf %s" % pkg)
        os.system("git add -A && git commit -m 'delete %s %s %s by %s'" % (
            branch, proj, pkg, self.giteeUserName))
        os.system("git push")
        os.chdir(self.work_dir)
        return 0
    
    def _modify_pkg_service(self, proj, pkg, branch_name):
        """
        change the service file for the package
        return 0 or -1
        """
        if os.system("osc ls %s %s &>/dev/null" % (proj, pkg)) != 0:
            log.warning("%s %s not found" % (proj, pkg))
            return -1
        os.chdir(self.work_dir)
        proj_path = os.path.join(self.work_dir, proj)
        pkg_path = os.path.join(proj_path, pkg)
        service_file_path = os.path.join(self.obs_meta_path, "%s/%s/%s/_service"
                % (branch_name, proj, pkg))
        if os.path.exists(proj_path):
            shutil.rmtree(proj)
        os.system("osc co %s %s &>/dev/null" % (proj, pkg))
        os.system("cp -f %s %s" % (service_file_path, pkg_path))
        os.chdir(pkg_path)
        os.system("osc add _service")
        os.system("osc ci -m 'modify by %s'" % self.giteeUserName)
        os.chdir(self.work_dir)
        return 0
    
    def _modify_pkg_meta(self, proj, pkg, branch_name):
        """
        change the package of the meta
        return 0 or -1
        """
        if os.system("osc ls %s %s &>/dev/null" % (proj, pkg)) != 0:
            log.warning("%s %s not found" % (proj, pkg))
            return -1
        os.chdir(self.work_dir)
        file_path = os.path.join(self.obs_meta_path, "%s/%s/%s/.osc/_meta"
                % (branch_name, proj, pkg))
        cmd = "osc meta pkg %s %s --file=%s | grep ^Done." % (proj, pkg, file_path)
        if os.system(cmd) != 0:
            log.error("%s/%s/.osc/_meta deal error" % (proj, pkg))
            return -1
        return 0
    
    def _change_pkg_prj(self, proj, new_proj, pkg, branch_name):
        """
        change the package of the project
        """
        self._del_pkg(proj, pkg)
        self._add_pkg(new_proj, pkg, branch_name)
    
    def _parse_git_log(self, line):
        """
        deal diff_patch line mesg
        """
        new_proj = ''
        new_file_path = ''
        log_list = list(line.split())
        temp_log_type = log_list[0]
        file_path = log_list[1]
        if len(log_list) == 3:
            new_file_path = list(line.split())[2]
        branch_name, proj, pkg, file_name = str(file_path).split('/')
        if len(new_file_path) != 0:
            new_proj = new_file_path.split('/')[1]
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
                pkg_path = os.path.join(self.obs_meta_path, '%s/%s/%s' % (branch_name, proj, pkg))
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
        mesg_list = [log_type, branch_name, proj, pkg, new_proj]  
        return mesg_list
    
    def _deal_some_param(self):
        """
        deal with some data and relation
        """
        pattern_string = ['.meta', '.prjconf', '/_service', '/_meta']
        for pattern in pattern_string:
            data = open(self.patch_file_path, 'r')
            for line in data:
                cmd1 = 'echo "%s" | grep "%s$"' % (line.strip(), pattern)
                if os.popen(cmd1).read():
                    tmp = {}
                    line = line.strip('\n')
                    log_type, branch_name, proj, pkg, new_proj = self._parse_git_log(line)
                    tmp["log_type"] = log_type
                    tmp["branch_name"] = branch_name
                    tmp["proj"] = proj
                    tmp["pkg"] = pkg
                    tmp["new_proj"] = new_proj
                    tmp["exist_flag"] = 0
                    prj_list = ['openEuler:Mainline', 'openEuler:Factory',
                                'openEuler:Epol', 'openEuler:Extras', 'bringInRely']
                    for p in prj_list:
                        cmd3 = "osc ls %s 2>&1 | grep -q -Fx %s" % (p, pkg)
                        if os.system(cmd3) == 0:
                            if p == proj:
                                log.info("package %s hava existed in obs project %s" % (pkg, p))
                                tmp["exist_flag"] = 1
                    self.import_list.append(tmp)
                else:
                    continue
            data.close()

    def obs_pkg_admc(self):
        """
        obs project package add, delete, modify, check
        """
        #self._pre_env()
        #self._git_clone("obs_meta")
        self._deal_some_param()
        log.info(self.import_list)
        for msg in self.import_list:
            if msg["log_type"] == "Add-pkg":
                if msg["exist_flag"] == 0:
                    self._add_pkg(msg["proj"], msg["pkg"], msg["branch_name"])
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
        return 0

    def _pre_data(self):
        """
        Preprocessing the data
        """
        os.chdir(self.work_dir)
        yaml_path = os.path.join(self.work_dir, "community/repository")
        f1 = open("%s/src-openeuler.yaml" % yaml_path, 'r')
        yaml_dict = {}
        meta_bp_dict = {}
        pkg_branch_dict = {}
        for line in f1:
            if re.search("- name:", line):
                pkg_name = line.split()[2]
            if re.search("  - ", line):
                branch = line.split()[1]
                if branch != "openEuler1.0-base" and branch != "openEuler1.0":
                    yaml_dict.setdefault(pkg_name, []).append(branch)
        f1.close()
        del yaml_dict["ci_check"]
        del yaml_dict["build"]
        os.chdir(self.obs_meta_path)
        cmd = "find | grep _service | grep -Ev 'OBS_PRJ_meta' | \
                awk -F '/' '{print $2,$3,$(NF-1)}' | sort | uniq > %s/res.txt" % self.work_dir
        while os.system(cmd) != 0:
            continue
        os.chdir(self.work_dir)
        f2 = open("%s/res.txt" % self.work_dir, 'r')
        for line in f2:
            br = line.strip().split()[0]
            proj = line.strip().split()[1]
            name = line.strip().split()[2]
            meta_bp_dict.setdefault(br, []).append(proj)
            pkg_branch_dict.setdefault(name, []).append(br)
        f2.close()
        os.remove("%s/res.txt" % self.work_dir)
        return yaml_dict, meta_bp_dict, pkg_branch_dict
    
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
                        res = self._add_pkg_service(branch_proj_dict[diff.lower()].split(' ')[0], pkg, diff)
                        if res == 0:
                            self._add_pkg(branch_proj_dict[diff.lower()].split(' ')[0], pkg, diff)
            else:
                for need_add_br in yaml_dict[pkg]:
                    res = self._add_pkg_service(branch_proj_dict[need_add_br.lower()].split(' ')[0], pkg, need_add_br)
                    if res == 0:
                        self._add_pkg(branch_proj_dict[need_add_br.lower()].split(' ')[0], pkg, need_add_br)
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
                        for proj in meta_bp_dict[diff]:
                            self._del_meta_pkg_service(diff, proj, pkg)
                            self._del_pkg(proj, pkg)
            else:
                for need_del_br in pkg_branch_dict[pkg]:
                    for proj in meta_bp_dict[need_del_br]:
                        self._del_meta_pkg_service(need_del_br, proj, pkg)
                        self._del_pkg(proj, pkg)
        log.info("check END")

    def check_obs_pkg(self):
        """
        check the obs project and operate according to the src-openeuler.yaml file
        """
        yaml_dict = {}
        meta_bp_dict = {}
        pkg_branch_dict = {}
        self._pre_env()
        self._git_clone("community")
        self._git_clone("obs_meta")
        yaml_dict, meta_bp_dict, pkg_branch_dict = self._pre_data()
        self._check_yaml_meta_pkg(yaml_dict, meta_bp_dict, pkg_branch_dict)
    

if __name__ == "__main__":
    kargs = {"giteeUserName":sys.argv[1], "giteeUserPwd":sys.argv[2], "obs_meta_path":sys.argv[3]}
    pm = OBSPkgManager(kargs)
    pm.obs_pkg_admc()
    pm.check_obs_pkg()
