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
common function for testing
"""
import os
import sys
import configparser




class ConfParser(configparser.ConfigParser):
    """
    rewrite optionxform function
    """
    def __init__(self, defaults=None):
        """
        init
        """
        configparser.ConfigParser.__init__(self, defaults=None)

    def optionxform(self, optionstr):
        """
        delete old function lower()
        """
        return optionstr


class SetEnv(object):
    """
    get parmers from config.ini file
    """
    def __init__(self):
        """
        init parmers by config.ini
        return: None
        """
        current_path = os.path.join(os.path.split(os.path.realpath(__file__))[0])
        config_path = os.path.join(current_path, "config.ini")
        self.config = ConfParser()
        self.config.read(config_path, encoding='utf-8')
        self._obs_info = None
        self._gitee_info = None
        self.obs_info = {}
        self.gitee_info = {}
        self.home_dir = os.environ['HOME']
        self.oscrc = os.path.join(self.home_dir, ".oscrc")
        self.oscrc_bak = os.path.join(self.home_dir, ".oscrc.bak")
        self.gitee_info_bak = {"user":"", "email":""}
    
    def set_oscrc(self):
        self._obs_info = self.config.options("obs")
        for info in self._obs_info:
            self.obs_info[info] = self.config.get("obs", info)
        if os.path.exists(self.oscrc):
            cmd = "mv %s %s" % (self.oscrc, self.oscrc_bak)
            if os.system(cmd) == 0:
                print("oscrc file bakup sucessfull")
            else:
                print("oscrc file backup failed")
                exit(1)
        cmd = "touch %s && echo '[general]\napiurl=%s\n[%s]\nuser=%s\npass=%s' > %s" % \
             (self.oscrc, self.obs_info["url"], self.obs_info["url"], self.obs_info["user"], \
              self.obs_info["passwd"], self.oscrc)
        ret=os.popen(cmd).read()
    
    def unset_oscrc(self):
        if os.path.exists(self.oscrc_bak):
            cmd = "rm -rf %s && mv %s %s" % (self.oscrc, self.oscrc_bak, self.oscrc)
        else:
            cmd = "rm -rf %s" % self.oscrc
        ret=os.popen(cmd).read()
    
    def set_gitee(self):
        ret = os.popen("git config --global user.name").read()
        self.gitee_info_bak["user"] = ret.strip("\n")
        ret = os.popen("git config --global user.email").read()
        self.gitee_info_bak["email"] = ret.strip("\n")
        self._gitee_info = self.config.options("gitee")
        for info in self._gitee_info:
            self.gitee_info[info] = self.config.get("gitee", info)
        cmd = "git config --global user.name '%s' && git config --global user.email '%s'" % \
             (self.gitee_info["user"], self.gitee_info["email"])
        ret = os.popen(cmd).read()
        print(ret)

    def unset_gitee(self):
        
        cmd = "git config --global user.name '%s' && git config --global user.email '%s'" % \
              (self.gitee_info_bak["user"], self.gitee_info_bak["email"])
        ret = os.popen(cmd).read()
        print(ret)
    

class CommonFunc(object):
    def __init__(self):
        pass

    def pull_from_gitee_repo(self, user, passwd, url, branch, repo):
        passwd = passwd.replace("@", "%40")
        url = url.split("//")[0] + "//" + user + ":" + passwd + "@" + url.split("//")[1]
        cmd = "git clone --depth 2 %s -b %s %s" % (url, branch, repo)
        print(cmd)
        ret = os.popen(cmd).read()    
        repo_path = os.path.join(os.getcwd(), repo)
        return repo_path
   
    def commit_to_gitee_repo(self, repo_path, *kwargs):
        os.chdir(repo_path)
        for f in kwargs:
            cmd = "git add %s" % f
            ret = os.popen(cmd).read()
        cmd = "git commit -m test"
        if os.system(cmd) == 0:
            return True
        else:
            return False
        

if __name__ == "__main__":
    import time
    p = SetEnv()
    p.set_oscrc()
    p.unset_oscrc()
    p.set_gitee()
    p.unset_gitee()
