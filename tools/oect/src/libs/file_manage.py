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
# Create: 2021-07-09
# ******************************************************************************/
import sys
sys.path.append('/home/oect')
import os
import hashlib
import shutil
from src.libs.logger import logger

def get_md5(filename):
    """
    @description : get md5 value of file
    -----------
    @param : filename
    -----------
    @returns :
    -----------
    """
    if not os.path.isfile(filename):
        logger.error(f"{filename} is not file")
        return '00000000'

    md5_hash = hashlib.md5()
    with open(filename,'rb') as file:
        while True:
            data = file.read(4096)
            if not data:
                break
            md5_hash.update(data)
    return md5_hash.hexdigest()

def mv_files(from_path, target_path, file_name = None):
    """
    @description : mv files in {from_path} to {target_path}
    -----------
    @param : from_path, target_path
    -----------
    @returns :
    -----------
    """
    def update_file(from_path, target_path, new_file):
        target_file_path=os.path.join(target_path, new_file) # 定义文件在目标目录的绝对路径 
        # 如果文件在目标文件夹中，则删除该文件
        if os.path.exists(target_file_path):
            logger.warning(f"{new_file} already in {target_path}, delete first")
            os.remove(target_file_path)
        shutil.move(os.path.join(from_path, new_file), target_path)
        return True

    if not os.path.isdir(target_path): # 若目标目录不存在，直接创建
        os.mkdir(target_path)

    if file_name is None: # 如果file_name 为None，默认即将移动from_path下的所有文件
        names = os.listdir(from_path)
        for i, name in enumerate(names):
            update_file(from_path, target_path, name)
    else:
        update_file(from_path, target_path, file_name)
    logger.info(f"move files from {from_path} to {target_path} successfully!")
    return True

def copy_file(from_path, target_path):
    """
    from_path: 源文件绝对路径
    target_path: 目的文件夹
    """
    file_name = ""
    if os.path.isfile(from_path):
        dir_name, file_name = os.path.split(from_path)
        target_file_path=os.path.join(target_path, file_name)

        # 判断目的文件夹有同名文件
        if os.path.isfile(target_file_path):
            logger.info(f"{file_name} already in {target_path}")
            if get_md5(from_path) != get_md5(target_file_path):
                shutil.copy(from_path, target_file_path)
        else:
            if os.path.exists(target_path):
                shutil.copy(from_path, target_path)
    else:
        logger.error(f"{from_path} is not file")
        return False
    
    return True