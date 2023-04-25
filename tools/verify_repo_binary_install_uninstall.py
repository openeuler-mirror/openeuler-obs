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
# Create: 2022-06-28
# ******************************************************************************
"""
verify project repo binary install and uninstall
"""

import os
import sys
import yaml
import shutil
import argparse
import subprocess
import smtplib
from email.mime.text import MIMEText
from email.header import Header

par = argparse.ArgumentParser()
par.add_argument("-rp", "--repo_project", default=None,
        help="set repo obs project name", required=True)
par.add_argument("-br", "--branch", default=None,
        help="branch name", required=True)
par.add_argument("-cp", "--check_project", default=None,
        help="will check obs project name", required=False)
par.add_argument("-a", "--arch", default=None,
        help="architecture name", required=True)
par.add_argument("-ip", "--obs_ip", default=None,
        help="obs server ipaddress", required=True)
par.add_argument("-eu", "--email_user", default=None,
        help="email user name", required=True)
par.add_argument("-epwd", "--email_passwd", default=None,
        help="email user password", required=True)
par.add_argument("-tu", "--to_addr", default=None,
        help="recive email user", required=True)
args = par.parse_args()

install_dir = "/tmp/check_install"
yum_file = "/etc/yum.repos.d/openEuler.repo"


def run_cmd(cmd):
    """
    run shell cmd
    """
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, encoding="utf-8")
    out, err = p.communicate()
    return out, err

def write_yum_repo():
    """
    write yum repofile
    """
    with open(yum_file, "w") as f:
        for p in args.repo_project.split():
            name = p.replace(':', '-')
            url = "http://%s:82/%s/standard_%s" % (args.obs_ip, 
                    p.replace(':', ':/'), args.arch)
            file_content = """
[%s]
name=%s
baseurl=%s
enabled=1
gpgcheck=0
""" % (name, name, url)
            f.write(file_content)
    ret = os.system("cat %s" % yum_file)

def read_yaml(file_path):
    """
    read yaml file
    """
    file_msg = {}
    if os.path.exists(file_path):
        with open(file_path, "r", encoding='utf-8') as f:
            file_msg = yaml.load(f, Loader=yaml.SafeLoader)
    return file_msg

def get_project_packages():
    """
    get project package dict
    """
    project_packages = {}
    if args.check_project:
        project_list = args.check_project.split(",")
    else:
        project_list = os.listdir(os.path.join(os.getcwd(), "config/%s" % args.branch))
    for p in project_list:
        pkglist = []
        yaml_file = os.path.join(os.getcwd(), "config/%s/%s/to_check.yaml" % 
                (args.branch, p))
        file_msg = read_yaml(yaml_file, Loader=yaml.SafeLoader)
        if file_msg:
            if file_msg["packages"]:
                for pkg in file_msg['packages']:
                    pkglist.append(pkg['name'])
            project_packages[p] = pkglist
        else:
            print("[WARNING]: %s %s don't have yaml file, will not check!" % (args.branch, p))
    return project_packages

def search_source_rpm(bin_rpm):
    """
    search bin rpm source rpm
    """
    source_rpm = None
    cmd = "dnf repoquery --source %s 2>/dev/null | grep -v \"none\" | head -n1" % bin_rpm
    res = os.popen(cmd).read()
    if res:
        for line in res.split('\n'):
            if "src.rpm" in line:
                source_rpm = line.rsplit('-', 2)[0]
                break
    else:
        print("search %s source rpm failed" % bin_rpm)
    return source_rpm

def get_problems(err, form):
    """
    parse error log
    """
    rpm_msg = []
    if ("Problem" not in err) and ("No package" not in err):
        return rpm_msg
    err_list = []
    for line in err.splitlines():
        rpm = ""
        tmp = {}
        if line in err_list:
            continue
        err_list.append(line)
        if "requires" in line and "package" in line:
            rpm = line.split(" package ")[1].split("requires")[0].strip()
        if "needed by" in line:
            rpm = line.split("needed by")[1].strip()
        if "obsoletes" in line:
            rpm = line.split("provided by")[1].strip()
        if rpm:
            bin_rpm = rpm.rsplit('-', 2)[0]
            source_rpm = search_source_rpm(bin_rpm)
            tmp["bin_rpm"] = bin_rpm
            tmp["source_rpm"] = source_rpm
            tmp["type"] = form
            tmp["err_info"] = line 
            rpm_msg.append(tmp)
    return rpm_msg

