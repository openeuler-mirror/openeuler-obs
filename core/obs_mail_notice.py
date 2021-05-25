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
        self.to_addr_list = []

    def _get_proj_status(self, proj, status):
        """
        get proj build results
        """
        cmd = "osc r --csv %s 2>/dev/null | grep %s | awk -F ';' '{print $1}'" % (proj, status)
        self.failed_pkglist = [x for x in os.popen(cmd).read().split('\n') if x != '']
        log.info("%s build %s packages:%s" % (proj, status, self.failed_pkglist))
    
    def _get_pkg_owner_email(self, proj, pkg, status):
        """
        get the email address of the package owner
        """
        log.info("Begin to get package %s owner email..." % pkg)
        _tmpdir = os.popen("mktemp -d").read().strip('\n')
        pkg_path = os.path.join(_tmpdir, proj, pkg)
        cmd = "cd %s && osc co %s %s &>/dev/null && cd %s && osc up -S &>/dev/null" % (
                _tmpdir, proj, pkg, pkg_path)
        if os.system(cmd) == 0:
            cmd = "cd {0} && grep -A 1 \"%changelog\" *.spec | grep \"@\" && cd -".format(
                    pkg_path)
            email = os.popen(cmd).read()
            if email:
                try:
                    to_addr = re.findall(r"<(.+?)>", email)[0]
                except IndexError:
                    to_addr = self.cc_addr.split(',')[0]
            else:
                to_addr = self.cc_addr.split(',')[0]
            log.info("Get package %s email succeed!" % pkg)
            shutil.rmtree(_tmpdir)
        else:
            log.info("osc co %s %s failed!" % (proj, pkg))
            to_addr = self.cc_addr.split(',')[0]
            log.info("Get package %s email failed, will use leader email." % pkg)
            shutil.rmtree(_tmpdir)
        if "buildteam" in to_addr:
            to_addr = self.cc_addr.split(',')[0]
        tmp = {"proj": proj, "pkg": pkg, "owner_email": to_addr, "status": status}
        self.to_addr_list.append(tmp)

    def _edit_email_content(self):
        """
        edit email content
        """
        line = ""
        for tmp in self.to_addr_list:
            proj_url = "https://build.openeuler.org/project/show/%s" % tmp["proj"]
            pkg_url = "https://build.openeuler.org/package/show/%s/%s" % (tmp["proj"], tmp["pkg"])
            line = line + """
            <tr><td><a href = "%s">%s</a></td><td><a href = "%s">%s</a></td><td>%s</td><td>%s</td></tr>
            """ % (proj_url, tmp["proj"], pkg_url, tmp["pkg"], tmp["status"], tmp["owner_email"])
        message = """
        <p>Hello:</p>
        <style>a{TEXT-DECORATION:none}</style>
        <table border=8>
        <tr><th>OBS_PROJECT</th><th>PACKAGE</th><th>BUILD_RESULT</th><th>RESPONSIBLE_PERSON_EMAIL</th></tr>
        %s
        </table>
        <p>Please solve it as soon as possible.</p>
        <p>Thanks ~^v^~ !!!</p>
        """ % line
        return message

    def _send_email(self, message):
        """
        send a email
        """
        msg = MIMEText(message, 'html')
        msg['Subject'] = Header("[OBS Package Build Failed Notice]", "utf-8")
        msg["From"] = Header(self.from_addr)
        to_addr = ""
        for tmp in self.to_addr_list:
            if not to_addr:
                to_addr = tmp["owner_email"]
            else:
                if tmp["owner_email"] not in to_addr:
                    to_addr = to_addr + "," + tmp["owner_email"]
        msg["To"] = Header(to_addr)
        msg["Cc"] = Header(self.cc_addr)
        smtp_server = "smtp.163.com"
        try:
            server = smtplib.SMTP_SSL(smtp_server)
            server.login(self.from_addr, self.from_addr_pwd)
            server.sendmail(self.from_addr, to_addr.split(',') + self.cc_addr.split(','), msg.as_string())
            server.quit()
            return 0
        except smtplib.SMTPException as e:
            return e
    
    def notify_all_respon_person(self):
        """
        notice all packages to person
        """
        status_list = ["failed", "unresolvable"]
        for status in status_list:
            for proj in self.proj.split(','):
                self._get_proj_status(proj, status)
                if self.failed_pkglist:
                    with ThreadPoolExecutor(10) as executor:
                        for pkg in self.failed_pkglist:
                            executor.submit(self._get_pkg_owner_email, proj, pkg, status)
        message = self._edit_email_content()
        ret = self._send_email(message)
        if ret == 0:
            log.info("send email succeed !")
        else:
            log.error("send email failed, Error:%s" % ret)


if __name__ == "__main__":
    kw = {"from_addr":sys.argv[1], "from_addr_pwd":sys.argv[2], 
            "cc_addr":sys.argv[3], "project":sys.argv[4]}
    omn = ObsMailNotice(**kw)
    omn.notify_all_respon_person()
