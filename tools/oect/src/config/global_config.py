#!/usr/bin/python3
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
# ******************************************************************************/
"""
Global environment variable value when the tool is running
"""

import os

# oect top dir
LIBS_CONFIG_FOLDER = os.path.abspath(os.path.dirname(__file__))
# path of user-agent.json
USER_AGENT_JSON = f'{LIBS_CONFIG_FOLDER}/user-agent.json'
# gitee api config
GITEE_API_CONFIG = f'{LIBS_CONFIG_FOLDER}/gitee_api_config.yaml'
# gitee memebers id
GITEE_OPENEULER_MEMBERS_ID_YAML = f'{LIBS_CONFIG_FOLDER}/oe_memebers_id.yaml'

# OBS 实时日志链接
DEFAULT_OSCRC_APIURL = "https://build.openeuler.org"
OBS_PROJECT_LIVE_LOG= DEFAULT_OSCRC_APIURL + "/package/live_build_log/{obs_project}/{package}/{repo}/{arch}"


# 抄送人邮箱账号信息
cc_email='xiasenlin1@huawei.com'

# 收件人邮箱账号信息
to_email='dev@openeuler.org'
