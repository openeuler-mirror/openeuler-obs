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
main script for running
"""
from common.log_obs import log
from common.parser_config import ParserConfigIni
from core.save import SaveInfo
from core.project_manager import OBSPrjManager
from core.gitee_to_obs import SYNCCode
from core.package_manager import OBSPkgManager
from core.update_obs_repos import RPMManager


class Runner(object):
    """
    Runner class for all action
    """
    def __init__(self, **kwargs):
        """
        init action
        kwargs: dict
        return:
        """
        self.kwargs = kwargs
        parc = ParserConfigIni()
        self.update_enabled_flag = parc.get_update_enabled_flag()
        self.ignore_list = parc.get_ignored_repo()

    def _obs_meta_action(self):
        """
        action basis on change of obs_meta
        return:
        """
        log.debug("obs_meta change")
        if not self.kwargs["obs_meta_path"]:
            log.error("can not find obs_meta path")
        else:
            obs_prjm = OBSPrjManager(self.kwargs["obs_meta_path"])
            obs_prjm.manager_action()
            obs_pkgm = OBSPkgManager(**self.kwargs)
            obs_pkgm.obs_pkg_admc()

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
        syc = SYNCCode(**self.kwargs)
        syc.sync_code_to_obs()

    def _update_obs_repo_rpms(self):
        """
        update obs repo rpms
        """
        log.debug("update repo rpms")
        update_repo = RPMManager(**self.kwargs)
        update_repo.update_pkgs()

    def run(self):
        """
        run main
        return:
        """
        log.debug(self.ignore_list)
        log.debug(self.update_enabled_flag)
        if self.kwargs["repo_rpms_update"]:
            self._update_obs_repo_rpms()
        elif self.kwargs["repository"] == "obs_meta":
            self._obs_meta_action()
        elif self.kwargs["repository"] not in self.ignore_list:
            if not self.update_enabled_flag[self.kwargs["branch"]]:
                log.debug("can not update branch:%s, package: %s"
                        % (self.kwargs["branch"], self.kwargs["repository"]))
                self._save_package_info()
            else:
                self._update_package()

