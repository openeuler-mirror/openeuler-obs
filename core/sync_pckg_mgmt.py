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
import sys
import yaml
import shutil
now_path = os.path.join(os.path.split(os.path.realpath(__file__))[0])
sys.path.append(os.path.join(now_path, ".."))
from common.log_obs import log


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

    def _add_pkg_service(self, tmp):
        """
        add obs_meta packages _service file
        """
        from_pkg_path = os.path.join(self.obs_meta_path, tmp['branch_from'], tmp['obs_from'], tmp['pkgname'])
        pkg_path = os.path.join(self.obs_meta_path, tmp['branch_to'], tmp['obs_to'], tmp['pkgname'])
        pkg_service_path = os.path.join(pkg_path, "_service")
        if tmp['branch_from'] == "master":
            branch = "openEuler"
        else:
            branch = tmp['branch_from']
        if not os.path.exists(pkg_path):
            os.makedirs(pkg_path)
        if not os.path.exists(pkg_service_path):
            cmd = "cp %s/_service %s/_service" % (from_pkg_path, pkg_path)
            if os.system(cmd) == 0:
                cmd = "sed -i 's/%s\//%s\//g' %s/_service" % (branch, tmp['branch_to'], pkg_path)
                if os.system(cmd) == 0:
                    log.info("add %s %s %s _service succeed!" % (tmp['branch_to'], tmp['obs_to'], tmp['pkgname']))
                else:
                    log.info("add %s %s %s _service failed!" % (tmp['branch_to'], tmp['obs_to'], tmp['pkgname']))
            else:
                log.error("copy %s service file failed!" % tmp['pkgname'])
    
    def _add_prj_meta_pkgs_service(self, msg):
        for tmp in msg:
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
                if "Epol" not in tmp['obs_to']:
                    self._write_selfbuild_meta_file(selfbuild_meta_path, tmp['obs_to'])
            self._add_pkg_service(tmp)

    def _del_pkg(self, tmp):
        """
        delete obs_meta packages
        """
        pkg_path = os.path.join(self.obs_meta_path, tmp['branch_to'], tmp['obs_to'], tmp['pkgname'])
        if os.path.exists(pkg_path):
            shutil.rmtree(pkg_path)
            log.info("delete %s %s %s succeed!" % (tmp['branch_to'], tmp['obs_to'], tmp['pkgname']))

    def _verify_meta_file(self, prj_pkg):
        """
        verify obs_meta with pckg-mgmt.yaml
        """
        for proj, pkg in prj_pkg.items():
            if proj != "branch":
                meta_pkglist = os.listdir(os.path.join(self.obs_meta_path, prj_pkg['branch'], proj))
                need_del_pkg = set(meta_pkglist) - set(pkg)
                log.info("obs_meta %s %s redundant pkg:%s" % (prj_pkg['branch'], proj, list(need_del_pkg)))
                for del_pkg in need_del_pkg:
                    tmp = {'pkgname': del_pkg, 'branch_to': prj_pkg['branch'], 'obs_to': proj}
                    self._del_pkg(tmp)

    def _push_code(self):
        """
        push code to gitee repo
        """
        if os.path.exists(self.obs_meta_path):
            os.chdir(self.obs_meta_path)
            cmd = "git status -s"
            if os.popen(cmd).read():
                cmd = "git add -A && git commit -m \"synchronize with pckg-mgmt.yaml file contents\""
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
            log.error("%s not exist!" % self.obs_meta_path)
            return -1

    def sync_yaml_meta(self):
        """
        integration of functions
        """
        change_file = self._get_change_file()
        yaml_dict = {}
        for line in change_file:
            log.info("line:%s" % line)
            name = list(line.split())[1]
            branch = name.split('/')[0]
            file_path = os.path.join(self.release_management_path, name)
            yaml_dict = self._get_yaml_file_msg(file_path)
            if not yaml_dict:
                log.info("%s file content is empty!" % name)
            else:
                if "everything" in yaml_dict['packages'].keys():
                    msg, del_msg, prj_pkg = self._parse_yaml_msg(yaml_dict, "new")
                    self._add_prj_meta_pkgs_service(msg)
                else:
                    msg, del_msg, prj_pkg = self._parse_yaml_msg(yaml_dict, "old")
                    self._add_prj_meta_pkgs_service(msg)
                for tmp in del_msg:
                    self._del_pkg(tmp)
                self._verify_meta_file(prj_pkg)
        ret = self._push_code()
        return ret


if __name__ == "__main__":
    kw = {'gitee_user':sys.argv[1], 'gitee_pwd':sys.argv[2]}
    mgmt = SyncPckgMgmt(**kw)
    mgmt.sync_yaml_meta()