def install_uninstall(check_rpmlist, sys_rpmlist, project):
    """
    rpms install and uninstall
    """
    final_msg = []
    if not check_rpmlist:
        return final_msg
    install_rpms = []
    install_remove_rpms = []
    for rpms in check_rpmlist:
        if rpms in sys_rpmlist:
            install_rpms.append(rpms)
        else:
            install_remove_rpms.append(rpms)
    if os.path.exists(install_dir):
        shutil.rmtree(install_dir)
    max_num = 3000
    if install_rpms:
        for i in range(0, len(install_rpms), max_num):
            part_install_rpms = install_rpms[i:i+max_num]
            rpms = " ".join(part_install_rpms)
            cmd = "yum install -y %s --installroot=%s" % (rpms, install_dir)
            out, err = run_cmd(cmd)
            print(out)
            if ("Complete!" in out) and ("Installed:" in out):
                print("[INFO]: Check Install system_rpm %s %s succeed!" % (project, rpms))
            else:
                print(err)
                print("[ERROR]: Check Install system_rpm %s %s failed!" % (project, rpms))
                msg = get_problems(err, "Install")
            if msg:
                final_msg.extend(msg)
        if os.path.exists(install_dir):
            shutil.rmtree(install_dir)
    if install_remove_rpms:
        for i in range(0, len(install_remove_rpms), max_num):
            part_install_remove_rpms = install_remove_rpms[i:i+max_num]
            rpms = " ".join(part_install_remove_rpms)
            cmd = "yum install -y %s" % rpms
            out, err = run_cmd(cmd)
            print(out)
            if ("Complete!" in out) and ("Installed:" in out):
                print("[INFO]: Check Install %s %s succeed!" % (project, rpms))
                cmd = "yum remove -y %s" % rpms
                out, err = run_cmd(cmd)
                print(out)
                if ("Complete!" in out) and ("Removed:" in out):
                   print("[INFO]: Check Remove %s %s succeed!" % (project, rpms))
                elif "protected packages" in err:
                    print(err)
                    print("[WARNING]: %s %s unable to remove!" % (project, rpms))
                else:
                    print(err)
                    print("[ERROR]: Check Remove %s %s failed!" % (project, rpms))
            else:
                print(err)
                print("[ERROR]: Check Install %s %s failed!" % (project, rpms))
                msg = get_problems(err, "Install")
                if msg:
                    final_msg.extend(msg)
    return final_msg

def check(project_packages):
    """
    check packages rpms
    """
    final_msg = {}
    if not project_packages:
        return final_msg
    cmd = "yum list --installed | grep '@anaconda' | grep '%s' |\
            awk -F. '{print $1}'" % args.arch
    out, err = run_cmd(cmd)
    sys_rpmlist = out.split()
    for proj,pkgs in project_packages.items():
        rpmlist = []
        repo = proj.replace(':', '-')
        if pkgs:
            for p in pkgs:
                cmd = "osc ls -b %s %s standard_%s %s 2>/dev/null | grep 'rpm' | \
                        grep -v 'src.rpm'" % (proj, p, args.arch, args.arch)
                ret = os.popen(cmd).read().split()
                for p in ret:
                    rpmlist.append(p.rsplit('-', 2)[0])
        else:
            cmd = "yum list --repo %s --available | grep -E '%s|noarch' | grep -v '.src' | \
                    awk -F. '{print $1}'" % (repo, args.arch)
            rpmlist = os.popen(cmd).read().split()
        if rpmlist:
            ret = install_uninstall(rpmlist, sys_rpmlist, proj)
            if ret:
                final_msg[proj] = ret
    return final_msg

def write_email(file_msg):
    """
    write email msg
    """
    msg = ""
    line = ""
    for proj, err_list in file_msg.items():
        for tmp in err_list:
            line = line + """
            <tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>
            """ % (proj, args.arch, tmp["bin_rpm"], tmp["source_rpm"], tmp["type"], 
                    tmp["err_info"])
            msg = """ 
    <p>检查OBS工程%s软件包的安装卸载，问题如下：</p>
    <table border=8>
    <tr><th>工程名</th><th>架构</th><th>二进制包名</th><th>源码包名</th><th>错误类型</th><th>原因</th></tr>
    %s
    </table>
    <p>请尽快解决，谢谢~^V^~!!!</p>
    """ % (args.check_project, line)
    return msg

def send_email(message):
    """
    send email
    """
    msg = MIMEText(message, 'html')
    msg['Subject'] = Header("[Project Package Install Notice]", "utf-8")
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

write_yum_repo()
prj_pkg_dict = get_project_packages()
check_result = check(prj_pkg_dict)
if check_result:
    email_msg = write_email(check_result)
    send_email(email_msg)
