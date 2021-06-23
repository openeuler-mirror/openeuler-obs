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
# Create: 2021-06-15
# ******************************************************************************
"""
test all: python3 -m pytest -s test_pckg_mgmt.py
test one class: python3 -m pytest -s test_pckg_mgmt.py::TestCase
test one class one case: python3 -m pytest -s test_pckg_mgmt.py::TestCase::test_1
"""
import os
import sys
import yaml
import pytest
current_path = os.path.join(os.path.split(os.path.realpath(__file__))[0])
sys.path.append(os.path.join(current_path, ".."))
from func import SetEnv, CommonFunc
from core.sync_pckg_mgmt import SyncPckgMgmt


S = SetEnv()
C = CommonFunc()
obs_meta_path = None
release_management_path = None
P = None

def verify_result(yaml_path, meta_path, status):
    with open(yaml_path, "r", encoding='utf-8') as f:
        file_msg = yaml.load(f, Loader=yaml.FullLoader)
    for title in file_msg['packages']:
        for msg in file_msg['packages'][title]:
            prj_meta_path = os.path.join(meta_path, "OBS_PRJ_meta", msg['branch_to'], msg['obs_to'])
            prj_path = os.path.join(meta_path, msg['branch_to'], msg['obs_to'])
            pkg_path = os.path.join(meta_path, msg['branch_to'], msg['obs_to'], msg['name'], "_service")
            if status == -2:
                if not os.path.exists(prj_meta_path):
                    assert True
                else:
                    assert False, "%s meta file is exist" % msg['obs_to']
            else:
                if os.path.exists(prj_meta_path):
                    assert True
                else:
                    assert False, "%s meta file is not exist" % msg['obs_to']
                if title == "delete":
                    if not os.path.exists(pkg_path):
                        assert True
                    else:
                        assert False, "%s is exist, it's in delete" % pkg_path
                else:
                    if os.path.exists(pkg_path):
                        assert True
                    else:
                        assert False, "%s is not exist" % pkg_path

