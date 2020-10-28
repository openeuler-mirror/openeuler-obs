#/bin/env python3
# -*- encoding=utf8 -*-
"""
created by: miaokaibo
date: 2020-10-20 9:55

main script for running
"""
from common.log_obs import log
from common.parser_config import ParserConfigIni
from core.save import SaveInfo
from core.project_manager import OBSPrjManager


class Runner(object):
    """
    Runner class for all action
    """
    def __init__(self, **kwargs):
        """
        init action
        kwargs: dict, init dict by "a"="A" style
        return:
        """
        self.kwargs = kwargs
        log.info(self.kwargs)
        parc = ParserConfigIni()
        self.update_enabled_flag = parc.get_update_enabled_flag()
        self.ignore_list = parc.get_ignored_repo()

    def _obs_meta_action(self):
        """
        action basis on change of obs_meta
        return:
        """
        log.debug("obs_meta change")
        obs_pm = OBSPrjManager(self.kwargs["obs_path"])
        obs_pm.manager_action()
        # TODO add package service

    def _save_package_info(self):
        """
        save package info for manual operation later
        return:
        """
        log.debug("save package info")
        si = SaveInfo()
        si.save_package_msg(self.kwargs["repository"], self.kwargs["branch"])

    def _update_package(self):
        """
        update package code for obs
        return:
        """
        log.debug("update package code")
        # TODO

    def run(self):
        """
        run main
        return:
        """
        log.debug(self.ignore_list)
        log.debug(self.update_enabled_flag)
        if self.kwargs["repository"] == "obs_meta":
            self._obs_meta_action()
        elif self.kwargs["repository"] not in self.ignore_list:
            if not self.update_enabled_flag[self.kwargs["branch"].lower()]:
                log.debug("can not update branch:%s, package: %s"
                        % (self.kwargs["branch"], self.kwargs["repository"]))
                self._save_package_info()
            else:
                self._update_package()

