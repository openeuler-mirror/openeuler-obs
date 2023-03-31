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
# Create: 2020-10-20
# ******************************************************************************

"""
function for all
"""
import os
import re
import pexpect
import requests
import jenkins
import subprocess
from common.log_obs import log
from requests.auth import HTTPBasicAuth
try:
    from urllib import urlencode
except ImportError:
    from urllib.parse import urlencode


def str_to_bool(s):
    """
    change string to bool
    """
    return s.lower() in ("yes", "true", "t", "1")

def run(cmd, timeout=600, print_out=False):
    """
    run shell cmd
    :param cmd: command
    :param timeout: timeout
    :param print_out: print out or not
    :return: return code, stdout, stderr
    """
    ret = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, encoding="utf-8", timeout=timeout)
    log.info("cmd: {}".format(cmd))
    if ret.stdout and print_out:
        log.info("ret.stdout: {}".format(ret.stdout))
    if ret.stderr:
        log.warning("ret.stderr: {}".format(ret.stderr))
    return ret.returncode, ret.stdout, ret.stderr

def git_repo_src(repo_url, gitee_user_name, gitee_user_pwd, dest_dir=None):
    """
    get repo source
    repo_url: url of repository
    gitee_user_name:
    gitee_user_pwd:
    """
    repos_dir = os.getcwd()
    tmp = repo_url.split("//")
    if dest_dir:
        repo_path = dest_dir
    else:
        repo_path = os.path.join(repos_dir, tmp[1].split("/")[-1].replace(".git", ""))
    for i in range(5):
        if os.path.exists(repo_path) and os.path.isdir(repo_path):
            cmd = "cd %s && git pull && cd -" % repo_path
        else:
            cmd = "rm -rf %s && git clone --depth 1 %s//%s:%s@%s %s" % \
                    (repo_path, tmp[0], gitee_user_name, gitee_user_pwd, tmp[1], repo_path)
        if os.system(cmd) == 0:
            break
    if os.path.exists(repo_path):
        return repo_path
    else:
        return None


class Pexpect(object):
    """
    expect by python
    """
    def __init__(self, user, ip, passwd, port=None):
        """
        init connect message
        user: user for system
        ip: ip of the system
        port: port for connectiong by sshd
        """
        self.user = user
        self.ip = ip
        self.passwd = passwd
        self.port = port

    def _expect(self, process):
        for i in range(5):
            ret=process.expect(["(yes/no)", "Password", "password", pexpect.EOF, \
                    pexpect.exceptions.TIMEOUT], timeout=60)
            if ret == 0:
                process.sendline("yes\n")
            if ret == 1 or ret == 2:
                process.sendline("%s\n" % self.passwd)
                break
            if ret == 3 or ret == 4:
                break

    def ssh_cmd(self, cmd, timeout=600):
        """
        cmd: command will be runnd
        return: response of command
        """
        try:
            if self.port:
                cmd = "ssh -p %s %s@%s '%s'" % (self.port, self.user, self.ip, cmd)
            else:
                cmd = "ssh %s@%s '%s'" % (self.user, self.ip, cmd)
            process = pexpect.spawn(cmd, timeout=timeout)
            self._expect(process)
            msg = process.readlines()
            process.close()
        except pexpect.exceptions.TIMEOUT as e:
            return e
        return msg

    def scp_file(self, src_file, dest_dir):
        """
        src_file:
        dest_dir:
        """
        if self.port:
            cmd = "scp -P %s %s %s@%s:%s" % (self.port, src_file, self.user, self.ip, dest_dir)
        else:
            cmd = "scp %s %s@%s:%s" % (src_file, self.user, self.ip, self.dest_dir)
        process = pexpect.spawn(cmd)
        self._expect(process)
        msg = process.readlines()
        process.close()

        return msg