class TestCase(object):
    def setup_class(self):
        S.set_gitee()
        global obs_meta_path
        global release_management_path
        global P
        release_management_path = C.pull_from_gitee_repo(S.gitee_info["user"], S.gitee_info["passwd"], \
                "https://gitee.com/{0}/release-management".format(S.gitee_info["user"]), "master", "release-management")
        obs_meta_path = C.pull_from_gitee_repo(S.gitee_info["user"], S.gitee_info["passwd"], \
                "https://gitee.com/{0}/obs_meta".format(S.gitee_info["user"]), "master", "obs_meta")
        kw = {"obs_meta_path": obs_meta_path,
                "release_management_path": release_management_path,
                "gitee_user": S.gitee_info["user"],
                "gitee_pwd": S.gitee_info["passwd"],
                "pckg_mgmt": "true"
                }
        P = SyncPckgMgmt(**kw)
        cmd = "python3 ../tools/create_pckg_mgmt_yaml.py -fp bringInRely -fb master -tp openEuler:20.99:LTS -tb openEuler-20.99-LTS"
        if os.system(cmd) == 0:
            assert True
        else:
            assert False, "fail to exec cmd:{0}".format(cmd)

    def teardown_class(self):
        S.unset_gitee()
        cmd = "rm -fr {0} {1}".format(obs_meta_path, release_management_path)
        if os.system(cmd) == 0:
            assert True
        else:
            assert False, "fail to exec cmd:{0}".format(cmd)

    def test_1(self):
        """
        test for add a legal yaml
        """
        assert os.path.exists(release_management_path), "{0} not exist".format(release_management_path)
        assert os.path.exists("pckg-mgmt.yaml"), "pckg-mgmt.yaml not exist"
        cmd = "mkdir -p {0}/openEuler-20.99-LTS && mv pckg-mgmt.yaml {1}".format(
                release_management_path, os.path.join(release_management_path, "openEuler-20.99-LTS"))
        if os.system(cmd) == 0:
            assert True
        else:
            assert False, "fail to exec cmd:{0}".format(cmd)
        C.commit_to_gitee_repo(release_management_path, "openEuler-20.99-LTS/pckg-mgmt.yaml")
        ret = P.sync_yaml_meta()
        if ret == -2:
            assert False, "yaml file is not legal"  
        else:
            assert True
        yaml_path = os.path.join(release_management_path, "openEuler-20.99-LTS/pckg-mgmt.yaml")
        verify_result(yaml_path, obs_meta_path, ret)

    def test_2(self):
        """
        test for add a error yaml
        """
        assert os.path.exists(release_management_path), "{0} not exist".format(release_management_path)
        cmd = "mkdir -p {0}/openEuler-mytest".format(release_management_path)
        if os.system(cmd) == 0:
            assert True
        else:
            assert False, "fail to exec cmd:{0}".format(cmd)
        msg = """packages:
  natural:
  - name: A-Tune
    branch_from: master
    branch_to: openEuler-test
    obs_from: openEuler:Mainline
    obs_to: openEuler:mytest
    date: 2021-06-23-14-25-20
  recycle: []
  delete: []
"""
        cmd = "echo \"%s\" > %s" % (msg, os.path.join(release_management_path, "openEuler-mytest/pckg-mgmt.yaml"))
        if os.system(cmd) == 0:
            assert True
        else:
            assert False, "fail to exec cmd:{0}".format(cmd)
        C.commit_to_gitee_repo(release_management_path, "openEuler-mytest/pckg-mgmt.yaml")
        ret = P.sync_yaml_meta()
        if ret == -2:
            assert True
        else:
            assert False
        yaml_path = os.path.join(release_management_path, "openEuler-mytest/pckg-mgmt.yaml")
        verify_result(yaml_path, obs_meta_path, ret)

    def test_3(self):
        """
        test for del a pkg
        """
        assert os.path.exists(release_management_path), "{0} not exist".format(release_management_path)
        yaml_path = os.path.join(release_management_path, "openEuler-20.99-LTS/pckg-mgmt.yaml")
        assert os.path.exists(yaml_path), "{0} not exist".format(yaml_path)
        cmd = "sed -n '3,8p' %s" % yaml_path
        ret = os.popen(cmd).read()
        if ret:
            assert True
        else:
            assert False, "fail to exec cmd:{0}".format(cmd)
        cmd = "sed -i '$s/.*/  delete:/g' %s" % yaml_path
        if os.system(cmd) == 0:
            assert True
        else:
            assert False, "fail to exec cmd:{0}".format(cmd)
        cmd = "echo \"%s\" >> %s && sed -i '$d' %s" % (ret, yaml_path, yaml_path)
        if os.system(cmd) == 0:
            assert True
        else:
            assert False, "fail to exec cmd:{0}".format(cmd)
        cmd = "sed -i '3,8d' %s" % yaml_path
        if os.system(cmd) == 0:
            assert True
        else:
            assert False, "fail to exec cmd:{0}".format(cmd)
        C.commit_to_gitee_repo(release_management_path, "openEuler-20.99-LTS/pckg-mgmt.yaml")
        res = P.sync_yaml_meta()
        if res == 0:
            assert True
        else:
            assert False, "fail to push code."
        for msg in ret.split('\n'):
            if "- name:" in msg:
                name = msg.split(': ')[1]
            if "branch_to" in msg:
                branch = msg.split(': ')[1]
            if "obs_to" in msg:
                proj = msg.split(': ')[1]
        assert os.path.exists(obs_meta_path), "{0} not exist".format(obs_meta_path)
        prj_path = os.path.join(obs_meta_path, branch, proj)
        pkg_path = os.path.join(prj_path, name, "_service")
        if os.path.exists(prj_path):
            if not os.path.exists(pkg_path):
                assert True
            else:
                assert False, "fail to delete package:%s." % name
        else:
            assert False, "project:%s is not exist." % proj

    def test_4(self):
        """
        test for add a pkg
        """
        assert os.path.exists(release_management_path), "{0} not exist".format(release_management_path)
        yaml_path = os.path.join(release_management_path, "openEuler-20.99-LTS/pckg-mgmt.yaml")
        assert os.path.exists(yaml_path), "{0} not exist".format(yaml_path)
        cmd = "tail -n6 %s" % yaml_path
        result = os.popen(cmd).read().split('\n')
        if result:
            assert True
        else:
            assert False, "fail to exec cmd:{0}".format(cmd)
        msg = [x for x in result if x!= '']
        cmd = "grep -n \"  natural:\" {0}".format(yaml_path)
        i = int(os.popen(cmd).read()[0])
        for ret in msg:
            cmd = "sed -i '%s a\\%s' %s" % (i, ret, yaml_path)
            i += 1
            if os.system(cmd) == 0:
                assert True
            else:
                assert False, "fail to exec cmd:{0}".format(cmd)
        cmd = "sed -n '$=' {0}".format(yaml_path)
        ret = int(os.popen(cmd).read())
        if ret:
            assert True
        else:
            assert False, "fail to exec cmd:{0}".format(cmd)
        cmd = "sed -i '{0},{1}d' {2}".format(ret - 5, ret, yaml_path)
        if os.system(cmd) == 0:
            assert True
        else:
            assert False, "fail to exec cmd:{0}".format(cmd)
        cmd = "sed -i '/  delete:/c\\  delete: []' {0}".format(yaml_path)
        if os.system(cmd) == 0:
            assert True
        else:
            assert False, "fail to exec cmd:{0}".format(cmd)
        C.commit_to_gitee_repo(release_management_path, "openEuler-20.99-LTS/pckg-mgmt.yaml")
        res = P.sync_yaml_meta()
        if res == 0:
            assert True
        else:
            assert False, "fail to push code."
        for tmp in msg:
            if "- name:" in tmp:
                name = tmp.split(': ')[1]
            if "branch_to" in tmp:
                branch = tmp.split(': ')[1]
            if "obs_to" in tmp:
                proj = tmp.split(': ')[1]
        assert os.path.exists(obs_meta_path), "{0} not exist".format(obs_meta_path)
        prj_path = os.path.join(obs_meta_path, branch, proj)
        pkg_path = os.path.join(prj_path, name, "_service")
        if os.path.exists(prj_path):
            if os.path.exists(pkg_path):
                assert True
            else:
                assert False, "fail to add package:%s." % name
        else:
            assert False, "project:%s is not exist." % proj

    def test_5(self):
        """
        test for rcycle a pkg
        """
        assert os.path.exists(release_management_path), "{0} not exist".format(release_management_path)
        yaml_path = os.path.join(release_management_path, "openEuler-20.99-LTS/pckg-mgmt.yaml")
        assert os.path.exists(yaml_path), "{0} not exist".format(yaml_path)
        cmd = "sed -n '3,8p' %s" % yaml_path
        result = os.popen(cmd).read()
        if result:
            assert True
        else:
            assert False, "fail to exec cmd:{0}".format(cmd)
        cmd = "sed -i '/recycle:/c\\  recycle:' {0}".format(yaml_path)
        if os.system(cmd) == 0:
            assert True
        else:
            assert False, "fail to exec cmd:{0}".format(cmd)
        cmd = "sed -n '/delete:/,$p' {0}".format(yaml_path)
        ret = os.popen(cmd).read()
        if ret:
            assert True
        else:
            assert False, "fail to exec cmd:{0}".format(cmd)
        cmd = "sed -i '/delete:/,$d' {0}".format(yaml_path)
        if os.system(cmd) == 0:
            assert True
        else:
            assert False, "fail to exec cmd:{0}".format(cmd)
        msg = result + ret
        cmd = "echo \"{0}\" >> {1}".format(msg, yaml_path)
        if os.system(cmd) == 0:
            assert True
        else:
            assert False, "fail to exec cmd:{0}".format(cmd)
        cmd = "sed -i '$d' {0} && sed -i '3,8d' {0}".format(yaml_path)
        if os.system(cmd) == 0:
            assert True
        else:
            assert False, "fail to exec cmd:{0}".format(cmd)
        C.commit_to_gitee_repo(release_management_path, "openEuler-20.99-LTS/pckg-mgmt.yaml")
        ret = P.sync_yaml_meta()
        if ret == "nothing to push":
            assert True
        else:
            assert False, "fail to move a package to recycle."

    def test_6(self):
        """
        test for modify other file, not is pckg-mgmt.yaml
        """
        assert os.path.exists(release_management_path), "{0} not exist".format(release_management_path)
        yaml_path = os.path.join(release_management_path, "openEuler-20.99-LTS/pckg-mgmt.yaml")
        assert os.path.exists(yaml_path), "{0} not exist".format(yaml_path)
        cmd = "echo \"test\" > {0}".format(os.path.join(release_management_path, "openEuler-20.99-LTS/testfile"))
        if os.system(cmd) == 0:
            assert True
        else:
            assert False, "fail to exec cmd:{0}".format(cmd)
        C.commit_to_gitee_repo(release_management_path, "openEuler-20.99-LTS/testfile")
        ret = P.sync_yaml_meta()
        if ret == "nothing to push":
            assert True
        else:
            assert False, "fail to modify other file, not is pckg-mgmt.yaml."
