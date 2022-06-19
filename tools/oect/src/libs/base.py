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
# Create: 2022-03-17
# ******************************************************************************/

import codecs
import csv
import requests
from requests.sessions import Session
from retrying import retry
from fake_useragent import UserAgent
from src.config import constant
from src.config import global_config
from src.libs.logger import logger
from src.libs.file_manage import mv_files
from src.libs.file_manage import copy_file
from src.libs.executecmd import ExecuteCmd


def update_yum_repo():
    """
    yum clean all and yum makecache
    Args:
    
    Returns:
    
    """

    ExecuteCmd.cmd_status(["yum", "clean", "all"])
    ExecuteCmd.cmd_status(["yum", "makecache"])

def set_repo(chosed_repo_file, branch):
    """
    Back up the repo directory and configure a new repo

    Args:
        chosed_repo_file: the new repo file for usage
        branch: branch related to the chosed_repo_file
    Returns:
    
    """

    repo_path = constant.REPO_PATH
    from_repo =f"{global_config.LIBS_CONFIG_FOLDER}/{chosed_repo_file}"
    back_repo_path = constant.BACK_REPO_PATH
    if not mv_files(repo_path, back_repo_path):
        logger.error("back repo file to temprepo failed!")
        return False
    if not copy_file(from_repo, repo_path):
        logger.error(f"set the repo cofigfile: {from_repo} failed!")
        return False

    if chosed_repo_file == constant.OE_REPO: # no more update
        return True

    new_repo_path = f"{repo_path}/{chosed_repo_file}" # 初始repo文件拷贝到repo_path目录下
    projects = constant.GITEE_BRANCH_PROJECT_MAPPING[branch] # 获取 
    with open(new_repo_path, "a+") as file:   #”w"代表着每次运行都覆盖内容
        for pj in projects:
            file.write("\n")
            repo = constant.OE_PROJECT_REALTIME_REPO[pj] # 获取映射的project repo URL列表
            file.write("[" + repo['name'] + "]"+"\n")
            repo_name = f"name={repo['name']}"
            file.write(repo_name + "\n")
            repo_baseurl = f"baseurl={repo['baseurl']}"
            file.write(repo_baseurl + "\n")
            repo_enable = f"enabled={repo['enabled']}"
            file.write(repo_enable + "\n")
            repo_gpgcheck = f"gpgcheck={repo['gpgcheck']}"
            file.write(repo_gpgcheck + "\n")

    update_yum_repo()
    return True

class http:
    """
    http的相关请求
    """

    def __init__(self) -> None:
        self.user_agent = UserAgent(path=global_config.USER_AGENT_JSON)
        self._request = Session()

    def __enter__(self):
        self.set_request(request=self._request)
        return self

    def __exit__(self, *args):
        self._request.close()

    def set_request(self, request):
        """
        set header info

        Args:
            request

        Returns:
        
        """

        request.headers.setdefault("User-Agent", self.user_agent.random)
        return request

    @retry(stop_max_attempt_number=3, stop_max_delay=1500)
    def _get(self, url, params=None, **kwargs):
        try:
            response = self._request.request(method="get", url=url, params=params, **kwargs)
        except requests.exceptions.ConnectionError as err:
            logger.error(err)
            logger.error("Failed to establish a new connection: [Errno 111] Connection refused')")
            return None
        if response.status_code != 200:
            if response.status_code == 410:
                logger.warning("Please check the token!")
            logger.error(response.text)
            raise requests.HTTPError("")
        return response
    
    @retry(stop_max_attempt_number=3, stop_max_delay=1500)
    def _post(self, url, data, **kwargs):
        response = self._request.request(method="post", url=url, data=data, **kwargs)
        if response.status_code not in [200, 201]:
            logger.error(response)
            raise requests.HTTPError("")
        return response

    @classmethod
    def get(cls, url, params=None, **kwargs):
        """
        get  request

        Args:
            url: url of post request
            params: params of post request
        
        Returns:
            response
        
        """
        
        """http的get请求"""
        with cls() as _self:
            try:
                get_method = getattr(_self, "_get")
                response = get_method(url=url, params=params, **kwargs)
            except requests.HTTPError:
                response = requests.Response()
        return response
    
    @classmethod
    def post(cls, url, data, **kwargs):
        """
        post request

        Args:
            url: url of post request
            data: data of post request

        Returns:
            response
        
        """
        
        with cls() as _self:
            try:
                get_method = getattr(_self, "_post")
                response = get_method(url=url, data=data, **kwargs)
            except requests.HTTPError:
                response = requests.Response()
        return response
