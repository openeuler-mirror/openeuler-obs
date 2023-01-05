#!/bin/env python3
# -*- encoding=utf8 -*-
#******************************************************************************
# Copyright (c) Huawei Technologies Co., Ltd. 2021-2021. All rights reserved.
# licensed under the Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#     http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY OR FIT FOR A PARTICULAR
# PURPOSE.
# See the Mulan PSL v2 for more details.
# Author: yaokai
# Create: 2021-03-19
# ******************************************************************************
"""
check the format and URL of the service file
"""
import os
import sys
import requests
Now_path = os.path.join(os.path.split(os.path.realpath(__file__))[0])
sys.path.append(os.path.join(Now_path, ".."))
from common.log_obs import log
from xml.etree import ElementTree as ET
from bs4 import BeautifulSoup
import xml.dom.minidom
from common.parser_config import ParserConfigIni

class CheckMetaPull(object):
    """
    Check the format of the service file and the correctness of its URL
    """
    def __init__(self, **kwargs):
        """
        kawrgs: dict,init dict by 'a': 'A' style
        prid: the pullrequest id
        branch: which gitee branch you want to ckeck
        token: giteee api access_token
        current_path: your codes path
        check_error: The list which check error
        """
        self.kwargs = kwargs
        self.prid = self.kwargs['pr_id']
        self.branch = self.kwargs['branch']
        self.token = self.kwargs['access_token']
        self.current_path = os.getcwd()
        self.check_error = []
        self.meta_path = self.kwargs['obs_meta_path']
        par = ParserConfigIni()
        self.obs_ignored_package = par.get_obs_ignored_package()

    def _clean(self):
        """
        Cleanup the current directory of obs_meta and community
        """
        del_repo = ['obs_meta','community']
        for repo in del_repo:
            cmd = "if [ -d {0} ];then rm -rf {0} && echo 'Finish clean the {0}';fi".format(repo)
            rm_result = os.popen(cmd).readlines()
            log.info(rm_result)

    def _get_latest_obs_meta(self):
        """
        Get the latest obs_meta
        """
        log.info("Get the latest obs_meta")
        clone_cmd = "git clone --depth=1 https://gitee.com/src-openeuler/obs_meta"
        for x in range(5):
            log.info("Try to clone %s" % x)
            clone_result = ""
            pull_result = ""
            clone_result = os.popen(clone_cmd).readlines()
            pull_result = os.popen("if [ -d obs_meta ];then echo 'Already up to date'; \
                    else echo 'Clone error';fi").readlines()
            if "Already" in pull_result[0]:
                log.info(pull_result)
                log.info("Success to clone obs_meta")
                return
            else:
                os.popen("if [ -d obs_meta ];then rm -rf obs_meta")
        raise SystemExit("*******obs_meta-clone-error:please check your net*******")

    def _get_change_file(self):
        """
        Gets a list of newly added files in obs_meta
        """
        current_path = os.getcwd()
        fetch_cmd = "git fetch origin pull/%s/head:thispr" % self.prid
        branch_cmd = "git branch -a | grep 'thispr'"
        checkout_cmd = "git checkout thispr"
        changed_file_cmd = "git diff --name-status HEAD~1 HEAD~0"
        if not self.meta_path:
            for x in range(5):
                os.chdir("obs_meta")
                fetch_result = os.popen(fetch_cmd).read()
                log.info(fetch_result)
                branch_result = os.popen(branch_cmd).readlines()
                if branch_result:
                    log.info(branch_result)
                    break
                else:
                    os.chdir("../")
                    self._clean()
                    self._get_latest_obs_meta()
            show_result = os.popen(checkout_cmd).readlines()
            log.info(show_result)
        else:
            cp_result = os.system("cp -rf %s ./ " % self.meta_path)
            os.chdir("obs_meta")
        changed_file = os.popen(changed_file_cmd).readlines()
        log.info(changed_file)
        os.chdir("../")
        return changed_file

    def _parse_git_log(self, line):
        """
        deal diff_patch line mesg
        """
        log.info("line:%s" % line)
        new_file_path = ''
        complete_new_file_path = ''
        modify_file_path = ''
        log_list = list(line.split())
        temp_log_type = log_list[0]
        if len(log_list) == 3:
            if log_list[1].split('/')[0] != log_list[2].split('/')[0] and \
                    log_list[1].split('/')[-2] == log_list[2].split('/')[-2]:
                log.error("ERROR_COMMIT: %s" % line)
                log.error("FAILED:PR contains the movement of same package \
                        between branches")
                raise SystemExit("*******PLEASE CHECK YOUR PR*******")
            else:
                new_file_path = list(line.split())[2]
                complete_new_file_path = list(line.split())[2]
        elif len(log_list) == 2:
            if temp_log_type == "M":
                modify_file_path = list(line.split())[1]
            if temp_log_type != "D":
                new_file_path = list(line.split())[1]
            complete_new_file_path = list(line.split())[1]
        log.info(new_file_path)
        return new_file_path, complete_new_file_path, modify_file_path

    def _check_file_format(self, file_path):
        """
        Function modules: Check the format of the service file
        """
        try:
            ET.parse(file_path)
            log.info("**************FORMAT CORRECT***************")
            log.info("The %s has a nice format" % file_path)
            log.info("**************FORMAT CORRECT***************")
        except Exception as e:
            log.error("**************FORMAT ERROR*****************")
            log.error("MAY be %s has a bad format" % file_path)
            log.error("%s format bad Because:%s" % (file_path, e))
            log.error("**************FORMAT ERROR*****************")
            return "yes"

    def _get_url_info(self, pkg_path):
        """
        get pkg_name and pkg_branch from service file
        """
        url_list = []
        with open(pkg_path, "r") as f:
            log.info('\n' + f.read())
        dom = xml.dom.minidom.parse(pkg_path)
        root = dom.documentElement
        param_lines = root.getElementsByTagName('param')
        for url in param_lines:
            if url.getAttribute("name") == "url":
                url_list.append(url.firstChild.data.strip('/'))
        log.info("ALL_URL:%s" % url_list)
        return url_list

    def _get_url_info_new(self, pkg_path):
        """
        get pkg_name and pkg_branch from service file for new service content
        """
        url_list = []
        revision_list = []
        path_info = self._get_path_info(pkg_path)
        with open(pkg_path, "r") as f:
            log.info('\n' + f.read())
        dom = xml.dom.minidom.parse(pkg_path)
        root = dom.documentElement
        param_lines = root.getElementsByTagName('param')
        for url in param_lines:
            if url.getAttribute("name") == "url":
                url_list.append(url.firstChild.data.strip('/'))
            elif url.getAttribute("name") == "revision":
                revision_list.append(url.firstChild.data.strip('/'))
        log.info("ALL_URL:%s" % url_list)
        log.info("ALL_REVISION:%s" % revision_list)
        return url_list,revision_list

    def _get_path_info(self, pkg_path):
        """
        get pkg_name and pkg_branch from change path
        """
        pkg_name = pkg_path.split('/')[-2]
        #Support Multi_Version
        if "Multi" in pkg_path.split('/')[0] or "multi" in pkg_path.split('/')[0]:
            pkg_url = pkg_path.split('/')[1]
        else:
            pkg_url = pkg_path.split('/')[0]
        pkg_info = [pkg_name, pkg_url]
        return pkg_info

    def _pkgname_check(self, pkg_name, service_name_list):
        """
        check the pkg_name from change_path and service_name_list
        """
        if pkg_name in service_name_list:
            log.info("SUCCESS_CHECK:The %s in _service url is correct" % pkg_name)
            return
        else:
            log.error("**************_Service URL ERROR*****************")
            log.error("FAILED:The %s in _service pkgname is not same" % pkg_name)
            error_flag = "yes"
            return error_flag

    def _check_correspond_from_service_new(self, **info):
        """
        Distingguish check pkg_name between different branch for new service content
        """
        error_flag = ""
        if info['pkg_url'] == "master" and len(list(set(info['ser_branch']))) == 1:
            error_flag = self._pkgname_check(info['pkg_name'], info['ser_name'])
        elif list(set(info['ser_branch']))[0] == info['pkg_url'] and len(list(set(info['ser_branch']))) == 1:
            error_flag = self._pkgname_check(info['pkg_name'], info['ser_name'])
        else:
            log.error("**************_Service URL ERROR*****************")
            log.error("FAILED:Please check the url in your %s _service again"
                    % info['pkg_name'])
            error_flag = "yes"
        return error_flag

    def _check_correspond_from_service(self, **info):
        """
        Distingguish check pkg_name between different branch
        """
        error_flag = ""
        if list(set(info['ser_branch']))[0] == "openEuler" \
                and info['pkg_url'] == "master" and len(list(set(info['ser_branch']))) == 1\
                and list(set(info['ser_next']))[0] == "next" \
                and len(list(set(info['ser_next']))) == 1:
            error_flag = self._pkgname_check(info['pkg_name'], info['ser_name'])
        elif list(set(info['ser_branch']))[0] == info['pkg_url'] \
                and len(list(set(info['ser_branch']))) == 1 \
                and list(set(info['ser_next']))[0] == "next" \
                and len(list(set(info['ser_next']))) == 1:
            error_flag = self._pkgname_check(info['pkg_name'], info['ser_name'])
        else:
            log.error("**************_Service URL ERROR*****************")
            log.error("FAILED:Please check the url in your %s _service again"
                    % info['pkg_name'])
            error_flag = "yes"
        return error_flag

    def parse_all_info(self,pkg_path):
        service_name = []
        service_branch = []
        service_next = []
        url_list = self._get_url_info(pkg_path)
        for all_url in url_list:
            service_next.append(all_url.split('/')[0])
            service_name.append(all_url.split('/')[-1])
            service_branch.append(all_url.split('/')[-2])
        path_info = self._get_path_info(pkg_path)
        log.info("Url_Next:%s" % service_next)
        log.info("Pkgname_in_Service:%s" % service_name)
        log.info("pkgbranch_in_Service:%s" % service_branch)
        log.info("Pkgname_in_Obe_meta_path:%s" % path_info[0])
        log.info("Pkgbranch_in_Obs_meta_path:%s" % path_info[1])
        all_info = {'ser_branch':service_branch, 'pkg_url':path_info[1],
            'ser_next':service_next, 'pkg_name':path_info[0],
            'ser_name':service_name}
        return all_info

    def parse_all_info_new(self,pkg_path):
        service_name = []
        service_branch = []
        url_list,revision_list = self._get_url_info_new(pkg_path)
        for all_url in url_list:
            head=os.path.splitext(all_url.split('/')[1])[0]
            service_name.append(head)
        for all_revision in revision_list:
            service_branch.append(all_revision)
        path_info = self._get_path_info(pkg_path)
        log.info("Pkgname_in_Service:%s" % service_name)
        log.info("pkgbranch_in_Service:%s" % service_branch)
        log.info("Pkgname_in_Obs_meta_path:%s" % path_info[0])
        log.info("Pkgbranch_in_Obs_meta_path:%s" % path_info[1])
        all_info = {'ser_branch':service_branch, 'pkg_url':path_info[1], 'pkg_name':path_info[0], 'ser_name':service_name}
        return all_info

    def _check_pkg_services(self, pkg_path):
        """
        Check the format of the service file and the correctness of its URL
        """
        error_flag2 = ""
        error_flag3 = ""
        os.chdir("%s/obs_meta" % self.current_path)
        error_flag1 = self._check_file_format(pkg_path)
        if error_flag1 != "yes":
            path_info = self._get_path_info(pkg_path)
            meta_pkg_name = path_info[0]
            meta_pkg_branch = path_info[1]
            if meta_pkg_branch != 'master':
                all_info = self.parse_all_info(pkg_path)
                error_flag2 = self._check_correspond_from_service(**all_info)
            else:
                if meta_pkg_name in self.obs_ignored_package:
                    all_info = self.parse_all_info(pkg_path)
                    error_flag2 = self._check_correspond_from_service(**all_info)
                else:
                    all_info = self.parse_all_info_new(pkg_path)
                    error_flag2 = self._check_correspond_from_service_new(**all_info)
        if self.token:
            error_flag3 = self._detect_protect_branch(pkg_path)
        error_flag4 = self._one_pkg_one_branch(pkg_path)
        error_flag = error_flag1 or error_flag2 or error_flag3 or error_flag4
        if error_flag:
            self.check_error.append(pkg_path)
        return error_flag

    def _check_meta_pro_and_repo(self, pro_repo):
        """
        get the project and repository from meta and distinguish
        """
        all_path_flag = []
        for msg in pro_repo:
            log.info("msg:%s" % msg)
            msglist = str(msg).split()
            for key in msglist:
                if "project=" in key:
                    project = key.split("\"")[1]
                if "repository=" in key:
                    repository = key.split("\"")[1]
            log.info(project)
            log.info(repository)
            error_flag = self._exist_for_pro_and_repo(project, repository)
            all_path_flag.append(error_flag)
        if "yes" in all_path_flag:
            return "yes"

    def _exist_for_pro_and_repo(self, project, repository):
        """
        check the project and repository is or not exist in obs
        """
        error_flag = None
        exit_cmd = "osc r %s --xml 2>/dev/null | grep %s" % (project, repository)
        exit_result = os.popen(exit_cmd).read()
        log.info(exit_result)
        if not exit_result:
            error_flag = "yes"
            log.error("Failed:The %s Not exit in %s" % (repository, project))
        else:
            log.info("Success:The %s exit in %s" % (repository, project))
        return error_flag

    def _check_meta_project_same_with_origin(self, pro_repo, change_file):
        error_flag = None
        path_list = change_file.split('/')
        multi_project_name = path_list[-1]
        log.info("meta file multi_project_name:{}".format(multi_project_name))
        for msg in pro_repo:
            msglist = str(msg).split()
            for key in msglist:
                if "project=" in key:
                    project = key.split("\"")[1]
            origin_project = project.replace(":selfbuild:BaseOS","")
            log.info("meta file origin_project_name:{}".format(origin_project))
            if origin_project not in multi_project_name:
                log.error("The _meta file project not same with project name!!!!!!")
                error_flag = "yes"
        return error_flag


    def _check_pro_meta(self, pkg_path):
        """
        check the _meta have the maintainer or path is or not
        """
        os.chdir("%s/obs_meta" % self.current_path)
        error_flag1 = self._check_file_format(pkg_path)
        error_flag2 = ""
        error_flag3 = ""
        error_flag4 = ""
        with open(pkg_path, "r") as f:
            parse = f.read()
            log.info('\n' + parse)
            soup = BeautifulSoup(parse, "html.parser")
            maintainers = soup.find_all('person')
            pro_repo = soup.find_all('path')
            log.info("maintainers:%s" % maintainers)
            log.info("pro_repo:%s" % pro_repo)
        if not maintainers:
            error_flag2 = "yes"
            log.error("The _meta file does not have the maintainers section!!!!!!")
        error_flag3 = self._check_meta_pro_and_repo(pro_repo)
        if "multi" in pkg_path or "Multi-Version" in pkg_path:
            error_flag4 = self._check_meta_project_same_with_origin(pro_repo, pkg_path)
        error_flag = error_flag1 or error_flag2 or error_flag3 or error_flag4
        if error_flag == "yes":
            self.check_error.append(pkg_path)
        return error_flag

    def _multi_name_check(self, change_file):
        """
        check the multi_version format
        """
        path_list = change_file.split('/')
        path_list_len = len(path_list)
        log.info("multi_name_check:%s" % path_list)
        error_flag2 = ""
        error_flag1 = ""
        if path_list_len >= 3:
            multi_branch = path_list[2]
            multi_branch_list = multi_branch.split('_')
            multi_branch_head = multi_branch_list[0]
            multi_branch_mid = multi_branch_list[1]
            multi_branch_tail = multi_branch_list[2]
            branch_list = os.listdir(os.path.join(self.current_path, "obs_meta"))
        if path_list_len == 4:
            multi_project = path_list[3]
            multi_pro_head = multi_project.split(':Multi-Version:')[0]
            multi_pro_tail = multi_project.split(':Multi-Version:')[1]
            if os.path.exists(os.path.join(self.current_path, "obs_meta",
                multi_branch_tail)):
                project_list = os.listdir(os.path.join(self.current_path, "obs_meta",
                    multi_branch_tail))
            else:
                project_list = None
                log.error("The %s is not exists!,please check your %s!!!"
                        % (multi_branch_tail, multi_branch))
                error_flag1 = "yes"
        if branch_list:
            log.info("multi_branch_head:%s" % multi_branch_head)
            log.info("multi_branch_tail:%s" % multi_branch_tail)
            log.info("branch_list:%s" % branch_list)
            if multi_branch_head == "Multi-Version" and multi_branch_tail in branch_list:
                log.info("Success to check branch:%s" % multi_branch)
            else:
                log.error("Failed!!! Make sure your Mukti-branch:%s" % multi_branch)
                error_flag2 = "yes"
        if branch_list and project_list:
            log.info("multi_pro_head:%s" % multi_pro_head)
            log.info("multi_pro_tail:%s" % multi_pro_tail.replace(':', '-'))
            log.info("multi_branch_mid:%s" % multi_branch_mid)
            log.info("project_list:%s" % project_list)
            if multi_pro_tail.replace(':', '-') == multi_branch_mid and  \
                    error_flag2 != "yes" and multi_pro_head in project_list:
                log.info("Success to check project:%s/%s" % (multi_branch, multi_project))
            else:
                log.error("Failed!!! Make sure your Multi_branch and project:%s/%s" \
                        % (multi_branch, multi_project))
                error_flag2 = "yes"
        error_flag = error_flag1 or error_flag2
        return error_flag

    def _detect_protect_branch(self, change_path):
        """
        check the pkg whether the branch is protected
        """
        # LoongArch branch does not check protected
        if "loongarch" in change_path.lower():
            return
        path_list = change_path.split('/')
        if "multi" in path_list[0] or "Multi" in path_list[0]:
            branch = path_list[1]
        else:
            branch = path_list[0]
        pkg = path_list[-2]
        api_url = "https://gitee.com/api/v5/repos/src-openeuler/%s" % pkg + \
                "/branches/%s?access_token=%s" % (branch, self.token)
        attempts = 0
        success = False
        while attempts < 5 and not success:
            try:
                response = requests.request(method='get', url=api_url)
                protect_value = response.json()['protected']
                log.info("%s protected:%s" % (pkg, protect_value))
                success = True
                if not protect_value:
                    log.error("ERROR:%s in %s is not protected branch" % (pkg, branch))
                    return "yes"
                else:
                    return
            except Exception as e:
                attempts += 1
                if attempts == 5:
                    break
        log.error("***************Get Request From Gitee ERROR***************")
        log.error("%s in %s can not get branch information from gitee" % (pkg, branch))
        log.error("***************Get Request From Gitee ERROR***************")
        return "yes"

    def _get_all_change_file(self):
        """
        get all change file_path
        """
        if self.meta_path:
            cp_result = os.system("cp -rf %s ./" % self.meta_path)
        else:
            self._clean()
            self._get_latest_obs_meta()
            self._get_latest_community()
        changefile = self._get_change_file()
        changelist = []
        complete_changelist = []
        modify_changelist = []
        for msg in changefile:
            parse_git, complete_parse_git, modify_git = self._parse_git_log(msg)
            if parse_git:
                changelist.append(parse_git)
            if complete_parse_git:
                complete_changelist.append(complete_parse_git)
            if modify_git:
                modify_changelist.append(modify_git)
        if changelist or complete_changelist:
            return changelist, complete_changelist, modify_changelist
        else:
            log.info("Finish!!There are no file need to check")
            sys.exit()

    def _get_multi_branch_and_project(self, multi_change):
        """
        get all the multi_version branch and one of the corresponding projects
        """
        pro_dir = "multi_version/%s" % multi_change.split('/')[1]
        branchs = os.listdir(os.path.join(self.current_path, \
                "obs_meta", "OBS_PRJ_meta/multi_version"))
        projects = os.listdir(os.path.join(self.current_path, \
                "obs_meta", "OBS_PRJ_meta", pro_dir))
        log.info("multi_branch_list:%s" % branchs)
        log.info("multi_project_list:%s" % projects)
        multi_info = {'branchs':branchs, 'projects':projects}
        return multi_info

    def _one_pkg_one_branch(self, change):
        """
        checks if the same package exists in a branch
        """
        pkg = change.split('/')[-2]
        branch = change.split('/')[-4]
        now_path = os.getcwd()
        all_pkg_pro = []
        if "multi" in change.split('/')[0] or "Multi" in change.split('/')[0]:
            meta_branch_path = os.path.join(self.current_path, "obs_meta", "multi_version", branch)
        else:
            meta_branch_path = os.path.join(self.current_path, "obs_meta", branch)
        os.chdir(meta_branch_path)
        all_pkg_path = os.popen("find | grep %s" % pkg).read().split('\n')
        log.info("all_pkg_name_contains %s:%s" % (pkg, all_pkg_path))
        for x in all_pkg_path:
            if x.split("/")[-1] == pkg and ":Bak" not in x and "RISC-V" not in x:
                all_pkg_pro.append(x)
        log.info("%s in %s is %s" % (pkg, branch, all_pkg_pro))
        os.chdir(now_path)
        if len(all_pkg_pro) != 1:
            log.error("%s in %s is %s" % (pkg, branch, all_pkg_pro))
            log.error("RPM can only exist in one project for one branch")
            return "yes"

    def _distinguish_check_service(self, change):
        """
        Distingguish the handing of Multi branch from that of Service
        """
        if "multi" in change.split('/')[0] or "Multi" in change.split('/')[0] and \
                len(change.split('/')) == 5:
            multi_info = self._get_multi_branch_and_project(change)
            if change.split('/')[1] in multi_info['branchs'] and \
                    change.split('/')[2] in multi_info['projects']:
                error_flag = self._check_pkg_services(change)
            else:
                log.error("Please check your commit dir %s!!!" % change)
                error_flag = "yes"
        elif len(change.split('/')) == 4:
            error_flag = self._check_pkg_services(change)
        else:
            log.error("Please check your commit dir %s!!!" % change)
            error_flag = "yes"
        return error_flag

    def _check_service_meta(self, change_list):
        """
        check the _service or _meta file in commit
        """
        flag_list = []
        for change in change_list:
            if "_service" in change:
                error_flag = self._distinguish_check_service(change)
                flag_list.append(error_flag)
            elif "OBS_PRJ_meta" in change and "prjconf" not in change:
                error_flag1 = None
                if "multi" in change or "Multi" in change:
                    error_flag1 = self._multi_name_check(change)
                error_flag2 = self._check_pro_meta(change)
                error_flag = error_flag1 or error_flag2
                flag_list.append(error_flag)
            elif "OBS_PRJ_meta" in change and "prjconf" in change:
                continue
            else:
                log.info("There are no _service or _meta need to check")
        os.chdir(self.current_path)
        self._clean()
        if "yes" in flag_list:
            print("error_check_list:")
            for error_service in self.check_error:
                print(error_service)
            raise SystemExit("*******PLEASE CHECK YOUR PR*******")

    def _check_branch_service(self, branch):
        """
        check the file for the corresponding branch
        """
        if "multi" in branch or "Multi" in branch:
            branchlist = os.listdir(os.path.join(self.current_path, "obs_meta",
                "OBS_PRJ_meta", "multi_version"))
        else:
            branchlist = os.listdir(os.path.join(self.current_path, "obs_meta",
                "OBS_PRJ_meta"))
        meta_path = os.path.join(self.current_path, "obs_meta")
        os.chdir(meta_path)
        if branch in branchlist:
            if "multi" in branch or "Multi" in branch:
                service = os.popen("find multi_version/%s | grep _service" % branch).read()
            else:
                service = os.popen("find %s | grep _service" % branch).read()
        elif branch == "all":
            service = os.popen("find | grep _service").read()
        service_list = list(service.split('\n'))
        ignore_branch = "openEuler-EPOL-LTS"
        service_path_list = [x.lstrip("./") for x in service_list if x and ignore_branch not in x]
        log.info(service_path_list)
        self._check_service_meta(service_path_list)

    def get_private_path_pkgname(self,private_sig_path):
        '''
        get private sig pkg name from sig path
        params
        private_sig_path : private sig path in community repo
        '''
        private_sig_pkgs = []
        for filepath,dirnames,filenames in os.walk(private_sig_path):
            for file in filenames:
                head,sep,tail = file.partition('.')
                private_sig_pkgs.append(head)
        return private_sig_pkgs

    def _check_private_sig_pkg(self,change_file):
        '''
        check add pkg include in private sig 
        params
        chang_file : modified file abs path
        '''
        log.info("******CHECK PR PRIVATE SIG PKGNAME*********")
        private_sig_path = os.path.join(self.current_path, "community",
                "sig", "Private","src-openeuler")
        private_sig_pkgs = self.get_private_path_pkgname(private_sig_path)
        failed_flag = False
        failed_msg = []
        for file in change_file:
            path_info = self._get_path_info(file)
            pkg_name = path_info[0]
            if pkg_name in private_sig_pkgs:
                log.error("check failed this pkg:{} in private sig".format(pkg_name))
                failed_msg.append(pkg_name)
                failed_flag = True
            else:
                log.info("check success this pkg:{} not in private sig".format(pkg_name))
        if failed_flag:
            log.error("this below pkgs in private sig:{}".format(failed_msg))
            raise SystemExit("*******CHECK PR PRIVATE SIG PKGNAME ERROR:please check your PR*******")
        log.info("******CHECK PR PRIVATE SIG PKGNAME*********")


    def _get_latest_community(self):
        """
        Get the latest community repo
        """
        log.info("Get the latest community")
        clone_cmd = "git clone --depth=1 https://gitee.com/openeuler/community"
        for x in range(5):
            log.info("Try to clone %s" % x)
            pull_result = ""
            os.system(clone_cmd)
            pull_result = os.popen("if [ -d community ];then echo 'Already up to date'; \
                    else echo 'Clone error';fi").readlines()
            if "Already" in pull_result[0]:
                log.info(pull_result)
                log.info("Success to clone community")
                return
            else:
                os.system("if [ -d community ];then rm -rf community;fi")
        raise SystemExit("*******community-clone-error:please check your net*******")

    def _check_pr_rule(self, release_manage, pr_file, modify_pr_file):
        """
        check openeuler_meta pull request
        """
        log.info("******CHECK PR RULE*********")
        failed_flag = []
        failed_msg = []
        if release_manage:
            for change_file in pr_file:
                if change_file not in modify_pr_file:
                    path_info = self._get_path_info(change_file)
                    if path_info[1] in release_manage:
                        log.error("check pr rule failed repository path:{}".format(change_file))
                        obs_project_name = change_file.split('/')[1]
                        failed_flag.append('yes')
                        failed_msg.append(obs_project_name)
                    else:
                        log.info("check pr rule success repository path:{}".format(change_file))
                else:
                    log.info("modify file ignore check pr rule repository path:{}".format(change_file))
            if failed_flag:
                log.error("you can not pull request in branch:{}".format(failed_msg))
                log.info("Please refer to this doc to create PR in repo release-management:https://gitee.com/openeuler/release-management/blob/master/openEuler%E5%BC%80%E5%8F%91%E8%80%85%E6%8F%90%E4%BA%A4PR%E6%8C%87%E5%AF%BC%E6%96%87%E6%A1%A3.md".format(failed_msg))
                raise SystemExit("*******PLEASE CHECK YOUR PR*******")
        else:
            log.error("get release management data failed,please check network and token")
        log.info("******CHECK PR RULE********")
        log.info("check pr rule finished,please wait other check!!!")


    def do_all(self):
        """
        make the get obs_meta change fuction and check fuction doing
        """
        if self.prid and self.token:
            release_management_data = self._release_management_tree()
            change_result, complete_change_result, modify_result = self._get_all_change_file()
            pr_check_result = self._check_pr_rule(release_management_data, complete_change_result, modify_result)
            self._check_private_sig_pkg(change_result)
            check_result = self._check_service_meta(change_result)
        elif not self.prid and self.branch:
            self._clean()
            self._get_latest_obs_meta()
            self._check_branch_service(self.branch)
        else:
            log.error("ERROR_INPUT:PLEASE CHECK YOU INPUT")

    def _release_management_tree(self):
        """
        get release_management tree
        """
        log.info("************************************** GET RELASE MANAGEMENT DATA**********************")
        release_management_data = []
        sha_api_url = "https://gitee.com/api/v5/repos/openeuler/release-management/branches/master?access_token={}".format(self.token)
        sha_value = self._gitee_api_request(sha_api_url,'shav')
        if sha_value:
            api_url = "https://gitee.com/api/v5/repos/openeuler/release-management/git/trees/{}?access_token={}".format(sha_value, self.token)
            release_manage_value = self._gitee_api_request(api_url,'manage')
            if release_manage_value:
                for current_file in release_manage_value:
                    if current_file['type'] == 'tree':
                        release_management_data.append(current_file['path'])
        log.info("************************************** GET RELASE MANAGEMENT DATA**********************")
        return release_management_data

    def _gitee_api_request(self, url,flag):
        """
        gitee api interface
        """
        retries = 0
        success = False
        while retries < 5:
            try:
                log.info("try to request data from gitee {}".format(retries))
                response = requests.request(method='get', url=url)
                if flag == 'shav':
                    response_value = response.json()['commit']['sha']
                    return response_value
                else:
                    response_value = response.json()['tree']
                    return response_value
            except Exception as e:
                log.info("try to request data from gitee {} failed,retry!!!".format(retries))
                retries += 1
                if retries == 5:
                    log.error("***************Get Request Data From Gitee ERROR***************")
                    raise SystemExit("*******error request data from gitee,please wait and retry*******")