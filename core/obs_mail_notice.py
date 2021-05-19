#!/bin/env python3
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
# Create: 2021-05-19
# ******************************************************************************

"""
OBS mail notice
"""
import os
import re
import sys
import shutil
import smtplib
from email.mime.text import MIMEText
from email.header import Header
from concurrent.futures import ThreadPoolExecutor
from common.log_obs import log

class ObsMailNotice(object):
    """
    check obs proj pkg results and email notification
    """
    def __init__(self, **kwargs):
        """
        from_addr: email sender
        from_addr_pwd: email sender password
        cc_addr: cc's email
        proj: obs project name
        """
        self.kwargs = kwargs
        self.from_addr = self.kwargs["from_addr"]
        self.from_addr_pwd = self.kwargs["from_addr_pwd"]
        self.cc_addr = self.kwargs["cc_addr"]
        self.proj = self.kwargs["project"]
        self.failed_pkglist = []
        self.to_addr = ""

    def send_email(self, pkg):
        """
        send a email
        """
        proj_url = "https://build.openeuler.org/project/show/%s" % self.proj
        pkg_url = "https://build.openeuler.org/package/show/%s/%s" % (self.proj, pkg)
        message = '''
        <style>a{TEXT-DECORATION:none}</style>
        <p>Hello:</p>
        <table border=8>
        <tr><th>OBS_PROJECT</th><th>PACKAGE</th><th>BUILD_RESULT</th></tr>
        <tr><th><a href = "%s">%s</a></th><th><a href = "%s">%s</a></th><th>failed</th></tr>
        </table>
        <p>Please solve it as soon as possible.</p>
        <p>Thanks !!!</p>
        ''' % (proj_url, self.proj, pkg_url, pkg)
        msg = MIMEText(message, 'html')
        msg['Subject'] = Header("OBS Package Build Failed Notice", "utf-8")
        msg["From"] = Header(self.from_addr)
        msg["To"] = Header(self.to_addr)
        msg["Cc"] = Header(self.cc_addr)
        smtp_server = "smtp.163.com"
        try:
            server = smtplib.SMTP(smtp_server, 25)
            server.login(self.from_addr, self.from_addr_pwd)
            server.sendmail(self.from_addr, self.to_addr.split(',') + self.cc_addr.split(','), msg.as_string())
            server.quit()
            return 0
        except smtplib.SMTPException as e:
            return e

    def get_proj_status(self):
        """
        get proj build results
        """
        cmd = "osc r --csv %s 2>/dev/null | grep failed | awk -F ';' '{print $1}'" % self.proj
        self.failed_pkglist = [x for x in os.popen(cmd).read().split('\n') if x != '']
        log.info("%s build failed packages:%s" % (self.proj, self.failed_pkglist))
    
    def get_pkg_owner_email(self, pkg):
        """
        get the email address of the package owner
        """
        log.info("Begin to get package %s owner email..." % pkg)
        _tmpdir = os.popen("mktemp -d").read().strip('\n')
        pkg_path = os.path.join(_tmpdir, self.proj, pkg)
        cmd = "cd %s && osc co %s %s &>/dev/null && cd %s && osc up -S &>/dev/null" % (
                _tmpdir, self.proj, pkg, pkg_path)
        if os.system(cmd) == 0:
            cmd = "cd {0} && grep -A 1 \"%changelog\" *.spec | grep \"@\" && cd -".format(
                    pkg_path)
            email = os.popen(cmd).read()
            if email:
                try:
                    self.to_addr = re.findall(r"<(.+?)>", email)[0]
                except IndexError:
                    self.to_addr = self.cc_addr.split(',')[0]
            else:
                self.to_addr = self.cc_addr.split(',')[0]
            log.info("Get package %s email succeed!" % pkg)
            shutil.rmtree(_tmpdir)
        else:
            log.info("osc co %s %s failed!" % (self.proj, pkg))
            self.to_addr = self.cc_addr.split(',')[0]
            log.info("Get package %s email failed, will use leader email." % pkg)
            shutil.rmtree(_tmpdir)

    def notify_respon_person(self, pkg):
        """
        notice a package to person
        """
        self.get_pkg_owner_email(pkg)
        ret = self.send_email(pkg)
        if ret == 0:
            log.info("send %s email succeed !" % pkg)
        else:
            log.error("send %s email failed, Error:%s" % (pkg, ret))

    def notify_all_respon_person(self):
        """
        notice all packages to person
        """
        self.get_proj_status()
        with ThreadPoolExecutor(10) as executor:
            for pkg in self.failed_pkglist:
                executor.submit(self.notify_respon_person, pkg)


if __name__ == "__main__":
    kw = {"from_addr":sys.argv[1], "from_addr_pwd":sys.argv[2], 
            "cc_addr":sys.argv[3], "project":sys.argv[4]}
    omn = ObsMailNotice(**kw)
    omn.notify_all_respon_person()
