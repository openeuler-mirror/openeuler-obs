#!/bin/env python3
# -*- encoding=utf-8 -*-
"""
# ********************************************************************
# Copyright (c) Huawei Technologies Co., Ltd. 2021-2021. All rights reserved.
# [openeuler-jenkins] is licensed under the Mulan PSL v1.
# You can use this software according to the terms and conditions of the Mulan PSL v1.
# You may obtain a copy of Mulan PSL v1 at:
#     http://license.coscl.org.cn/MulanPSL
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY OR FIT FOR A PARTICULAR
# PURPOSE.
# See the Mulan PSL v1 for more details.
# Author: wangge
# Create: 2021-10-29
# ********************************************************************
"""


# oect的上层目录
RUN_DIRECTORY = "/home"

# 存放配置文件repo的目录
CONFIG = f"{RUN_DIRECTORY}/oect/src/config"
REPO_PATH = "/etc/yum.repos.d"
BACK_REPO_PATH = "/etc/yum.repos.d/temprepos"
OE_REPO = "huawei.repo"
RT_REPO = "realtime.repo"
ORI_REPO = "openEuler.repo"

# 当前用户的obs主页
OBS_OWN_HOME = "https://build.openeuler.org/user/show/senlin"
# OBS 实时日志链接
OBS_PROJECT_LIVE_LOG= "https://build.openeuler.org/package/live_build_log/{obs_project}/{package}/{repo}/{arch}"
# OBS 账号
ACCOUNT = "senlin"
# OBS主页
# OBS_HOST = "https://build.openeuler.org/"
OBS_HOST = "http://117.78.1.88/"
# openeuler dailybuild
DAILYBUILD_URL = "http://121.36.84.172/dailybuild/{branch}/{repo_dir}/Packages"
OPENEULER_REPO_URL = 'https://repo.huaweicloud.com/openeuler/{branch}/{repo_dir}/Packages'

SIGS_YAML_URL = 'https://gitee.com/openeuler/community/raw/master/sig/sigs.yaml'
SIG_OWNER_URL = 'https://gitee.com/openeuler/community/raw/master/sig/{signame}/OWNERS'
SPEC_URL = 'https://gitee.com/src-openeuler/{package}/raw/{branch}/{specfile}'
LOCAL_REPO_EXCEP = f'{RUN_DIRECTORY}/oect/src/config/pdfs.yaml'
LOCAL_SIGS = '/root/community/sig/'
LOCAL_SIGS_OWNERS = LOCAL_SIGS + '{signame}/sig-info.yaml'
LOCAL_OPENEULER_OWNERS = f'{CONFIG}/openEuler-owner.csv'

# check_rpm_install_dependence log url
CHECK_RPM_INSTALL_DEPENDENCE = 'https://jenkins.openeuler.org/job/openEuler-OS-build/job/check_rpm_install_dependence_{arch}/{num}/consoleFull'

# oemaker rpmlist.xml url
OEMAKER_RPMLIST_XML_PATH = 'https://gitee.com/src-openeuler/oemaker/raw/{branch}/rpmlist.xml'

# openeuler branch bind with obs project
GITEE_BRANCH_PROJECT_MAPPING = {
    "master": ["openEuler:Mainline", "openEuler:Epol"],
    # "master": ["bringInRely", "openEuler:Extras", "openEuler:Factory", "openEuler:Mainline", "openEuler:Epol"],
    "openEuler-20.03-LTS-SP1": ["openEuler:20.03:LTS:SP1", "openEuler:20.03:LTS:SP1:Epol"],
    "openEuler-20.03-LTS-SP3": ["openEuler:20.03:LTS:SP3", "openEuler:20.03:LTS:SP3:Epol"],
    "openEuler-22.03-LTS-Next": ["openEuler:22.03:LTS:Next", "openEuler:22.03:LTS:Next:Epol"],
    "openEuler-22.03-LTS": ["openEuler:22.03:LTS", "openEuler:22.03:LTS:Epol"]
}

