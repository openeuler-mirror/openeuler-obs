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
# Author: wangchong
# Create: 2022-06-23
# ******************************************************************************
"""
check project package binary archive complete
"""

import os
import sys
import yaml
import shutil
import argparse
import paramiko
import smtplib
from email.mime.text import MIMEText
from email.header import Header

par = argparse.ArgumentParser()
par.add_argument("-p", "--project", default=None, help="obs project name", required=True)
par.add_argument("-dp", "--dep_project", default=None,
                help="obs binary dependent project, example:openEuler:selfbuild:BaseOS", required=True)
par.add_argument("-dr", "--dep_repo", default=None,
                help="dependent repo name, example:mainline_standard_aarch64", required=True)
par.add_argument("-a", "--arch", default=None,
                help="architecture name, example:aarch64", required=True)
par.add_argument("-ip", "--obs_ip", default=None, help="obs server ipaddress", required=True)
par.add_argument("-ou", "--obs_user", default=None, help="obs server user", required=True)
par.add_argument("-opwd", "--obs_password", default=None, help="obs server password", required=True)
par.add_argument("-eu", "--email_user", help="email user name", required=True)
par.add_argument("-epwd", "--email_passwd", help="email user password", required=True)
par.add_argument("-tu", "--to_addr", help="recive email user", required=True)
args = par.parse_args()

branch = args.project.replace(":", "-")
gitee_repo_path = os.path.join(os.getcwd(), "obs_pkg_rpms")
yaml_file = os.path.join(gitee_repo_path, "repo_files", "%s_%s.yaml" % (branch, args.arch))
full_path = os.path.join("/srv/obs/build", args.dep_project, args.dep_repo, args.arch, ":full")


def git_clone():
    """
    git clone gitee repo
    """
    if os.path.exists(gitee_repo_path):
        shutil.rmtree(gitee_repo_path)
    git_url = "https://gitee.com/openeuler_latest_rpms/obs_pkg_rpms.git"
    cmd = "git clone --depth 1 %s" % git_url
    for i in range(5):
        if os.system(cmd) != 0:
            print("[ERROR]: Git clone failed, try again...")
        else:
            print("[INFO]: Git clone succeed!")
            break
    if not os.path.exists(gitee_repo_path):
        sys.exit(1)

def read_yaml():
    """
    read yaml file
    """
    rpmlist = []
    if os.path.exists(yaml_file):
        with open(yaml_file, "r", encoding='utf-8') as f:
            file_msg = yaml.load(f, Loader=yaml.FullLoader)
        for rpm in file_msg.values():
            rpmlist.extend(rpm)
    shutil.rmtree(gitee_repo_path)
    return rpmlist

def get_server_rpmlist():
    """
    get obs server dependent repos binary list
    """
    pmk = paramiko.SSHClient()
    key = paramiko.AutoAddPolicy()
    pmk.set_missing_host_key_policy(key)
    pmk.connect(args.obs_ip, "22", args.obs_user, args.obs_password, timeout=5)
    cmd = "cd %s && ls *.rpm | grep -v 'src.rpm'" % full_path
    stdin, stdout, stderr = pmk.exec_command(cmd)
    error_msg = stderr.readlines()
    if len(error_msg) > 0:
        print(error_msg)
        sys.exit(1)
    server_rpmlist = []
    for line in stdout.readlines():
        server_rpmlist.append(line.replace("\n", ""))
    return server_rpmlist

def rpm_exist(rpmlist, server_rpmlist):
    """
    check rpms archive
    """
    notfind = []
    for rpm in rpmlist:
        if rpm and rpm.endswith(".rpm") and rpm not in server_rpmlist:
            notfind.append(rpm)
    if notfind:
        msg = "<p>%s %s some binary not archived into %s as follows:</p>" %(
                args.project, args.arch, full_path)
        print(msg)
        for line in notfind:
            msg = msg + "<br>%s" % line
            print(line)
        return msg
    else:
        print("[INFO]: %s %s all binary archived into %s are no missing."
                % (args.project, args.arch, full_path))
        sys.exit(0)

def send_email(message):
    """
    send email
    """
    msg = MIMEText(message, 'html')
    msg['Subject'] = Header("[Check %s Project Binary Archive]" % args.project, "utf-8")
    msg['From'] = Header(args.email_user)
    msg['To'] = Header(args.to_addr)
    smtp_server = "smtp.163.com"
    try:
        server = smtplib.SMTP_SSL(smtp_server)
        server.login(args.email_user, args.email_passwd)
        server.sendmail(args.email_user, args.to_addr.split(','), msg.as_string())
        server.quit()
        print("[INFO]: send email succeed!")
    except smtplib.SMTPException as e:
        raise SystemExit("send email failed, reason:%s" % e)

def check_binary_archive():
    if args.arch not in args.dep_repo:
        print("[ERROR]: %s and %s are not match." % (args.dep_repo, args.arch))
        sys.exit(1)
    git_clone()
    rpmlist = read_yaml()
    server_rpmlist = get_server_rpmlist()
    msg = rpm_exist(rpmlist, server_rpmlist)
    if msg:
        send_email(msg)
        sys.exit(1)

check_binary_archive()
