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
# Author: yaokai
# Create: 2020-10-26
# ******************************************************************************
"""
sync code from gitee to obs
"""
import re
import sys
import os
import time
import shutil
import json
import requests
import threadpool
current_path = os.path.join(os.path.split(os.path.realpath(__file__))[0])
sys.path.append(os.path.join(current_path, ".."))
from common.log_obs import log
from common.common import Pexpect
from common.common import git_repo_src
from common.parser_config import ParserConfigIni


class SYNCCode(object):
    """
    if the rpm package has changed in gitee what you should donext
    (Synchronize the latest code to OBS)
    """
    def __init__(self, **kwargs):
        """
        kargs: dict, init dict by 'a': 'A' style
        The dict key_value as the following:
            repository: The package you want sync it to obs
            gitee_branch: The branch for you commit in gitee
            giteeuser: The gitee account
            giteeuserpwd: The gitee passwd
            meta_path: Where the obs_meta save in jenkins
            obs_server_user: The user name for you use in server
            obs_server_ip: The ip for you server
            obs_server_passwd: The password for your ip
            obs_server_port: The port for your ip
        """
        self.timestr = time.strftime("%Y%m%d %H-%M-%S", time.localtime())
        self.kwargs = kwargs
        self.repository = self.kwargs['repository']
        self.gitee_branch = self.kwargs['branch']
        self.giteeuser = self.kwargs['gitee_user']
        self.giteeuserpwd = self.kwargs['gitee_pwd']
        self.meta_path = self.kwargs['obs_meta_path']
        self.pkgs = self.kwargs['pkglist']
        self.project = self.kwargs['project']
        self.cmd = Pexpect(self.kwargs['source_server_user'],
                self.kwargs['source_server_ip'],
                self.kwargs['source_server_pwd'],
                self.kwargs['source_server_port'])
        par = ParserConfigIni()
        self.obs_pkg_rpms_url = par.get_repos_dict()["obs_pkg_rpms"]
        self.obs_pkg_prms_files_dir = None
        self.sync_failed_rpms = []

    def _write_date_to_file(self):
        """
        write date repository changed to file
        """
        tmpdir = os.popen("mktemp").read().split("\n")[0]
        self.obs_pkg_prms_files_dir = git_repo_src(self.obs_pkg_rpms_url, self.giteeuser, self.giteeuserpwd, tmpdir)
        try:
            branch_path = os.path.join(self.obs_pkg_prms_files_dir, self.gitee_branch)
            if not os.path.exists(branch_path):
                os.makedirs(branch_path)
            cmd1 = "echo %s > %s/%s" % (self.timestr, branch_path, self.repository)
            if os.system(cmd1) != 0:
                log.error("fail to write date of package changed to file")
            cmd2 = "cd %s && git pull && git add * && git commit -m 'update date for pkg %s' && git push"\
                    % (self.obs_pkg_prms_files_dir, self.repository)
            if os.system(cmd2) != 0:
                log.error("fail to update file to %s" % self.repository)
        except AttributeError as e:
            log.error(e)
        finally:
            cmd = "rm -rf %s" % tmpdir
            os.system(cmd)

    def _git_clone(self, rpm_dir, gitee_branch, path):
        """
        rpm_dir: The name for git repository "it will exist under the current directory"
        rpm_branch: The branch you want to checkout for this git repository
        """
        log.info("Git clone the %s in %s" % (rpm_dir, gitee_branch))
        self.cmd.ssh_cmd("rm -rf %s " % (path))
        repo_url = "https://%s:%s@gitee.com/src-openEuler/%s" % (self.giteeuser, self.giteeuserpwd, rpm_dir)
        for i in range(5):
            clone_result = self.cmd.ssh_cmd("git lfs clone --depth=1 %s -b %s %s"
                    % (repo_url, gitee_branch, path), 600)
            pull_result_last = str(self.cmd.ssh_cmd('git -C %s pull' % path)[1].strip()).split("'")[1]
            if "Already" in pull_result_last:
                log.info(pull_result_last)
                log.info("At now %s the branch is in %s" % (rpm_dir, gitee_branch))
                return True
            else:
                log.info("_GIT_CLONE: %s" % i)
                clear_repo = self.cmd.ssh_cmd("rm -rf %s" % path)
                log.info("clear_repo:%s" % clear_repo)
                continue
        log.error("_GIT_CLONE_ERROR: %s" % rpm_dir)
        return False

    def _get_obs_project(self):
        """
        Get the obs project from gitee_branch
        """
        log.info("Start get the obs_project")
        if "multi" in self.gitee_branch:
            path = self.meta_path + '/' + 'multi_version/' + self.gitee_branch
            log.info(path)
            cmd = "find %s -name %s | awk -F '/' '{print $5}'" % (path, self.repository)
        else:
            path = self.meta_path + '/' + self.gitee_branch
            log.info(path)
            cmd = "find %s -name %s | awk -F '/' '{print $4}'" % (path, self.repository)
        all_project = os.popen(cmd).readlines()
        log.info(all_project)
        obs_project = None
        for project in all_project:
            obs_project = project.replace('\n', '')
            if ":Bak" in obs_project:
                continue
            else:
                break
        if obs_project and ":Bak" not in obs_project:
            log.info("The %s obs_project for gitee_%s is <<<<%s>>>>" % (
                self.repository, self.gitee_branch, obs_project))
            return obs_project
        else:
            log.error("Failed !!! The rpm is not exist in %s branch !!!"
                    % self.gitee_branch)
            return False

    def _get_latest_gitee_pull(self):
        """
        make the obs server code be the latest
        """
        if self.gitee_branch == "master":
            source_path = "/srv/cache/obs/tar_scm/repo/next/openEuler"
        elif "multi" in self.gitee_branch:
            source_path = "/srv/cache/obs/tar_scm/repo/next/openEuler/multi_version/" + self.gitee_branch
        else:
            source_path = "/srv/cache/obs/tar_scm/repo/next/" + self.gitee_branch
        if self.repository == "CreateImage":
            log.error("The <<CreateImage>> packages does not need to be sync!!!")
            return False
        elif self.repository == "kernel":
            pull_result = str(self.cmd.ssh_cmd("git -C %s/kernel pull" % source_path)
                    [1].strip()).split("'")[1]
            log.info(pull_result)
            tag_path = "%s/kernel/SOURCE" % source_path
            kernel_tags = str(self.cmd.ssh_cmd("cat %s" % tag_path)[1].strip()).split("'")[1]
            log.info(kernel_tags)
            open_kernel_path = "%s/openEuler-kernel/kernel" % source_path
            open_kernel_git = "https://%s:%s@gitee.com/openeuler/kernel" % (self.giteeuser, self.giteeuserpwd)
            log.info(open_kernel_git)
            ssh_rm_result = self.cmd.ssh_cmd("rm -rf %s" % open_kernel_path)
            log.info(ssh_rm_result)
            ssh_clone_result = self.cmd.ssh_cmd("git lfs clone --depth=1 %s -b %s %s" % (open_kernel_git,
                kernel_tags, open_kernel_path), 600)
            pull_result_last = str(self.cmd.ssh_cmd('git -C %s pull' % open_kernel_path)[1].strip()).split("'")[1]
            if "Already" in pull_result_last:
                log.info(pull_result_last)
                log.info("kernel gitee pull success")
                return True
            else:
                log.error("kernel gitee pull failed")
                return False
        else:
            rpm_path = source_path + '/' + self.repository
            ssh_cmd = "if [ -d %s ];then echo 'exist';else echo 'need to clone';fi" % rpm_path
            repository_exist = self.cmd.ssh_cmd(ssh_cmd)
            repository_exist = str(repository_exist[1].strip()).split("'")[1]
            log.info(self.repository + ':' + repository_exist)
            if repository_exist == 'exist':
                pull_result = str(self.cmd.ssh_cmd('git -C %s pull' % rpm_path)[1].strip()).split("'")[1]
                log.info(pull_result)
                pull_result_last = str(self.cmd.ssh_cmd('git -C %s pull' % rpm_path)[1].strip()).split("'")[1]
                if "Already" in pull_result_last:
                    log.info(pull_result_last)
                    return True
                else:
                    clone_result = self._git_clone(self.repository, self.gitee_branch, rpm_path)
                    return clone_result
            else:
                clone_result = self._git_clone(self.repository, self.gitee_branch, rpm_path)
                return clone_result

    def _gitee_pr_to_obs(self, obs_pro):
        """
        obs_pro:The obs project that gitee branch corresponds
        """
        osc_service = os.popen("osc service remoterun %s %s" % (obs_pro, self.repository)).readlines()
        for results in osc_service:
            if "ok" in results:
                log.info(results)
                log.info("Success for osc service remoterun the %s" % self.repository)
                return True
            else:
                continue
        log.error("Failed !!! fail to service remoterun !!!")
        return False

    def _pre_sync_code(self, project=None):
        """
        The way to offer that make all fuction runing
        """
        if not project:
            obs_project = self._get_obs_project()
        else:
            obs_project = project
            log.info("The %s in %s" % (self.repository, obs_project))
        pull_result = self._get_latest_gitee_pull()
        remoterun_result = self._gitee_pr_to_obs(obs_project)
        if obs_project and pull_result and remoterun_result:
            log.info("SYNC %s in %s SUCCESS" % (self.repository, obs_project))
            return True
        else:
            log.error("SYNC %s in %s ERROR: Please check the log.error" % (self.repository, obs_project))
            return False

    def sync_code_to_obs(self):
        """
        The only way to offer that make all fuction runing
        """
        if not self.pkgs:
            if self.repository and self.gitee_branch:
                if not self._pre_sync_code(self.project):
                    raise SystemExit("SYNC %s ERROR" % self.repository)
            else:
                raise SystemExit('please check you arguments')
        else:
            if "broken" == self.pkgs[0] and len(self.pkgs) == 1:
                project_flag = "yes"
                broken_cmd = "osc r --csv %s -r standard_aarch64 -a aarch64 2>/dev/null | \
                        grep broken | awk -F ';' '{print $1}'" % self.project
                log.info("Get the broken rpm:%s" % broken_cmd)
                broken_result = os.popen(broken_cmd).read()
                log.debug(broken_result)
                broken_list = broken_result.split('\n')
                self.pkgs = [x for x in broken_list if x != '']
                log.info("broken_rpmlist: %s" % self.pkgs)
                if not self.pkgs:
                    log.info("There are no broken pkgs in %s" % self.project)
            if "All" == self.pkgs[0] and len(self.pkgs) == 1:
                project_flag = "yes"
                if not self.repository and self.project:
                    cmd = "osc ls %s 2>/dev/null" % self.project
                    pkgs = os.popen(cmd).read().split('\n')
                    self.pkgs = [x for x in pkgs if x != '']
                    log.info("project_rpmlist: %s" % self.pkgs)
                if not self.pkgs:
                    log.info("There are no pkgs in %s" % self.project)
            for pkg in self.pkgs:
                if "\n" in pkg:
                    self.repository = pkg.replace('\n', '')
                else:
                    self.repository = pkg
                sync_result = self._pre_sync_code(self.project)
                if not sync_result:
                    self.sync_failed_rpms.append(self.repository)
            if self.sync_failed_rpms:
                log.error("SYNC ERROR LIST: %s" % ",".join(self.sync_failed_rpms))
                raise SystemExit("Failed, There are some pkgs sync failure")


