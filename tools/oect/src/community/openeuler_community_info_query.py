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
# Create: 2021-06-20
# ******************************************************************************/
"""
This is a simple script to query that contact person for specific package
"""
import sys
sys.path.append('/home/oect')
import os
import re
import yaml
import csv
from genericpath import isfile
from src.libs.logger import logger
from src.config import constant
from src.libs.base import http, save2csv
from itertools import islice


class OpenEulerCommunityRepoInfoQuery(object):
    """
    get sig maintainer and contributor of package
    """
    def __init__(self):
        """
        @description :
        -----------
        @param :
        -----------
        @returns :
        -----------
        """

        self.signames = []
        self.sig_repo_map = dict()
        self.get_local_sigs_yaml() # 读取本地的sigs.yaml内容
        self.exps = dict()
        self.get_local_excep_repo_name()
        self.openeuler_repo_owner = dict()
        self.get_local_openEuler_owmers()
        
    def get_local_openEuler_owmers(self):
        """
        get owner of openeuler packages
        Args:
        
        Returns:
        
        """
        with open (constant.LOCAL_OPENEULER_OWNERS, 'r',encoding='gbk') as owner_file:
            reader = csv.reader(owner_file)
            for line in islice(reader, 1, None):
                # Package	Sig	Team	Owner	Email	QA	maintainers
                self.openeuler_repo_owner[line[0].strip()] = dict()
                self.openeuler_repo_owner[line[0].strip()]['Team'] = line[2].strip()
                self.openeuler_repo_owner[line[0].strip()]['Owner'] = line[3].strip()
                self.openeuler_repo_owner[line[0].strip()]['Email'] = line[4].strip()
                self.openeuler_repo_owner[line[0].strip()]['QA'] = line[5].strip()
                self.openeuler_repo_owner[line[0].strip()]['maintainers'] = line[6].strip()
        
        
    def get_local_excep_repo_name(self):
        """
        get the repo_name:srpm_name spec_name dict
        Args:
        
        Returns:
        
        """
        with open(constant.LOCAL_REPO_EXCEP, encoding='utf-8') as f:
            self.exps = yaml.safe_load(f)
        
    
    def get_local_sigs_yaml(self):
        """
        get the content of local sigs.yaml 

        returns:
            sigs: content of sigs.yaml
                exp:
                A-Tune:['python-nni', 'python-astor']
        """
        sigs = dict()
        sigs_dir = os.listdir(constant.LOCAL_SIGS)
        logger.info(sigs_dir)
        for sig_dir in sigs_dir:
            if sig_dir == 'TC' or isfile(os.path.join(constant.LOCAL_SIGS, sig_dir)):
                continue

            self.signames.append(sig_dir)
            sigs[sig_dir] = []

            sig_repos_dir = os.path.join(constant.LOCAL_SIGS, sig_dir, 'src-openeuler') 
            # community/tree/master/sig/Application/src-openeuler/
            try:
                src_oe_pkgs_dir = os.listdir(sig_repos_dir)
            except FileNotFoundError as err:
                # logger.warning(f"{sig_dir} has no src-openeuler/repo")
                continue

            for src_oe_prepos in src_oe_pkgs_dir:
                repos_yamls = os.listdir(os.path.join(sig_repos_dir, src_oe_prepos))
                repo_names = [repo_yaml.replace('.yaml', '') for repo_yaml in repos_yamls]
                sigs[sig_dir].extend(repo_names)

        self.sig_repo_map = sigs

    
    def get_gitee_repo_related_name(self, name_type, name):
        """
        get the real package repo name on gitee

        args:
            name_type: the name of the package/srpm/spec
            name: the value of name
        returns:
            related names: packsge, srpm, spec
        """

        spec_name = name
        gitee_repo_name = name
        srpm_name = name
        for key, value in self.exps.items():
            if name_type == 'spec':
                if value.get("spec") == name:
                    gitee_repo_name = key
                    srpm_name = value.get("srpm")
                    break
            if name_type == 'srpm':
                if value.get("srpm") == name:
                    gitee_repo_name = key
                    spec_name = value.get("spec")
                    break
            if name_type == 'gitee_repo':
                if key == name:
                    spec_name = value.get("spec")
                    srpm_name = value.get("srpm")
                    break
        return gitee_repo_name, spec_name, srpm_name
        

    def query_sig_of_repo(self, package):
        """
        get the sig name of specific package
        args:
            pacakge
        returns:
            sig_name: SIG name to which package belongs
        """ 
        sig_name = "NA"
        if not self.sig_repo_map:
            return sig_name
        for sig in self.signames:
            for repo in self.sig_repo_map[sig]:
                if repo == package:
                    return sig
        return sig_name

        
    def get_owner_sigs(self, gitee_id):
        """
        get the sigs maintained by gitee_id

        args:
            gitee_id: Registered gitee ID
        returns:
            own_sigs: Maintained sig list
        """
        own_sigs = []
        for sig_name in self.signames:
            sig_owners = self.query_maintainer_info(sig_name)
            if gitee_id in sig_owners:
                own_sigs.append(sig_name)

        logger.info(f"{gitee_id} maintain {own_sigs}")
        return own_sigs

    @staticmethod
    def query_maintainer_info(sig_name, info_type='gitee_id'):
        """
        get maintainers of specific sig

        args:
            sig_name: name of sig
        returns:
            maintainers: maintainers of sig
        """

        maintainers = []
        sig_maintainer_yaml = constant.LOCAL_SIGS_OWNERS.format(signame = sig_name)
        try:
            with open(sig_maintainer_yaml, encoding='utf-8') as f:
                yaml_content = yaml.safe_load(f)
                maintainer_content = yaml_content.get('maintainers', {})
                for maintainer_info in maintainer_content:
                    maintainers.append(maintainer_info[info_type])
                logger.info(f"{sig_name} 's maintailers: {maintainers}")
        except FileNotFoundError as err:
            logger.warning(f"{sig_maintainer_yaml}: {err.strerror}")
        except KeyError as kerr:
            logger.warning(f"{sig_name} has no {kerr} info")

        if maintainers:
            return maintainers[0]
        else:
            return ['NA']

    @staticmethod
    def get_spec_context(package_name, spec_name, branch = 'master'):
        """
        get spec file content of package
        args:
            package: package name/spec filename
        returns:
            spec_content: content of spec file
        """

        specurl = constant.SPEC_URL.format( 
            package = package_name, 
            branch = branch, 
            specfile = spec_name + ".spec")
        logger.info(f"specurl:{specurl}")
        resp = http.get(specurl)

        if resp is None or resp.status_code != 200:
            logger.warning(f"get spec: None")
            return None
        spec_str = resp.text
        if spec_str is None:
            logger.error("spec_str is None")
            return None
        else:
            spec = spec_str.splitlines()
        return spec

    def get_latest_contributors(self, package_name, branch, max_eamil_num=1):
        """
        get latest contributors's emails

        args:
            package: package name/spec filename
            max_eamil_num: limit the maximum number of eamils
        returns:
            emails: eamils of latest contributors
        """
        __, spec_name, __ = self.get_gitee_repo_related_name('gitee_repo', package_name)
        spec = OpenEulerCommunityRepoInfoQuery.get_spec_context(package_name, spec_name, branch)
        if spec is None:
            logger.error("get spec of %s failed!", package_name)
            return 'NA'

        emails = self.get_emails_of_contributors(spec)
        if emails:
            return emails[0]
        else:
            return 'NA'
        
    @staticmethod
    def get_emails_of_contributors(spec, max_eamil_num=1):
        """
        analyse the email of contributor in changelog
        args:
            spec: content of spec file
            max_eamil_num: limit the maximum number of eamils
        returns:
            emails: eamils of latest max_eamil_num contributors
        """
        emails = []
        num = 0
        in_changelog = False
        for line in spec:
            if line.startswith("%changelog"):
                in_changelog = True
            if in_changelog and line.startswith("*") and num < max_eamil_num:
                try:
                    regular = re.compile(r'[0-9a-zA-Z\.\-]+@[0-9a-zA-Z\.\-]+[com, org]')
                    email = re.findall(regular, line)[0]
                    logger.info(f"email: {email}")
                    emails.append(email)
                    num = num + 1
                except IndexError as e:
                    logger.error(f"analyse developer for {line} failed")
                    emails.append(line)
        return emails

    def query_sig_repo(self, sig_name):
        """
        query the repo name list of sig_name
        Args:
            sig_name: name of sig
        Returns:
            sig_repos: list of repo of sig
        """
        
        sig_repos = []
        
        try:
            sig_repos = self.sig_repo_map[sig_name]
        except KeyError as ke:
            logger.error(ke)
        return sig_repos

    def query_full_sig_repos(self):
        """
        @description :生成一份gitee上的repo——sig——maintainer信息表
        -----------
        @param :
        -----------
        @returns :
        -----------
        """
        res_data = []
        for c_sig_name in self.signames:
            sig_repos = self.query_sig_repo(c_sig_name)
            sig_maintainer = self.query_maintainer_info(c_sig_name)
            for repo_name in sig_repos:
                res_data.append([repo_name, c_sig_name, sig_maintainer])

        res_csv_name = "openEuler_full_repos.csv"
        save2csv(res_csv_name, res_data, 'w', ["Package", "Sig", "Maintainers"])


    def get_related_email(self, repo_name):
        """
        @description : 获取软件包的sig组信息、最近的贡献者邮箱信息
        -----------
        @param :
        -----------
        @returns :
        -----------
        """

        sig_name = self.query_sig_of_repo(repo_name)
        sig_maintainer = self.query_maintainer_info(sig_name)
        developer_email = self.get_latest_contributors(repo_name, self.branch)
        return sig_name, sig_maintainer, developer_email


sig_info_query = OpenEulerCommunityRepoInfoQuery()

if __name__ == "__main__":
    sig_info_query.get_latest_contributors('zip', 'master')