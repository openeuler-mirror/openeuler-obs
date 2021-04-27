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
# Author: wangchong
# Create: 2021-04-23
# ******************************************************************************
"""
test all: python3 -m pytest -s test_package.py
test one class: python3 -m pytest -s test_package.py::TestCase
test one class one case: python3 -m pytest -s test_package.py::TestCase::test_1
"""
import os
import sys
import pytest
current_path = os.path.join(os.path.split(os.path.realpath(__file__))[0])
sys.path.append(os.path.join(current_path, ".."))
from func import SetEnv, CommonFunc
from core.package_manager import OBSPkgManager


S = SetEnv()
C = CommonFunc()
obs_meta_path = None
P = None


class TestCase(object):
    def setup_class(self):
        S.set_oscrc()
        S.set_gitee()
        global obs_meta_path
        global P
        obs_meta_path = C.pull_from_gitee_repo(S.gitee_info["user"], S.gitee_info["passwd"], \
                "https://gitee.com/{0}/obs_meta".format(S.gitee_info["user"]), "master", "obs_meta")
        kw = {"obs_meta_path": obs_meta_path,
                "gitee_user": S.gitee_info["user"],
                "gitee_pwd": S.gitee_info["passwd"],
                "sync_code": False,
                "branch2": "", "project2": "",
                "check_yaml": "", "check_meta": "",
                }
        P = OBSPkgManager(**kw)
        for i in range(1, 3):
            cmd = "osc list | grep home:{0}:test{1}".format(S.obs_info["user"], i)
            if os.system(cmd) == 0:
                cmd = "osc api -X DELETE /source/home:{0}:test{1}".format(S.obs_info["user"], i)
                ret = os.system(cmd)
            file_msg = """
<project name=\\"home:{0}:test{1}\\">
  <title/>
  <description/>
  <person userid=\\"{2}\\" role=\\"maintainer\\"/>
</project>
            """.format(S.obs_info["user"], i, S.obs_info["user"])
            cmd = "echo \"{0}\" > {1}/_meta_test".format(file_msg, obs_meta_path)
            if os.system(cmd) == 0:
                assert True
            else:
                assert False, "fail to exec cmd:{0}".format(cmd)
            cmd = "osc api -X PUT /source/home:{0}:test{1}/_meta -T {2}/_meta_test".format(S.obs_info["user"], \
                    i, obs_meta_path)
            if os.system(cmd) == 0:
                assert True
            else:
                assert False, "fail to exec cmd:{0}".format(cmd)
            cmd = "cd {0} && mkdir -p multi-version/test-rock/home:{1}:test{2}".format(obs_meta_path, S.obs_info["user"], i)
            if os.system(cmd) == 0:
                assert True
            else:
                assert False, "fail to exec cmd:{0}".format(cmd)
            C.commit_to_gitee_repo(obs_meta_path, "multi-version/test-rock/home:{0}:test{1}".format(S.obs_info["user"], i))

    def teardown_class(self):
        S.unset_oscrc()
        S.unset_gitee()
        for i in range(1, 3):
            cmd = "osc api -X DELETE /source/home:{0}:test{1}".format(S.obs_info["user"], i)
            if os.system(cmd) == 0:
                assert True
            else:
                assert False, "fail to delete home:{0}:test{1} after testing".format(S.obs_info["user"], i)
        cmd = "rm -fr {0}".format(obs_meta_path)
        if os.system(cmd) == 0:
            assert True
        else:
            assert False, "fail to exec cmd:{0}".format(cmd)

    def test_1(self):
        """
        test for creating package for multi-version
        """
        assert os.path.exists(obs_meta_path), "{0} not exist".format(obs_meta_path)
        for i in range(1, 3):
            file_msg = """
<services>
    <service name=\\"tar_scm_kernel_repo\\">
      <param name=\\"scm\\">repo</param>
      <param name=\\"url\\">next/multi-version/test-rock/mytest{0}</param>
    </service>
</services>
            """.format(i)
            prj_path = os.path.join(obs_meta_path, "multi-version/test-rock/home:{0}:test{1}".format(S.obs_info["user"], i))
            cmd = "cd {0} && mkdir mytest{1} && echo \"{2}\" > mytest{3}/_service".format(prj_path, i, file_msg, i)
            if os.system(cmd) == 0:
                assert True
            else:
                assert False, "fail to exec cmd:{0}".format(cmd)
        C.commit_to_gitee_repo(obs_meta_path, \
                "multi-version/test-rock/home:{0}:test1/mytest1/_service".format(S.obs_info["user"]), \
                "multi-version/test-rock/home:{0}:test2/mytest2/_service".format(S.obs_info["user"]))
        P.obs_pkg_admc()
        for i in range(1, 3):
            cmd = "osc list home:{0}:test{1} mytest{2} _service".format(S.obs_info["user"], i, i)
            if os.system(cmd) == 0:
                assert True
            else:
                assert False, "fail to create package mytest{0} in project home:{1}:test{2}".format(i, S.obs_info["user"], i)
    
    def test_2(self):
        """
        test for modify package _service for multi-version
        """
        assert os.path.exists(obs_meta_path), "{0} not exist".format(obs_meta_path)
        cmd = "cd {0} && sed -i 's/mytest1/mytest1-new/g' \
                multi-version/test-rock/home:{1}:test1/mytest1/_service".format(obs_meta_path, S.obs_info["user"])
        if os.system(cmd) == 0:
            assert True
        else:
            assert False, "fail to exec cmd:{0}".format(cmd)
        C.commit_to_gitee_repo(obs_meta_path, "multi-version/test-rock/home:{0}:test1/mytest1/_service".format(S.obs_info["user"]))
        P.obs_pkg_admc()
        cmd = "osc api -X GET /source/home:{0}:test1/mytest1/_service".format(S.obs_info["user"])
        ret = os.popen(cmd).read()
        if "mytest1-new" in ret:
            assert True
        else:
            assert False, "fail to modify package _service"

    def test_3(self):
        """
        test for change package project for multi-version
        """
        assert os.path.exists(obs_meta_path), "{0} not exist".format(obs_meta_path)
        cmd = "cd {0} && mv multi-version/test-rock/home:{1}:test1/mytest1 \
                multi-version/test-rock/home:{2}:test2/".format(obs_meta_path, S.obs_info["user"], S.obs_info["user"])
        if os.system(cmd) == 0:
            assert True
        else:
            assert False, "fail to exec cmd:{0}".format(cmd)
        C.commit_to_gitee_repo(obs_meta_path, \
                "multi-version/test-rock/home:{0}:test1/mytest1".format(S.obs_info["user"]), \
                "multi-version/test-rock/home:{0}:test2/mytest1".format(S.obs_info["user"]))
        P.obs_pkg_admc()
        cmd = "osc list home:{0}:test1 | grep ^mytest1$".format(S.obs_info["user"])
        ret1 = os.popen(cmd).read()
        cmd = "osc list home:{0}:test2 | grep ^mytest1$".format(S.obs_info["user"])
        ret2 = os.popen(cmd).read()
        if "mytest1" not in ret1 and "mytest1" in ret2:
            assert True
        else:
            assert False, "fail to change package project"

    def test_4(self):
        """
        test for delete package _service for multi-version
        """
        assert os.path.exists(obs_meta_path), "{0} not exist".format(obs_meta_path)
        cmd = "cd {0} && rm -f multi-version/test-rock/home:{1}:test2/mytest1/_service".format(
                obs_meta_path, S.obs_info["user"])
        if os.system(cmd) == 0:
            assert True
        else:
            assert False, "fail to exec cmd:{0}".format(cmd)
        C.commit_to_gitee_repo(obs_meta_path, \
                "multi-version/test-rock/home:{0}:test2/mytest1/_service".format(S.obs_info["user"]))
        P.obs_pkg_admc()
        cmd = "osc api -X GET /source/home:{0}:test2/mytest1/_service".format(S.obs_info["user"])
        if os.system(cmd) != 0:
            assert True
        else:
            assert False, "fail to delete package _service"

    def test_5(self):
        """
        test for delete package for multi-version
        """
        assert os.path.exists(obs_meta_path), "{0} not exist".format(obs_meta_path)
        cmd = "cd {0} && rm -rf multi-version/test-rock/home:{1}:test2/mytest1".format(
                obs_meta_path, S.obs_info["user"])
        if os.system(cmd) == 0:
            assert True
        else:
            assert False, "fail to exec cmd:{0}".format(cmd)
        C.commit_to_gitee_repo(obs_meta_path, \
                "multi-version/test-rock/home:{0}:test2/mytest1".format(S.obs_info["user"]))
        P.obs_pkg_admc()
        cmd = "osc list home:{0}:test2 | grep mytest1".format(S.obs_info["user"])
        if os.system(cmd) != 0:
            assert True
        else:
            assert False, "fail to delete package"
