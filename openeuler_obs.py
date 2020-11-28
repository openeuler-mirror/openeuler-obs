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
# Create: 2020-10-16
# ******************************************************************************

"""
main script for openeuler-obs
"""
import argparse
import os
import sys
from common.log_obs import log
from core.runner import Runner


#ArgumentParser
par = argparse.ArgumentParser()
par.add_argument("-o", "--obs", default=None,
        help="Local path of obs_meta repository.", required=False)
par.add_argument("-r", "--repository",
        help="gitee repository name.", required=False)
par.add_argument("-b", "--branch", default="master",
        help="gitee repository branch name.", required=False)
par.add_argument("-b2", "--branch2", default=None,
        help="gitee repository branch name, cp some packages to this branch.", required=False)
par.add_argument("-p", "--project", default=None,
        help="obs project name.", required=False)
par.add_argument("-p2", "--project2", default=None,
        help="obs project name, cp some packages to this project.\
                should be used with -o -b2.", required=False)
par.add_argument("-ip", "--source_server_ip", default=None,
        help="ip of obs source server machine.", required=False)
par.add_argument("-sport", "--source_server_port", default=None,
        help="ip of obs source server machine.", required=False)
par.add_argument("-suser", "--source_server_user", default=None,
        help="user of obs source server machine.", required=False)
par.add_argument("-spwd", "--source_server_pwd", default=None,
        help="password of obs source server machine user.", required=False)
par.add_argument("-guser", "--gitee_user", default=None,
        help="user of gitee.", required=False)
par.add_argument("-gpwd", "--gitee_pwd", default=None,
        help="password of gitee.", required=False)
par.add_argument("-c", "--check", default=False,
        help="check obs package.", required=False)
par.add_argument("--pkglist", default=None, nargs='+',
        help="packages list, connect everyone by espace.", required=False)

par.add_argument("-up", "--repo_rpms_update", default=False,
        help="update obs repo rpms.\
        should be used with project repo arch rsip rsu rsup rsp gitee_user gitee_pwd, \
        and pkglist will be used if update some packges not all.", required=False)
par.add_argument("-repo", "--repo", default=None,
        help="obs project repo name.", required=False)
par.add_argument("-arch", "--arch", default=None,
        help="obs project arch name.", required=False)
par.add_argument("-rsip", "--repo_server_ip", default=None,
        help="obs repo server machine ip.", required=False)
par.add_argument("-rsu", "--repo_server_user", default=None,
        help="obs repo server user.", required=False)
par.add_argument("-rsup", "--repo_server_pwd", default=None,
        help="obs repo server user password.", required=False)
par.add_argument("-rsp", "--repo_server_port", default=None,
        help="obs repo server port.", required=False)


args = par.parse_args()
#apply
kw = {
        "obs_meta_path": args.obs,
        "repository": args.repository,
        "branch": args.branch,
        "branch2": args.branch2,
        "project": args.project,
        "project2": args.project2,
        "source_server_ip": args.source_server_ip,
        "source_server_port": args.source_server_port,
        "source_server_user": args.source_server_user,
        "source_server_pwd": args.source_server_pwd,
        "gitee_user": args.gitee_user,
        "gitee_pwd": args.gitee_pwd,
        "check_flag": args.check,
        "pkglist": args.pkglist,

        "repo_rpms_update": args.repo_rpms_update,
        "repo": args.repo,
        "arch": args.arch,
        "repo_server_ip": args.repo_server_ip,
        "repo_server_user": args.repo_server_user,
        "repo_server_port": args.repo_server_port,
        "repo_server_pwd": args.repo_server_pwd,
        }

run = Runner(**kw)
run.run()
