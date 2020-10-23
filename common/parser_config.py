#/bin/env python3
# -*- encoding=utf8 -*-
"""
created by: miaokaibo
date: 2020-10-20 9:55

parser config.ini
"""
import os
import configparser
from common import common
#import common



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
        self.config = configparser.ConfigParser()
        self.config.read(config_path, encoding='utf-8')
        self._init_update_enabled_flag()
        self._init_ignored_repo()
        self._init_package_info_file()

    def _init_update_enabled_flag(self):
        """
        init update enable flag for branch from config.ini
        return: None
        """
        branch_list = self.config.options("update_enable")
        for b in branch_list:
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
        get file
        """
        return self.package_info_file


if __name__ == "__main__":
    p = ParserConfigIni()
    update_enabled_flag = p.get_update_enabled_flag()
    print(update_enabled_flag)