OE_PROJECT_REALTIME_REPO = {
    "openEuler:Factory":{
        "name":"Factory",
        "baseurl":"http://119.3.219.20:82/openEuler:/Factory/standard_aarch64/",
        "enabled":1,
        "gpgcheck":0},
    "openEuler:Mainline":{
        "name":"Mainline",
        "baseurl":"http://119.3.219.20:82/openEuler:/Mainline/standard_aarch64/",
        "enabled":1,
        "gpgcheck":0},
    "openEuler:22.03:LTS":{
        "name":"2203_LTS",
        "baseurl":"http://119.3.219.20:82/openEuler:/22.03:/LTS/standard_aarch64/",
        "enabled":1,
        "gpgcheck":0},
    "openEuler:22.03:LTS:Epol":{
        "name":"2203_LTS_Epol",
        "baseurl":"http://119.3.219.20:82/openEuler:/22.03:/LTS:/Epol/standard_aarch64/",
        "enabled":1,
        "gpgcheck":0},
    "openEuler:22.03:LTS:Next":{
        "name":"2203_LTS_Next",
        "baseurl":"http://119.3.219.20:82/openEuler:/22.03:/LTS:/Next/standard_aarch64/",
        "enabled":1,
        "gpgcheck":0},
    "openEuler:22.03:LTS:Next:Epol":{
        "name":"2203_LTS_Next_Epol",
        "baseurl":"http://119.3.219.20:82/openEuler:/22.03:/LTS:/Next:/Epol/standard_aarch64/",
        "enabled":1,
        "gpgcheck":0}
}

BUILD_REQUIRE_PATTERN = {
    'C': {
        'build_require': {'gcc', 'gcc-c++', 'glibc', 'glibc-common', 'make', 'automake', 'cmake'},
        'build_command': {'make_build', 'make', 'make ', '%{__make}'}
    },
    'python': {
        'build_require': {
            'python2', 'python-devel', 'python3', 'python2-devel', 
            'python3-devel', '/usr/bin/pathfix.py', 
            'python3-pandas', 'python3-numpy', 'python3-pyelftools',
            '%{required_python}', '%{_py}'
            },
        'build_command': {'py3_build', 'py2_build', '%{__python3}'}
    },
    'java': {
        'build_require': {
            'maven-local', 'mvn', 'ant', 'maven', 
            'javapackages-local', 'gradle-local'
            },
        'build_command': {
            'mvn_build', 'mvn ', 'mvn_artifact ', 'gradle ', 
            'gradlew ', 'gradle-local', 'gradle_build', 'ant '
            }
    },
    'go': {
        'build_require': {
            'go', 'golang', 'golang-bin', 
            'compiler(go-compiler)', 
            'go-compilers-golang-compiler'
            },
        'build_command': {'go build', 'gobuild '}
    },
    'erlang': {
        'build_require': {'erlang', 'erlang-crypto'},
        'build_command': {'erlang_compile'}
    },
    'nodejs': {
        'build_require': {'nodejs', 'nodejs-packaging', 'nodejs-devel'},
        'build_command': {'nodejs_symlink_deps'}
    },
    'perl': {
        'build_require': {
            'perl-devel', 'perl-generators', 
            'perl-interpreter', 'perl'
            },
        'build_command': {'perl'}
    },
    'qt': {
        'build_require': {
            'qt4-devel', 'qt5-qtbase-devel', 
            'qt5-qtwebkit-devel', 'qt5-rpm-macros'
            },
        'build_command': {'qmake_qt4', 'qmake_qt5', 'qmake-qt5'}
    },
    'lua': {
        'build_require': {'lua-devel', 'lua'},
        'build_command': {'LUA_'}
    },
    'ruby': {
        'build_require': {
            'ruby', 'ruby-devel', 'rubygems-devel', 
            '%{?scl_prefix_ruby}ruby(release)', 
            '%{?scl_prefix_ruby}rubygems'
            },
        'build_command': {'rake', 'gem build'}
    },
    'rust': {
        'build_require': {'rust-packaging'},
        'build_command': {'cargo_build'}
    },
    'meson': {
        'build_require': {'meson'},
        'build_command': {'meson_build', 'meson '}
    },
    'mingw': {
        'build_require': {
            'mingw32-gcc-c++', 'mingw64-gcc-c++', 
            'mingw32-filesystem', 'mingw64-filesystem', 
            'mingw32-gcc', 'mingw64-gcc'
            },
        'build_command': {'mingw', 'mingw_make  '}
    },
    'ocaml': {
        'build_require': {'ocaml'},
        'build_command': {'jbuilder '}
    },
    'php': {
        'build_require': {'php-devel'},
        'build_command': {}
    }
}

