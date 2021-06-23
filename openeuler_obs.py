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
par.add_argument("-c1", "--check_yaml", default=False,
        help="check obs package with yaml file.", required=False)
par.add_argument("-c2", "--check_meta", default=False,
        help="check obs package with obs_meta.", required=False)
par.add_argument("--pkglist", default=None, nargs='+',
        help="packages list, connect everyone by espace.", required=False)

par.add_argument("-up", "--repo_rpms_update", default=False,
        help="update obs repo rpms. type bool, default False, \
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

par.add_argument("-latest", "--latest_info", default=False,
        help="store latest package info by branch to gitee repo obs_pkg_rpms, \
                type is bool, default False, should be with -b -guser -gpwd.", required=False)

par.add_argument("-cc", "--check_codes", default=False,
        help="check codes same or not between gitee and obs,should be with -b and -p", required=False)
par.add_argument("-cps", "--check_pkg_service", default=False,
        help="check if there are any problems with the content of the _service file in the rpm package", required=False)
par.add_argument("-at", "--access_token", default=False,
        help="gitee access_token number used for api get", required=False)
par.add_argument("-prid", "--pr_id", default=False,
        help="use the pr_id to get this pullrequest", required=False)
par.add_argument("-sc", "--sync_code", default=True,
        help="when adding package to project or changing package project, \
                the code should be synchronized. type bool, default True", required=False)
par.add_argument("-sgo", "--sync_gitee_to_obs", default=None,
        help="when you want to sync not only one rpm please let this be true --sync_gitee_to_obs=true", required=False)

par.add_argument("-gld", "--get_latest_date", default=None,
        help="get the latest git date to obs_pkg_rpms --get_latest_date=true", required=False)
par.add_argument("-omn", "--obs_mail_notice", default=False,
        help="obs mail notice to package owner --obs_mail_notice=true", required=False)
par.add_argument("-fa", "--from_addr", default=None,
        help="email sender", required=False)
par.add_argument("-fap", "--from_addr_pwd", default=None,
        help="email sender password", required=False)
par.add_argument("-ca", "--cc_addr", default=None,
        help="cc's email", required=False)
par.add_argument("-pm", "--pckg_mgmt", default=False,
        help="synchronize the obs_meta file according to the pckg-mgmt.yaml file", required=False)
par.add_argument("-rm", "--remt", default=None,
        help="Local path of release-management repository.", required=False)
par.add_argument("-a", "--ALL_", default=False, help="update all obs repo rpms", required=False)

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
        "check_yaml": args.check_yaml,
        "check_meta": args.check_meta,
        "pkglist": args.pkglist,

        "repo_rpms_update": args.repo_rpms_update,
        "repo": args.repo,
        "arch": args.arch,
        "repo_server_ip": args.repo_server_ip,
        "repo_server_user": args.repo_server_user,
        "repo_server_port": args.repo_server_port,
        "repo_server_pwd": args.repo_server_pwd,

        "latest_info": args.latest_info,
        "check_codes": args.check_codes,
        "check_pkg_service": args.check_pkg_service,
        "access_token": args.access_token,
        "pr_id": args.pr_id,
        "sync_code": args.sync_code,
        "all": args.ALL_,
        "sync_gitee_to_obs": args.sync_gitee_to_obs,
        "get_latest_date": args.get_latest_date,
        "from_addr": args.from_addr,
        "from_addr_pwd": args.from_addr_pwd,
        "cc_addr": args.cc_addr,
        "obs_mail_notice": args.obs_mail_notice,
        "pckg_mgmt": args.pckg_mgmt,
        "release_management_path": args.remt
        }

run = Runner(**kw)
run.run()
