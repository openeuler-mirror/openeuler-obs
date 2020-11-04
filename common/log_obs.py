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
logger for all scripts
"""
import os
import logging


def get_logger():
    """
    get logger object
    return: logger object
    """
    #log_path = os.path.join(os.path.split(os.path.realpath(__file__))[0], "../log")
    log_path = "log"
    if not os.path.exists(log_path):
        os.mkdir(log_path)
    elif not os.path.isdir(log_path):
        os.remove(log_path)
        os.mkdir(log_path)
    logfile = os.path.join(log_path, "openeuler-obs.log")
    logger = logging.getLogger("")
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - '\
            '%(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s')
    file_handler = logging.FileHandler(logfile, mode='w')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.DEBUG)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)
    logger.addHandler(file_handler)
    return logger


log = get_logger()


if __name__ == "__main__":
    log.debug("test")
