#! /usr/bin/env python
# coding=utf-8
# ******************************************************************************
# Copyright (c) Huawei Technologies Co., Ltd. 2020-2020. All rights reserved.
# licensed under the Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#     http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY OR FIT FOR A PARTICULAR
# PURPOSE.
# See the Mulan PSL v2 for more details.
# Author: senlin
# Create: 2022-02-14
# ******************************************************************************/

import re
import csv
import smtplib
from email.mime.text import MIMEText
from email.header import Header
from src.libs.logger import logger
from src.config import global_config
from  src.libs.csvrw import CSVRW

# config of sender
EMAIL='13813374731@163.com'
PASS='SJSJAISTRUWXFETI'
SMTP_SERVER = 'smtp.163.com'


class SendEmail(object):
    """
    email sendor
    """
    cc = global_config.cc_email
    to = global_config.to_email
    def  __init__(self):
        """
        @description :
        -----------
        @param :
        -----------
        @returns :
        -----------
        """
        


    @classmethod
    def send_email(cls, message, subject):
        """
        send a email

        args:
            message: Message body
        returns:
            True: send email normally
            False: Abnormal email sending feedback
        """
        sender_email = EMAIL
        sender_email_pass = PASS
        # cc_emails = self.cc.get('email').split(',')
        # to_emails = self.to.get('email').split(',')
        to_emails = []
        to_emails.extend(cls.cc)
        to_emails.extend(cls.cc)


        msg = MIMEText(message, 'html')
        msg['Subject'] = Header(subject, "utf-8")
        msg["From"] = Header(EMAIL)
        msg["To"] = Header(";".join(cls.cc))
        msg["Cc"] = Header(";".join(cls.to))

        try:
            server = smtplib.SMTP_SSL(SMTP_SERVER)
            server.login(sender_email, sender_email_pass)
            server.sendmail(sender_email, to_emails, msg.as_string())
            server.quit()
            logger.info("send email succeed !")
            return True
        except smtplib.SMTPException as err:
            logger.error(f"send email failed: {err.strerror}!")
            return False
            
    @staticmethod
    def edit_email_content(csv_file, csv_title=None):
        """
        edit email content
        Args:
            input_dict
        Returns:
            message:
        """
        # CSVRW.get_object_type()
        csv_data, csv_title = CSVRW.read_2_dict(csv_file, 'gbk')
        if not csv_data or not csv_title:
            logger.warning("Invalid input csv file")
            return None

        title = """<tr>"""
        for key in csv_title:
            title += """<th>%s</th>""" % (key)
        title += """</tr>"""

        line = ""
        for main_key, main_value in csv_data.items():
            new_line = """<tr>"""
            new_line += """<td>%s</td>""" % (main_key)

            for __, sub_value in main_value.items():
                new_line += """<td>%s</td>""" % (sub_value)
            new_line += """</tr>"""

            line = line + new_line
            
        message = """
        <p>Hello:</p>
        <style>a{TEXT-DECORATION:none}</style>
        <table border=8>
        %s
        %s
        </table>
        <p>Please solve it as soon as possible.</p>
        <p>Thanks ~^v^~ !!!</p>
        """ % (title, line)

        return message


    def _check_email(self):
        """
        Verify and keep the legal email address

        returns:
            valid_email: legal email address
        """
        valid_email = set()
        for origin_email in self.to_email:
            try:
                regular = re.compile(r'[0-9a-zA-Z\.]+@[0-9a-zA-Z\.]+[com, org]')
                email = re.findall(regular, origin_email)[0]
                if email:
                    valid_email.add(email)
            except IndexError as e:
                logger.error(f"analyse developer for {email} failed")
        return list(valid_email)

