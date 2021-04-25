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
# Create: 2021-04-22
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
from core.project_manager import OBSPrjManager


S = SetEnv()
C = CommonFunc()
repo_path = None
P = None


class TestCase(object):
    def setup_class(self):
        S.set_oscrc()
        S.set_gitee()
        cmd = "osc list | grep home:{0}:test".format(S.obs_info["user"])
        if os.system(cmd) == 0:
            cmd = "osc api -X DELETE /source/home:{0}:test".format(S.obs_info["user"])
        global repo_path
        global P
        repo_path = C.pull_from_gitee_repo(S.gitee_info["user"], S.gitee_info["passwd"], \
                    "https://gitee.com/{0}/obs_meta".format(S.gitee_info["user"]), "master", "obs_meta")
        P = OBSPrjManager(repo_path)

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
        test for creating project for multi-version
        """
        assert os.path.exists(repo_path), "{0} not exist".format(repo_path)
        file_msg = """
<project name=\\"home:{0}:test\\">
  <title/>
  <description/>
  <person userid=\\"{1}\\" role=\\"maintainer\\"/>
</project>
        """.format(S.obs_info["user"], S.obs_info["user"])

        cmd = "cd {0} && mkdir -p OBS_PRJ_meta/multi-version/test && echo \"{1}\" > \
               OBS_PRJ_meta/multi-version/test/home:{2}:test".format(repo_path, file_msg, S.obs_info["user"])
        if os.system(cmd) == 0:
            assert True
        else:
            assert False, "fail to exec cmd:{0}".format(cmd)
        C.commit_to_gitee_repo(repo_path, "OBS_PRJ_meta/multi-version/test/home:{0}:test".format(S.obs_info["user"]))  
        P.manager_action()
        project_dir = os.path.join(repo_path, "multi-version", "test", "home:{0}:test".format(S.obs_info["user"]))
        assert os.path.exists(project_dir), "{0} not exist".format(project_dir)
        cmd = "osc list | grep home:{0}:test".format(S.obs_info["user"])
        ret = os.popen(cmd).read()
        if ret:
            assert True
        else:
            assert False, "fail to create project on OBS system"

    def test_2(self):
        """
        test for changing project meta
        """
        cmd = "sed -i 's/<title\/>/<title>miao_test<\/title>/g' OBS_PRJ_meta/multi-version/test/home:{0}:test".format(\
               S.obs_info["user"])
        if os.system(cmd) == 0:
            assert True
        else:
            assert False, "fail to exec cmd:{0}".format(cmd)
        C.commit_to_gitee_repo(repo_path, "OBS_PRJ_meta/multi-version/test/home:{0}:test".format(S.obs_info["user"]))  
        P.manager_action()
        cmd = "osc api -X GET /source/home:{0}:test/_meta".format(S.obs_info["user"])
        print(cmd)
        ret = os.popen(cmd).read()
        print(ret)
        if "miao_test" in ret:
            assert True
        else:
            assert False, "fail to change project meta info" 
        
    def test_3(self):
        """
        test for deleting project
        """ 
        cmd = "cd {0} && git rm -f OBS_PRJ_meta/multi-version/test/home:{1}:test && git commit -m delete".format(\
              repo_path, S.obs_info["user"])
        if os.system(cmd) == 0:
            assert True
        else:
            assert False, "fail to delete project meta file from {0}".format(repo_path)
        P.manager_action()
        cmd = "osc list | grep home:{0}:test".format(S.obs_info["user"])
        ret = os.popen(cmd).read()
        print(ret)
        if ret:
            assert False, "fail to delete project"
        else:
            assert True
        
    def test_4(self):
        """
        test for creating normal project 
        """
        assert os.path.exists(repo_path), "{0} not exist".format(repo_path)
        file_msg = """
<project name=\\"home:{0}:test\\">
  <title/>
  <description/>
  <person userid=\\"{1}\\" role=\\"maintainer\\"/>
</project>
        """.format(S.obs_info["user"], S.obs_info["user"])
        cmd = "cd {0} && mkdir -p OBS_PRJ_meta/test && echo \"{1}\" > OBS_PRJ_meta/test/home:{2}:test".format(\
              repo_path, file_msg, S.obs_info["user"])
        if os.system(cmd) == 0:
            assert True
        else:
            assert False, "fail to exec cmd:{0}".format(cmd)
        C.commit_to_gitee_repo(repo_path, "OBS_PRJ_meta/test/home:{0}:test".format(S.obs_info["user"]))
        P.manager_action()
        project_dir = os.path.join(repo_path, "test", "home:{0}:test".format(S.obs_info["user"]))
        assert os.path.exists(project_dir), "{0} not exist".format(project_dir)
        cmd = "osc list | grep home:{0}:test".format(S.obs_info["user"])
        ret = os.popen(cmd).read()
        print(ret)
        if ret:
            assert True
        else:
            assert False, "fail to create project on OBS system"

    def test_5(self):
        """
        test for changing normal project meta
        """
        cmd = "sed -i 's/<title\/>/<title>miao_test<\/title>/g' OBS_PRJ_meta/test/home:{0}:test".format(\
              S.obs_info["user"])
        if os.system(cmd) == 0:
            assert True
        else:
            assert False, "fail to exec cmd:{0}".format(cmd)
        C.commit_to_gitee_repo(repo_path, "OBS_PRJ_meta/test/home:{0}:test".format(S.obs_info["user"]))  
        P.manager_action()
        cmd = "osc api -X GET /source/home:{0}:test/_meta".format(S.obs_info["user"])
        print(cmd)
        ret = os.popen(cmd).read()
        print(ret)
        if "miao_test" in ret:
            assert True
        else:
            assert False, "fail to change project meta info" 
        
    def test_6(self):
        """
        test for deleting nomal project
        """ 
        cmd = "cd {0} && git rm -f OBS_PRJ_meta/test/home:{1}:test && git commit -m delete".format(\
              repo_path, S.obs_info["user"])
        if os.system(cmd) == 0:
            assert True
        else:
            assert False, "fail to delete project meta file from {0}".format(repo_path)
        P.manager_action()
        cmd = "osc list | grep home:{0}:test".format(S.obs_info["user"])
        ret = os.popen(cmd).read()
        print(ret)
        if ret:
            assert False, "fail to delete project"
        else:
            assert True
        