class CheckCode(object):
    """
    Make sure that the codes for gitee and obs are the same
    """
    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.project = kwargs["project"]
        self.branch = kwargs["branch"]
        cmd = "osc list %s" % self.project
        self.packages = set(os.popen(cmd).read().split("\n")) - set([''])
        self.not_same_packages = []

    def get_gitee_spec(self, branch, package):
        """
        get spec file from gitee repo
        branch: branch of package in gitee
        package: name of package
        """
        log.info("--------------------------------------")
        cmd = "curl https://gitee.com/src-openeuler/{0}/tree/{1} | grep src-openeuler > {2}".format(\
            package, branch, package)
        log.info("%s - %s" % (package, cmd))
        spec_files = None
        ret = os.system(cmd)
        for i in range(3):
            if ret == 0:
                break
            ret = os.system(cmd)
        if ret == 0:
            try:
                cmd = "cat {0}| grep spec".format(package)
                data = os.popen(cmd).read()
                str_find = '<a title=.* href="/src-openeuler/.*">(.*.spec)</a>'
                #str_find = '<a href="/src-openeuler/.*" title=.*>(.*.spec)</a>'
                spec_files = re.findall(str_find, data)
                log.info("%s - %s" % (package, spec_files))
            except SyntaxError as e:
                log.error(e)
        cmd = "rm -rf %s" % package
        os.system(cmd)
        if spec_files:
            for spec_file in spec_files:
                cmd = "wget https://gitee.com/src-openeuler/{0}/raw/{1}/{2} -O {3}".format(\
                    package, branch, spec_file, spec_file)
                log.info("%s - %s" % (package, cmd))
                if os.system(cmd) != 0:
                    os.system(cmd)
            return spec_files
        return None 
       # url = "https://gitee.com/api/v5/repos/src-openeuler/{0}/contents/%2F?ref={1}".format(package, branch)
       # ret = requests.get(url)
       # data = json.dumps(ret.json(), sort_keys=True, indent=4, ensure_ascii=False)
       # str_find = '"download_url": "(.*.spec)",'
       # url = re.findall(str_find, data)[0]
       # spec_file = os.path.basename(url)
       # cmd = "wget %s" % url
       # if os.system(cmd) != 0:
       #     os.system(cmd)
       # return spec_file

    def get_obs_spec(self, project, package):
        """
        get spec file from obs repo
        project:
        package:
        """
        cmd = "osc ls -e %s %s | grep '.spec'" % (project, package)
        data = os.popen(cmd).read()
        str_find = '(.*.spec)'
        spec_files = re.findall(str_find, data)
        log.info("%s - obs spec files: %s" % (package, spec_files))
        if spec_files:
            for spec_file in spec_files:
                cmd = "osc co %s %s %s" % (project, package, spec_file)
                log.info("%s - %s" % (package, cmd))
                if os.system(cmd) != 0:
                    os.system(cmd)
            return spec_files
        return None

    def same_or_not(self, gitee_spec, obs_spec, package):
        """
        check spec file between gitee spec file and obs spec file
        return: False - not same; True - same
        """
        if gitee_spec and obs_spec:
            for ospec in obs_spec:
                sf = ospec.split(":")[-1]
                index = gitee_spec.index(sf)
                log.info("gitee spec:%s, obs spec:%s" % (gitee_spec[index], ospec))
                cmd = "diff %s %s" % (gitee_spec[index], ospec)
                log.info(cmd)
                ret = os.popen(cmd).read()
                cmd = "rm -rf %s %s" % (gitee_spec[index], ospec)
                os.system(cmd)
                if ret:
                    log.info("diff-" + ret)
                    return False
            return True
        elif not gitee_spec and not obs_spec:
            log.info("%s has no script" % package)
            return True
        elif not gitee_spec:
            log.error("%s no spec from gitee" % package)
            return False
        elif not obs_spec:
            log.error("%s no spec from obs" % package)
            return False

    def check(self, package):
        """
        check one package
        """
        gitee_spec = self.get_gitee_spec(self.branch, package)
        obs_spec = self.get_obs_spec(self.project, package)
        if self.same_or_not(gitee_spec, obs_spec, package):
            log.info("codes of %s are same between gitee and obs" % package)
        else:
            self.not_same_packages.append(package)
            log.info("codes of %s are not same between gitee and obs" % package)

    def check_all(self):
        """
        check all packages
        """
        if self.packages:
            pool = threadpool.ThreadPool(30)
            reqs = threadpool.makeRequests(self.check, self.packages)
            for req in reqs:
                pool.putRequest(req)
            pool.wait()
            log.info("codes not same between gitee and obs:%s" % self.not_same_packages)
            self.sync_code()

    def sync_code(self):
        """
        sync not_same_packages code
        """
        if self.not_same_packages:
            log.info("Start synchronization code...")
            self.kwargs['pkglist'] = self.not_same_packages
            sy = SYNCCode(**self.kwargs)
            sy.sync_code_to_obs()


if __name__ == "__main__":
    #Now start
    kw = {'repository': sys.argv[1], 'branch': sys.argv[2],
            'gitee_user': sys.argv[3], 'gitee_pwd': sys.argv[4],
            'obs_meta_path': '/home/python_bash/obs_meta', 'source_server_user': 'root',
            'source_server_ip': '124.90.34.227', 'source_server_pwd': '654321',
            'source_server_port': '11243'}
    sync_run = SYNCCode(**kw)
    #sync_run.sync_code_to_obs()
