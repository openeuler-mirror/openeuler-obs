#/bin/env python3
# -*- encoding=utf8 -*-
"""
created by: miaokaibo
date: 2020-10-20 9:55

parser config.ini
"""
import os
import configparser


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

    def _init_update_enabled_flag(self):
        """
        init update enable flag for branch from config.ini
        return: None
        """
        branch_list = self.config.options("update_enable")
        for b in branch_list:
            self.update_enabled_flag[b] = self.config.get("update_enable", b)

    def get_update_enabled_flag(self):
        """
        get update enabled flag for branch
        return: update enable flag dict
        """
        return self.update_enabled_flag


if __name__ == "__main__":
    p = ParserConfigIni()
    update_enabled_flag = p.get_update_enabled_flag()
    print(update_enabled_flag)
