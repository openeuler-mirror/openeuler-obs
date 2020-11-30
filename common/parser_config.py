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
parser config.ini
"""
import os
import sys
import configparser
from common import common
#import common


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


class ParserConfigIni(object):
    """
    get parmers from config.ini file
    """
    def __init__(self):
        """
        init parmers by config.ini
        return: None
        """
        self.update_enabled_flag = {}
        self.branch_proj = {}
        self.repos = {}
        self.obs_repos = {}
        config_path = "config/config.ini"
        self.config = ConfParser()
        #self.config = configparser.ConfigParser()
        self.config.read(config_path, encoding='utf-8')
        self._init_branch_list()
        self._init_update_enabled_flag()
        self._init_ignored_repo()
        self._init_package_info_file()
        self._init_branch_proj()
        self._init_gitee_repository()
        self._init_obs_repository()
        self._init_obs_prj_root_path()

    def _init_branch_list(self):
        """
        init branch list from config.ini
        return: None
        """
        self.branch_list = self.config.options("update_enable")

    def get_branch_list(self):
        """
        get current branch list
        return: branch list
        """
        return self.branch_list

    def _init_update_enabled_flag(self):
        """
        init update enable flag for branch from config.ini
        return: None
        """
        for b in self.branch_list:
            self.update_enabled_flag[b] = common.str_to_bool(self.config.get("update_enable", b))

    def get_update_enabled_flag(self):
        """
        get update enabled flag for branch
        return: update enable flag dict
        """
        return self.update_enabled_flag

    def _init_ignored_repo(self):
        """
        init ignored repo list
        return: None
        """
        self.ignored_repos = self.config.get("ignore_repo", "name").split(" ")

    def get_ignored_repo(self):
        """
        get ignored repo
        return: ignored repo list
        """
        return self.ignored_repos

    def _init_package_info_file(self):
        """
        init package info file for store package which is not be updated
        """
        self.package_info_file = self.config.get("package_info_file", "name")

    def get_package_info_file(self):
        """
        get package info file which store package that not be updated
        """
        return self.package_info_file
    
    def _init_branch_proj(self):
        """
        init branch proj
        """
        branch_proj_list = self.config.options("branch_proj")
        for b in branch_proj_list:
            self.branch_proj[b] = self.config.get("branch_proj", b)

    def get_branch_proj(self):
        """
        get branch proj data
        return a dict
        """
        return self.branch_proj

    def _init_gitee_repository(self):
        """
        init repos url
        """
        repos_list = self.config.options("gitee_repository")
        for repo in repos_list:
            self.repos[repo] = self.config.get("gitee_repository", repo)

    def get_repos_dict(self):
        """
        get repos url
        return: repos, type: dict
        """
        return self.repos

    def _init_obs_repository(self):
        """
        init obs repos name
        """
        obs_list = self.config.options("obs_project_repos")
        for obs in obs_list:
            self.obs_repos[obs.replace("-", ":")] = self.config.get("obs_project_repos", obs)

    def get_obs_repos_dict(self):
        """
        get repos of obs
        return: obs repos, type: dict
        """
        return self.obs_repos

    def _init_obs_prj_root_path(self):
        """
        init obs project root path where store all packages of all obs projects
        """
        self.obs_prj_root_path = self.config.get("obs_project_root_path", "path")

    def get_obs_prj_root_path(self):
        """
        get obs project root path
        """
        return self.obs_prj_root_path


if __name__ == "__main__":
    p = ParserConfigIni()
    print(p.get_update_enabled_flag())
    print(p.get_branch_list())
    print(p.get_ignored_repo())
    print(p.get_package_info_file())
    print(p.get_branch_proj())
    print(p.get_repos_dict())
    print(p.get_obs_repos_dict())
    print(p.get_obs_prj_root_path())