class Comment(object):
    """
    gitee comments process
    :param owner: 仓库属于哪个组织
    :param repo: 仓库名
    :param token: gitee 账户token
    """

    def __init__(self, owner, repo, token):
        self._owner = owner
        self._repo = repo
        self._token = token


    def comment_pr(self, pr, comment):
        """
        评论pull request
        :param pr: 本仓库PR id
        :param comment: 评论内容
        :return: 0成功，其它失败
        """
        comment_pr_url = "https://gitee.com/api/v5/repos/{}/{}/pulls/{}/comments".format(self._owner, self._repo, pr)
        data = {"access_token": self._token, "body": comment}
        rs = self.do_requests("post", comment_pr_url, body=data, timeout=10)
        if rs == 0:
            return True
        else:
            return False

    def parse_comment_to_table(self, pr, results, tips, details):
        """
        :param pr: 仓库PR id
        :param results: 门禁检查返回结果
        :return: none
        """
        comment_state = {"success":":white_check_mark:", "warning":":bug:", "failed":":x:"}
        comments = ["<table>", "<tr><th colspan=2>Check Item</th> <th>Check Result</th> <th colspan=2>Description</th>"]
        for check_item, check_result in results.items():
            emoji_result = comment_state[check_result]
            word_result = check_result.upper()
            info_str = '''<tr><td colspan=2>{}</td> <td>{}
            <strong>{}</strong></td> <td colspan=2>{}</td>
            '''.format(check_item, emoji_result, word_result, details[check_item])
            comments.append(info_str)
        comments.append("</table>")
        comments.extend(tips)
        self.comment_pr(pr, "\n".join(comments))


    def do_requests(self, method, url, querystring=None, body=None, auth=None, timeout=30, obj=None):
        """
        http request
        :param method: http method
        :param url: http[s] schema
        :param querystring: dict
        :param body: json
        :param auth: dict, basic auth with user and password
        :param timeout: second
        :param obj: callback object, support list/dict/object
        :return:
        """
        if method.lower() not in ["get", "post", "put", "delete"]:
            return -1
        if querystring:
            url = "{}?{}".format(url, urlencode(querystring))
        try:
            func = getattr(requests, method.lower())
            if body:
                if auth:
                    rs = func(url, json=body, timeout=timeout, auth=HTTPBasicAuth(auth["user"], auth["password"]))
                else:
                    rs = func(url, json=body, timeout=timeout)
            else:
                if auth:
                    rs = func(url, timeout=timeout, auth=HTTPBasicAuth(auth["user"], auth["password"]))
                else:
                    rs = func(url, timeout=timeout)
            if rs.status_code not in [requests.codes.ok, requests.codes.created, requests.codes.no_content]:
                return 1
            # return response
            if obj is not None:
                if isinstance(obj, list):
                    obj.extend(rs.json())
                elif isinstance(obj, dict):
                    obj.update(rs.json())
                elif callable(obj):
                    obj(rs)
                elif hasattr(obj, "cb"):
                    getattr(obj, "cb")(rs.json())
            return 0
        except requests.exceptions.SSLError as sslerror:
            return -2
        except requests.exceptions.Timeout as timeouterror:
            return 2
        except requests.exceptions.RequestException as excepterror:
            return 3

class JenkinsProxy(object):
    """
    Jenkins 代理，实现jenkins一些操作
    """

    def __init__(self, base_url, username, token, timeout=10):
        """

        :param base_url:
        :param username: 用户名
        :param token:
        :param timeout:
        """
        self._username = username
        self._token = token
        self._timeout = timeout
        self._jenkins = jenkins.Jenkins(base_url, username=username, password=token, timeout=timeout)

    def get_job_info(self, job_path):
        """
        获取任务信息
        :param job_path: job路径
        :return: None if job_path not exist
        """
        try:
            return self._jenkins.get_job_info(job_path)
        except jenkins.JenkinsException as e:
            return None

    @classmethod
    def get_job_path_from_job_url(cls, job_url):
        """
        从url中解析job路径
        :param job_url: 当前工程url, for example https://domain/job/A/job/B/job/C
        :return: for example, A/B/C
        :2 :代表目录层级
        """
        jenkins_first_level_dir_index = 2
        jenkins_dir_interval_with_level = 2
        job_path = re.sub(r"/$", "", job_url)
        job_path = re.sub(r"http[s]?://", "", job_path)
        sp = job_path.split("/")[jenkins_first_level_dir_index::
                                 jenkins_dir_interval_with_level]
        sp = [item for item in sp if item != ""]
        job_path = "/".join(sp)
        return job_path

    @staticmethod
    def get_job_path_build_no_from_build_url(build_url):
        """
        从url中解析job路径
        :param build_url: 当前构建url, for example https://domain/job/A/job/B/job/C/number/
        :return: for example A/B/C/number
        """
        job_build_no = re.sub(r"/$", "", build_url)
        job_url = os.path.dirname(job_build_no)
        build_no = os.path.basename(job_build_no)
        job_path = JenkinsProxy.get_job_path_from_job_url(job_url)
        return job_path, build_no
