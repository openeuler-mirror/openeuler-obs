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

work_path = "/srv/cache/obs/tar_scm/repo/next/"

class SYNCCode(object):
    """
    if the rpm package has changed in gitee what you should donext
    (Synchronize the latest code to OBS)
    """
    def __init__(self, rpm_name, gitee_branch, giteeuser, giteeuserpwd, cmd):
        """
        rpm_name: The package you want sync it to obs
        gitee_branch: The branch for you commit in gitee
        giteeuser: The gitee account
        giteeuserpwd: The gitee passwd
        cmd : The object you create for ssh_cmd
        """
        self.rpm_name = rpm_name
        self.gitee_branch= gitee_branch
        self.cmd = cmd
        self.giteeuser = giteeuser
        self.giteeuserpwd = giteeuserpwd

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
        download_path = "/srv/cache/obs/tar_scm/repo/next/obs_meta"
        self._git_clone("obs_meta", "master", download_path)
        ss_cmd = "find %s/%s -name %s " % (download_path, self.gitee_branch,
                self.rpm_name)
        obs_project = str(self.cmd.ssh_cmd(ss_cmd)[1]).split('/')[9]
        if obs_project:
            log.info("The %s obs_project for gitee_%s is <<<<%s>>>>" % (
                self.rpm_name, self.gitee_branch, obs_project))
            self.cmd.ssh_cmd("rm -rf %s" % (download_path))
            return obs_project
        else:
            self.cmd.ssh_cmd("rm -rf %s" % (download_path))
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
        if self.rpm_name == "CreateImage":
            sys.exit("The rpm packages does not need to be sync!!!")
        elif self.rpm_name == "kernel":
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
            rpm_path = source_path + '/' + self.rpm_name
            self._git_clone(self.rpm_name, self.gitee_branch, rpm_path)

    def _gitee_pr_to_obs(self, obs_pro):
        """
        obs_pro:The obs project that gitee branch corresponds
        """
        osc_service = self.cmd.ssh_cmd("osc service remoterun %s %s" % (obs_pro, self.rpm_name))
        for results in osc_service:
            if "ok" in str(results.strip()):
                log.info(str(results.strip()))
                log.info("Success for osc service remoterun the %s" % self.rpm_name)
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
    #Now star
    sshcmd = Pexpect("root", "124.90.34.227", "654321", port=11243)
    sync_run = SYNCCode(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sshcmd)
    sync_run.sync_code_to_obs()
