#/bin/env python3
# -*- encoding=utf8 -*-
"""
created by: miaokaibo
date: 2020-10-20 9:55

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
        config_path = os.path.join(
                os.path.split(os.path.realpath(__file__))[0],
                "../config/config.ini")
        self.config = ConfParser()
        #self.config = configparser.ConfigParser()
        self.config.read(config_path, encoding='utf-8')
        self._init_branch_list()
        self._init_update_enabled_flag()
        self._init_ignored_repo()
        self._init_package_info_file()

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


if __name__ == "__main__":
    p = ParserConfigIni()
    print(p.get_update_enabled_flag())
    print(p.get_branch_list())
    print(p.get_ignored_repo())
    print(p.get_package_info_file())