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
# Author: yaokai13
# Create: 2021-04-27
# ******************************************************************************
"""
test all: python3 -m pytest -s test_project.py
test one class: python3 -m pytest -s test_project.py::TestCase
test one class one case: python3 -m pytest -s test_project.py::TestCase::test_1
"""
import os
import sys
import pytest
current_path = os.path.join(os.path.split(os.path.realpath(__file__))[0])
sys.path.append(os.path.join(current_path, ".."))
from func import SetEnv, CommonFunc
from core.gitee_to_obs import SYNCCode
from common.common import Pexpect

S = SetEnv()
C = CommonFunc()
repo_path = None
P = None
source_path = "/srv/cache/obs/tar_scm/repo/next/"
scmd = Pexpect("root","127.0.0.1","112233","2222")

class TestCase(object):
    def setup_class(self):
        S.set_oscrc()
        S.set_gitee()
        global repo_path
        repo_path = C.pull_from_gitee_repo(S.gitee_info["user"], S.gitee_info["passwd"], \
                    "https://gitee.com/{0}/obs_meta".format(S.gitee_info["user"]), "master", "obs_meta")

    def teardown_class(self):
        S.unset_oscrc()
        S.unset_gitee()
        cmd = "rm -rf %s" % repo_path
        if os.system(cmd) == 0:
            assert True
        else:
            assert False, "fail to clear {0} after testing".format(repo_path)
    
    def test_1(self):
        """
        test for sync all the pkg in obs_project
        """
        assert os.path.exists(repo_path), "{0} not exist".format(repo_path)
        kw = {
                "branch": "***",
                "gitee_user": "***",
                "gitee_pwd": "***",
                "obs_meta_path": repo_path,
                "project": "***",
                "source_server_user": "***",
                "source_server_ip": "***",
                "source_server_pwd": "***",
                "source_server_port": "***",
                "repository":"",
                "pkglist":""
                }
        check1 = SYNCCode(**kw)
        check1.sync_code_to_obs()
        cmd = "osc ls %s" % kw['project']
        pkgs = os.popen(cmd).readlines()
        print(pkgs)
        for pkg in pkgs:
            if kw['branch'] == "master":
                my_cmd = "ls %s | grep %s" % (os.path.join(source_path,"openEuler"), pkg.replace('\n', ''))
                if pkg.replace('\n', '') != scmd.ssh_cmd(my_cmd)[1].strip().decode('utf-8'):
                    assert False,  "{0} sync fail".format(pkg.replace('\n', ''))
            elif "Multi-Version" in kw['branch']:
                my_cmd = "ls %s | grep %s" % (os.path.join(source_path,"multi_version",kw['branch']), pkg.replace('\n', ''))
                if pkg.replace('\n', '') != scmd.ssh_cmd(my_cmd)[1].strip().decode('utf-8'):
                    assert False,  "{0} sync fail".format(pkg.replace('\n', ''))
            else:
                my_cmd = "ls %s | grep %s" % (os.path.join(source_path,kw['branch']), pkg.replace('\n', ''))
                if pkg.replace('\n', '') != scmd.ssh_cmd(my_cmd)[1].strip().decode('utf-8'):
                    assert False,  "{0} sync fail".format(pkg.replace('\n', ''))


    def test_2(self):
        """
        test for sync one pkg
        """
        assert os.path.exists(repo_path), "{0} not exist".format(repo_path)
        kw = {
                "branch": "***",
                "gitee_user": "***",
                "gitee_pwd": "***",
                "obs_meta_path": repo_path,
                "repository": "***",
                "source_server_user": "***",
                "source_server_ip": "***",
                "source_server_pwd": "***",
                "source_server_port": "***",
                "pkglist":"",
                "project":""
                }
        check2 = SYNCCode(**kw)
        check2.sync_code_to_obs()
        if kw['branch'] == "master":
            my_cmd = "ls %s | grep %s" % (os.path.join(source_path,"openEuler"), kw['repository'])
            if kw['repository'] != scmd.ssh_cmd(my_cmd)[1].strip().decode('utf-8'):
                assert False,  "{0} sync fail".format(kw['repository'])
        elif "Multi-Version" in kw['branch']:
            my_cmd = "ls %s | grep %s" % (os.path.join(source_path,"multi_version",kw['branch']), kw['repository'])
            if kw['repository'] != scmd.ssh_cmd(my_cmd)[1].strip().decode('utf-8'):
                assert False,  "{0} sync fail".format(kw['repository'])
        else:
            my_cmd = "ls %s | grep %s" % (os.path.join(source_path,kw['branch']), kw['repository'])
            if kw['repository'] != scmd.ssh_cmd(my_cmd)[1].strip().decode('utf-8'):
                assert False,  "{0} sync fail".format(kw['repository'])

    def test_3(self):
        """
        Have the project name help you more fast to sync
        """ 
        assert os.path.exists(repo_path), "{0} not exist".format(repo_path)
        kw = {
                "branch": "***",
                "gitee_user": "***",
                "gitee_pwd": "***",
                "obs_meta_path": repo_path,
                "repository": "***",
                "source_server_user": "***",
                "source_server_ip": "***",
                "source_server_pwd": "***",
                "source_server_port": "***",
                "pkglist":"",
                "project":"***"
                }
        check3 = SYNCCode(**kw)
        check3.sync_code_to_obs()
        if kw['branch'] == "master":
            my_cmd = "ls %s | grep %s" % (os.path.join(source_path,"openEuler"), kw['repository'])
            if kw['repository'] != scmd.ssh_cmd(my_cmd)[1].strip().decode('utf-8'):
                assert False,  "{0} sync fail".format(kw['repository'])
        elif "Multi-Version" in kw['branch']:
            my_cmd = "ls %s | grep %s" % (os.path.join(source_path,"multi_version",kw['branch']), kw['repository'])
            if kw['repository'] != scmd.ssh_cmd(my_cmd)[1].strip().decode('utf-8'):
                assert False,  "{0} sync fail".format(kw['repository'])
        else:
            my_cmd = "ls %s | grep %s" % (os.path.join(source_path,kw['branch']), kw['repository'])
            if kw['repository'] != scmd.ssh_cmd(my_cmd)[1].strip().decode('utf-8'):
                assert False,  "{0} sync fail".format(kw['repository'])

 
    def test_4(self):
        """
        use the pkglist help you can sync not only one pkg at the same time
        """
        assert os.path.exists(repo_path), "{0} not exist".format(repo_path)
        kw = {
               "branch": "***",
                "gitee_user": "***",
                "gitee_pwd": "***",
                "obs_meta_path": repo_path,
                "repository": "",
                "source_server_user": "***",
                "source_server_ip": "***",
                "source_server_pwd": "***",
                "source_server_port": "***",
                "pkglist": ["***", "***"],
                "project": "***"
                }
        check4 = SYNCCode(**kw)
        check4.sync_code_to_obs()
        for pkg in kw['pkglist']:
            if kw['branch'] == "master":
                my_cmd = "ls %s | grep %s" % (os.path.join(source_path,"openEuler"), pkg.replace('\n', ''))
                if pkg.replace('\n', '') != scmd.ssh_cmd(my_cmd)[1].strip().decode('utf-8'):
                    assert False,  "{0} sync fail".format(pkg.replace('\n', ''))
            elif "Multi-Version" in kw['branch']:
                my_cmd = "ls %s | grep %s" % (os.path.join(source_path,"multi_version",kw['branch']), pkg.replace('\n', ''))
                if pkg.replace('\n', '') != scmd.ssh_cmd(my_cmd)[1].strip().decode('utf-8'):
                    assert False,  "{0} sync fail".format(pkg.replace('\n', ''))
            else:
                my_cmd = "ls %s | grep %s" % (os.path.join(source_path,kw['branch']), pkg.replace('\n', ''))
                if pkg.replace('\n', '') != scmd.ssh_cmd(my_cmd)[1].strip().decode('utf-8'):
                    assert False,  "{0} sync fail".format(pkg.replace('\n', ''))
