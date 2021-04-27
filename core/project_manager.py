#!/usr/bin/env python3
# -*- encoding=utf-8 -*-
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
# Create: 2020-10-29
# ******************************************************************************

"""
obs project manager
"""
import re
import os
import sys
import time
from datetime import datetime
current_path = os.path.join(os.path.split(os.path.realpath(__file__))[0])
sys.path.append(os.path.join(current_path, ".."))
from common.log_obs import log


class OBSPrjManager(object):
    """
    obs project manager, include create delete and backup
    """
    def __init__(self, obs_meta):
        """
        init project base info
        obs_meta_path: path of obs_meta repository
        """
        self.obs_meta = obs_meta
        os.chdir(self.obs_meta)
        self.commit_msg = []

    def _set_info(self):
        """
        set obs project info, include name branch metadata
        """
        cmd = "git diff --name-status HEAD~1 HEAD~0"
        log.info(cmd)
        ret = os.popen(cmd).read().replace("\t", " ")
        log.info(ret)
        if "OBS_PRJ_meta" not in ret:
            log.info("obs project not be changed") 
            return 1
        message = ret.split("\n")
        log.info(message)
        for msg in message:
            msg = ' '.join(msg.split())
            log.info(msg)
            if "OBS_PRJ_meta" not in msg:
                continue
            action_type = msg.split(" ")[0]
            if not action_type:
                continue
            tmp = {}
            tmp["action_type"] = action_type 
            file_path = msg.split(" ")[1]
            if action_type in ["A", "D", "M"]:
                tmp["branch"] = file_path.split("/")[-2]
                tmp["file"] = file_path
                tmp["name"] = file_path.split("/")[-1]
                if len(file_path.split("/")) > 3:
                    tmp["sub_dir"] = file_path.split("OBS_PRJ_meta/")[1].split(tmp["branch"])[0]
                else:
                    tmp["sub_dir"] = ""
            elif action_type.startswith("R"):
                tmp["old_file"] = msg.split(" ")[1]
                tmp["new_file"] = msg.split(" ")[2]
                tmp["old_name"] = tmp["old_file"].split("/")[-1]
                tmp["new_name"] = tmp["new_file"].split("/")[-1]
            else:
                continue
            self.commit_msg.append(tmp)
        log.info(self.commit_msg)
        return 0

    def _create(self, sub_dir, branch, name, meta_file):
        """
        create project
        branch: branch name
        name: name of obs project
        meta_file: meta of obs project
        """
        obs_prj_dir = os.path.join(sub_dir, branch, name)
        log.info("obs project dir path: %s" % obs_prj_dir)
        if not os.path.exists(obs_prj_dir):
            if name.endswith(":Bak"):
                cmd = "cp -r %s %s" % (os.path.join(branch, name.replace(":Bak", "")), 
                    obs_prj_dir)
            else:
                cmd = "mkdir -p %s && touch %s/README.md" % (obs_prj_dir, obs_prj_dir)
            res = os.popen(cmd).read()
            log.info(res)
        log.info("create new obs project by meta file %s" % meta_file)
        if os.path.exists(obs_prj_dir):
            cmd = "osc api -X PUT /source/%s/_meta -T %s" % (name, meta_file)
            os.system(cmd)
            cmd = "git add %s && \
                    git commit -m 'add new obs project by meta file' && \
                    git push" % obs_prj_dir
            for i in range(5):
                if os.system(cmd) == 0:
                    break
    
    def _change_meta(self, name, meta_file):
        """
        change meta data of project
        name: name of obs project
        meta_file: meta of obs project
        """
        cmd = "osc api -X PUT /source/%s/_meta -T %s" % (name, meta_file)
        os.system(cmd)

    def _delete(self, sub_dir, branch, name):
        """
        delete project
        branch: branch name
        name: name of obs project
        """
        log.info("delete project %s" % name)
        cmd = "osc api -X DELETE /source/%s" % name
        os.system(cmd)
        cmd = "git rm -r %s && git commit -m 'delete project %s' && \
                git push" % (os.path.join(sub_dir, branch, name), name)
        for i in range(5):
            if os.system(cmd) == 0:
                break

    def _rename(self, sub_dir, branch, old_name, new_name, new_meta):
        """
        rename project
        branch: branch name
        name: name of obs project
        meta_file: meta of new obs project
        """
        cmd = "osc api -X DELETE /source/%s" % old_name
        os.system(cmd)
        cmd = "osc api -X PUT /source/%s/_meta -T %s" % (new_name, new_meta)
        os.system(cmd)
        cmd = "cp -r %s %s && git rm -r %s && git add %s && \
                git commit -m 'rename project %s to %s' && \
                git push" % (os.path.join(sub_dir, branch, old_name), \
                os.path.join(sub_dir, branch, new_name), \
                os.path.join(sub_dir, branch, old_name), \
                os.path.join(sub_dir, branch, new_name), \
                os.path.join(sub_dir, branch, old_name), \
                os.path.join(sub_dir, branch, new_name))
        log.info(cmd)
        for i in range(5):
            if os.system(cmd) == 0:
                break
    
    def manager_action(self):
        """
        main function of obs project manager 
        """
        res = self._set_info()
        if res != 0:
            return res
        for msg in self.commit_msg:
            if msg["action_type"] == "A":
                self._create(msg["sub_dir"], msg["branch"], msg["name"], msg["file"])
            elif msg["action_type"] == "M":
                self._change_meta(msg["name"], msg["file"])
            elif msg["action_type"] == "D":
                self._delete(msg["sub_dir"], msg["branch"], msg["name"])
            elif msg["action_type"].startswith("R"):
                self._rename(msg["sub_dir"], msg["branch"], msg["old_name"], msg["new_name"], msg["new_file"])
        return 0


if __name__ == "__main__":
    obs_meta_path = sys.argv[1]
    obs_prj = OBSPrjManager(obs_meta_path)
    obs_prj.manager_action()

