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
function for all
"""

import pexpect


def str_to_bool(s):
    """
    change string to bool
    """
    return s.lower() in ("yes", "true", "t", "1")


class Pexpect(object):
    """
    expect by python
    """
    def __init__(self, user, ip, passwd, port=None):
        """
        init connect message
        user: user for system
        ip: ip of the system
        port: port for connectiong by sshd
        """
        self.user = user
        self.ip = ip
        self.passwd = passwd
        self.port = port

    def _expect(self, process):
        for i in range(5):
            ret=process.expect(["(yes/no)", "Password", "password", pexpect.EOF, \
                    pexpect.exceptions.TIMEOUT], timeout=60)
            if ret == 0:
                process.sendline("yes\n")
            if ret == 1 or ret == 2:
                process.sendline("%s\n" % self.passwd)
                break
            if ret == 3 or ret == 4:
                break

    def ssh_cmd(self, cmd, timeout=30):
        """
        cmd: command will be runnd
        return: response of command
        """
        if self.port:
            cmd = "ssh -p %s %s@%s '%s'" % (self.port, self.user, self.ip, cmd)
        else:
            cmd = "ssh %s@%s '%s'" % (self.user, self.ip, cmd)
        print(cmd)
        process = pexpect.spawn(cmd, timeout=timeout)
        self._expect(process)
        msg = process.readlines()
        process.close()

        return msg

    def scp_file(self, src_file, dest_dir):
        """
        src_file:
        dest_dir:
        """
        if self.port:
            cmd = "scp -P %s %s %s@%s:%s" % (self.port, src_file, self.user, self.ip, dest_dir)
        else:
            cmd = "scp %s %s@%s:%s" % (src_file, self.user, self.ip, self.dest_dir)
        print(cmd)
        process = pexpect.spawn(cmd)
        self._expect(process)
        msg = process.readlines()
        process.close()

        return msg


if __name__ == "__main__":
    test = Pexpect("root", "127.0.0.1", "123456", port=2224)
    res = test.ssh_cmd("pwd")
    print(res)
    res = test.scp_file("./ip.txt", "~")
    print(res)
