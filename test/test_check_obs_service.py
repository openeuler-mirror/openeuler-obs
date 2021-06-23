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
# Create: 2021-06-15
# *****************************************************************************
"""
test all: python3 -m pytest -s test_check_obs_service.py
test one class: python3 -m pytest -s test_check_obs_service.py::TestCase
test one class one case: python3 -m pytest -s test_check_obs_service.py::TestCase::test_1
"""
import os
import sys
import pytest
current_path = os.path.join(os.path.split(os.path.realpath(__file__))[0])
sys.path.append(os.path.join(current_path, ".."))
from func import SetEnv, CommonFunc
from common.common import Pexpect
from core.check_meta_service import CheckMetaPull
S = SetEnv()
C = CommonFunc()
token = S.get_token()

def verify_obs_meta(cmd_str):
    """
    make the commit to obs_meta for make check enironment
    """
    rm_rel = os.system("rm -rf ./obs_meta")
    repo_path = C.pull_from_gitee_repo(S.gitee_info["user"], S.gitee_info["passwd"], \
            "https://gitee.com/{0}/obs_meta".format(S.gitee_info["user"]), "master", "obs_meta")
    commit_cmd = "cd obs_meta  && git add -A && git commit -m 'test' && cd -"
    cmd_resul = os.system(cmd_str)
    commit_cmd = os.system(commit_cmd)
    if cmd_resul != 0 and commit_cmd != 0:
        return False
    else:
        return True

class TestCase(object):
    def setup_class(self):
        S.set_oscrc()
        S.set_gitee()

    def teardown_class(self):
        S.unset_oscrc()
        S.unset_gitee()
    
    def test_1(self):
        """
        test obs_meta commit for modifiy service : Service Correct
        """
        name_path = "obs_meta/master/openEuler:Factory"
        old_path = "obs_meta/master/openEuler:Mainline"
        cp_cmd = "mv %s/libcyaml %s/libcyaml" % (name_path, old_path)
        verfiy_meta = verify_obs_meta(cp_cmd)
        if not verfiy_meta:
            assert False
        kw = {
                "branch": "",
                "pr_id": "test",
                "access_token": token,
                "obs_meta_path": "./obs_meta"
                }
        check1 = CheckMetaPull(**kw)
        try:
            check1.do_all()
        except SystemExit:
            assert False
        else:
            assert True

    def test_2(self):
        """
        test error service for given branch : Branch have no wrong service
        """
        kw = {
                "branch": "openEuler-20.03-LTS",
                "pr_id": "",
                "access_token": "",
                "obs_meta_path": ""
                }
        check2 = CheckMetaPull(**kw)
        try:
            check2.do_all()
        except SystemExit:
            assert False
        else:
            assert True

    def test_3(self):
        """
        test the meta file commit for obs_meta : The meta file have a correct format
        """
        kw = {
                "branch": "",
                "pr_id": "698",
                "access_token": token,
                "obs_meta_path": ""
                }
        check3 = CheckMetaPull(**kw)
        try:
            check3.do_all()
        except SystemExit:
            assert False
        else:
            assert True

    def test_4(self):
        """
        test obs_meta commit for modifiy service : Service Error 
        """
        kw = {
                "branch": "",
                "pr_id": "744",
                "access_token": token,
                "obs_meta_path": ""
                }
        check4 = CheckMetaPull(**kw)
        try:
            check4.do_all()
        except SystemExit:
            assert True
        else:
            assert False

    def test_5(self):
        """
        test obs_meta commit for meta file : The meta file have a wrong format
        """
        name_path = "obs_meta/OBS_PRJ_meta/openEuler-20.03-LTS/openEuler:20.03:LTS:Epol"
        mv_cmd = "sed -i '1d' %s" % name_path
        verfiy_meta = verify_obs_meta(mv_cmd)
        if not verfiy_meta:
            assert False
        kw = {
                "branch": "",
                "pr_id": "***",
                "access_token": token,
                "obs_meta_path": "./obs_meta"
                }
        check4 = CheckMetaPull(**kw)
        try:
            check4.do_all()
        except SystemExit:
            assert True
        else:
            assert False

    def test_6(self):
        """
        test error service for given branch : Branch have wrong service
        """
        kw = {
                "branch": "openEuler-20.03-LTS-SP1",
                "pr_id": "",
                "access_token": "",
                "obs_meta_path": ""
                }
        check2 = CheckMetaPull(**kw)
        try:
            check2.do_all()
        except SystemExit:
            assert True
        else:
            assert False

    def test_7(self):
        """
        test the protect branch: not in protect branch
        """
        kw = {
                "branch": "",
                "pr_id": "763",
                "access_token": token,
                "obs_meta_path": ""
                }
        check2 = CheckMetaPull(**kw)
        try:
            check2.do_all()
        except SystemExit:
            assert False
        else:
            assert True

    def test_8(self):
        """
        test the pkg name in service: service have wrong name
        """
        name_path = "obs_meta/master/openEuler:Mainline"
        mv_cmd = "mv %s/gcc %s/gdd" % (name_path, name_path)
        verfiy_meta = verify_obs_meta(mv_cmd)
        if not verfiy_meta:
            assert False
        kw = {
                "branch": "",
                "pr_id": "test",
                "access_token": token,
                "obs_meta_path": "./obs_meta"
                }
        check8 = CheckMetaPull(**kw)
        try:
            check8.do_all()
        except SystemExit:
            assert True
        else:
            assert False

    def test_9(self):
        """
        test error : pkg in branch have different project
        """
        name_path = "obs_meta/master/openEuler:Factory"
        old_path = "obs_meta/master/openEuler:Mainline"
        cp_cmd = "cp %s/gcc %s/gcc -rf" % (old_path, name_path)
        verfiy_meta = verify_obs_meta(cp_cmd)
        if not verfiy_meta:
            assert False
        kw = {
                "branch": "",
                "pr_id": "test",
                "access_token": token,
                "obs_meta_path": "./obs_meta"
                }
        check9 = CheckMetaPull(**kw)
        try:
            check9.do_all()
        except SystemExit:
            assert True
        else:
            assert False

    def test_10(self):
        """
        test error : The key word for next in service url spelling mistakes
        """
        old_path = "obs_meta/master/openEuler:Mainline"
        sed_cmd = "sed -i 's/next/Next/g' %s/gcc/_service" % old_path
        verfiy_meta = verify_obs_meta(sed_cmd)
        if not verfiy_meta:
            assert False
        kw = {
                "branch": "",
                "pr_id": "test",
                "access_token": token,
                "obs_meta_path": "./obs_meta"
                }
        check9 = CheckMetaPull(**kw)
        try:
            check9.do_all()
        except SystemExit:
            assert True
        else:
            assert False
