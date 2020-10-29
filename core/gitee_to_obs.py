#!/bin/evn python3

"""
created by :yaokai
date: 2020-10-26
"""
import sys
import os
import git
import shutil
from common.log_obs import log
from common.common import Pexpect

class SYNCCode(object):
    """
    if the rpm package has changed in gitee what you should donext
    (Synchronize the latest code to OBS)
    """
    def __init__(self, kargs):
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
        self.kargs = kargs
        self.repository = self.kargs['repository']
        self.gitee_branch = self.kargs['gitee_branch']
        self.giteeuser = self.kargs['giteeuser']
        self.giteeuserpwd = self.kargs['giteeuserpwd']
        self.meta_path = self.kargs['meta_path']
        self.cmd = Pexpect(self.kargs['obs_server_user'], 
                self.kargs['obs_server_ip'],
                self.kargs['obs_server_passwd'],
                self.kargs['obs_server_port'])

    def _git_clone(self, rpm_dir, gitee_branch, path):
        """
        rpm_dir: The name for git repository "it will exist under the current directory"
        rpm_branch: The branch you want to checkout for this git repository
        """
        log.info("Git clone the %s in %s" % (rpm_dir, gitee_branch))
        self.cmd.ssh_cmd("rm -rf %s " % (path))
        repo_url = "https://%s:%s@gitee.com/src-openEuler/%s" % (self.giteeuser, self.giteeuserpwd, rpm_dir)
        clone_result = self.cmd.ssh_cmd("git lfs clone --depth=1 %s -b %s %s"
                % (repo_url, gitee_branch, path), 60)
        log.info("At now %s the branch is in %s" % (rpm_dir, gitee_branch))

    def _get_obs_project(self):
        """
        Get the obs project from gitee_branch
        """
        log.info("Start get the obs_project")
        os.chdir("%s/%s" % (self.meta_path, self.gitee_branch))
        cmd = "find ./ -name %s | awk -F '/' '{print $2}'" % self.repository
        obs_project = os.popen(cmd).readlines()[0].replace('\n', '')
        if obs_project:
            log.info("The %s obs_project for gitee_%s is <<<<%s>>>>" % (
                self.repository, self.gitee_branch, obs_project))
            return obs_project
        else:
            sys.exit("Failed !!! The rpm is not exist in %s branch !!!"
                    % self.gitee_branch)

    def _get_latest_gitee_pull(self):
        """
        make the obs server code be the latest
        """
        if self.gitee_branch == "master":
            source_path = "/srv/cache/obs/tar_scm/repo/next/openEuler"
        else:
            source_path = "/srv/cache/obs/tar_scm/repo/next/" + self.gitee_branch
        if self.repository == "CreateImage":
            sys.exit("The rpm packages does not need to be sync!!!")
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
            self.cmd.ssh_cmd("rm -rf %s" % open_kernel_path)
            self.cmd.ssh_cmd("git lfs clone --depth=1 %s -b %s %s" % (open_kernel_git, 
                kernel_tags, open_kernel_path), 120)
        else:
            rpm_path = source_path + '/' + self.repository
            self._git_clone(self.repository, self.gitee_branch, rpm_path)

    def _gitee_pr_to_obs(self, obs_pro):
        """
        obs_pro:The obs project that gitee branch corresponds
        """
        osc_service = self.cmd.ssh_cmd("osc service remoterun %s %s" % (obs_pro, self.repository))
        for results in osc_service:
            if "ok" in str(results.strip()):
                log.info(str(results.strip()))
                log.info("Success for osc service remoterun the %s" % self.repository)
                break
            else:
                continue
            sys.exit("Failed !!! fail to service remoterun !!!")

    def sync_code_to_obs(self):
        """
        The only way to offer that make all fuction runing
        """
        obs_project = self._get_obs_project()
        self._get_latest_gitee_pull()
        self._gitee_pr_to_obs(obs_project)

if __name__ == "__main__":
    #Now start
    kwargs = {'repository': sys.argv[1], 'gitee_branch': sys.argv[2], 
            'giteeuser': sys.argv[3], 'giteeuserpwd': sys.argv[4], 
            'meta_path': '/home/python_bash/obs_meta', 'obs_server_user': 'root',
            'obs_server_ip': '124.90.34.227', 'obs_server_passwd': '654321',
            'obs_server_port': '11243'}
    sync_run = SYNCCode(kwargs)
    sync_run.sync_code_to_obs()