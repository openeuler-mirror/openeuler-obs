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
from core.gitee_to_obs import CheckCode
from core.getdate import GETDate
from core.check_meta_service import CheckMetaPull
from core.package_manager import OBSPkgManager
from core.update_obs_repos import RPMManager
from core.obs_mail_notice import ObsMailNotice
import os

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
        kwargs["init_path"] = os.getcwd()
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

    def _save_unsync_info(self):
        """
        save unsync package info for manual operation later
        return:
        """
        log.debug("save package info")
        si = SaveInfo(self.kwargs["gitee_user"], self.kwargs["gitee_pwd"])
        si.save_unsync_package(self.kwargs["repository"], self.kwargs["branch"])

    def _save_latest_info(self):
        """
        save package latest info
        return:
        """
        log.debug("save latest info")
        si = SaveInfo(self.kwargs["gitee_user"], self.kwargs["gitee_pwd"])
        si.save_latest_info(self.kwargs["branch"])

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

    def _check_codes(self):
        """
        check codes between gitee and obs
        """
        log.debug("check codes")
        check_codes = CheckCode(**self.kwargs)
        check_codes.check_all()

    def _get_latest_date(self):
        """
        get the latest git date to obs_pkgs_rpms
        """
        log.debug("get latest date")
        get_date = GETDate(**self.kwargs)
        get_date.update_to_obs_pkg_rpms()

    def _mail_notice(self):
        """
        send mail to the package owner
        """
        log.debug("OBS Mail Notice")
        mail_notice = ObsMailNotice(**self.kwargs)
        mail_notice.notify_all_respon_person()

    def run(self):
        """
        run main
        return:
        """
        if self.kwargs["check_codes"]:
            self._check_codes()
        elif self.kwargs["repo_rpms_update"]:
            self._update_obs_repo_rpms()
        elif self.kwargs["latest_info"]:
            self._save_latest_info()
        elif self.kwargs["repository"] == "obs_meta":
            self._obs_meta_action()
        elif self.kwargs["sync_gitee_to_obs"] == "true":
            if not self.update_enabled_flag[self.kwargs["branch"]]:
                if self.kwargs["repository"] and self.kwargs["repository"] not in self.ignore_list:
                    log.debug("can not update branch:%s, package: %s"
                            % (self.kwargs["branch"], self.kwargs["repository"]))
                    self._save_unsync_info()
            else:
                self._update_package()
        elif self.kwargs["check_pkg_service"] == "true":
            print("check_pkg_service")
            check = CheckMetaPull(**self.kwargs)
            check.do_all()
        elif self.kwargs["get_latest_date"] == "true" and self.kwargs["branch"]:
            self._get_latest_date()
        elif self.kwargs["obs_mail_notice"] == "true":
            self._mail_notice()
