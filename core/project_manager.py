#!/usr/bin/env python
# -*- encoding=utf-8 -*-
import re
import os
import sys
import time
from datetime import datetime
current_path = os.path.join(os.path.split(os.path.realpath(__file__))[0])
sys.path.append(os.path.join(current_path, ".."))
from common.log_obs import log


class OBSPrjManager():
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
            log.info(msg)
            if "OBS_PRJ_meta" not in msg:
                continue
            action_type = msg.split(" ")[0]
            if not action_type:
                continue
            tmp = {}
            tmp["action_type"] = action_type 
            tmp["branch"] = msg.split(" ")[1].split("/")[1]
            if action_type in ["A", "D", "M"]:
                tmp["file"] = msg.split(" ")[1]
                tmp["name"] = tmp["file"].split("/")[-1]
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

    def _create(self, branch, name, meta_file):
        """
        create project
        branch: branch name
        name: name of obs project
        meta_file: meta of obs project
        """
        obs_prj_dir = os.path.join(branch, name)
        log.info("obs project dir path: %s" % obs_prj_dir)
        if not os.path.exists(obs_prj_dir):
            if name.endswith(":Bak"):
                cmd = "cp -r %s %s" % (os.path.join(branch, name.replace(":Bak", "")), 
                    obs_prj_dir)
            else:
                cmd = "mkdir %s && touch %s/README.md" % (obs_prj_dir, obs_prj_dir)
            res = os.popen(cmd).read()
            log.info(res)
        log.info("create new obs project by meta file %s" % meta_file)
        if os.path.exists(obs_prj_dir):
            cmd = "osc api -X PUT /source/%s/_meta -T %s" % (name, meta_file)
            os.system(cmd)
            cmd = "git add %s && \
                    git commit -m 'add new obs project by meta file' && \
                    git push" % obs_prj_dir
            os.system(cmd)
    
    def _change_meta(self, name, meta_file):
        """
        change meta data of project
        name: name of obs project
        meta_file: meta of obs project
        """
        cmd = "osc api -X PUT /source/%s/_meta -T %s" % (name, meta_file)
        os.system(cmd)

    def _delete(self, branch, name):
        """
        delete project
        branch: branch name
        name: name of obs project
        """
        log.info("delete project %s" % name)
        cmd = "osc api -X DELETE /source/%s" % name
        os.system(cmd)
        cmd = "git rm -r %s && git commit -m 'delete project %s' && \
                git push" % (os.path.join(branch, name), name)
        os.system(cmd)

    def _rename(self, branch, old_name, new_name, new_meta):
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
                git push" % (os.path.join(branch, old_name), \
                os.path.join(branch, new_name), \
                os.path.join(branch, old_name), \
                os.path.join(branch, new_name), \
                os.path.join(branch, old_name), \
                os.path.join(branch, new_name))
        log.info(cmd)
        os.system(cmd)
    
    def manager_action(self):
        """
        main function of obs project manager 
        """
        res = self._set_info()
        if res != 0:
            return res
        for msg in self.commit_msg:
            if msg["action_type"] == "A":
                self._create(msg["branch"], msg["name"], msg["file"])
            elif msg["action_type"] == "M":
                self._change_meta(msg["name"], msg["file"])
            elif msg["action_type"] == "D":
                self._delete(msg["branch"], msg["name"])
            elif msg["action_type"].startswith("R"):
                self._rename(msg["branch"], msg["old_name"], msg["new_name"], msg["new_file"])
        return 0


if __name__ == "__main__":
    obs_meta_path = sys.argv[1]
    obs_prj = OBSPrjManager(obs_meta_path)
    obs_prj.manager_action()

