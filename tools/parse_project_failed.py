#/bin/env python3
# -*- encoding=utf-8 -*-
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
# ******************************************************************************
import os
import sys
import csv
import shutil
import filecmp
import datetime
import logging
import argparse
import subprocess

LOG_FORMAT = "%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
logging.basicConfig(level=logging.DEBUG, format=LOG_FORMAT, datefmt=DATE_FORMAT)


def run(cmd, timeout=600, print_out=False):
    """
    run shell cmd
    :param timeout: timeout
    :param print_out: print out info, default False
    :return: returncode, stdout, stderr
    """
    ret = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding="utf-8",
                         timeout=timeout)
    logging.info("cmd: {}".format(cmd))
    if ret.stdout and print_out:
        logging.info("ret.stdout: {}".format(ret.stdout))
    if ret.stderr:
        logging.warning("ret.stderr: {}".format(ret.stderr))
    return ret.returncode, ret.stdout, ret.stderr


def write_to_csv(file_path, csv_data):
    """
    write data to csv
    :param file_path: csv file path to write
    :param csv date: csv data
    :return: 
    """
    if not csv_data:
        logging.warning(f"{file_path} has nothing to write")
        return

    with open(file_path, mode='w', newline="\n") as csv_file:
        fieldnames = list(csv_data[0].keys())
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        for line in csv_data:
            writer.writerow(line)


def update_csv_to_obs(file_path):
    """
    update csv to obs
    :param file_path: csv file path
    :return: 
    """
    prefix = file_path.split("-")[0]
    latest_csv_path = f"{prefix}-latest.csv"
    cmd = f"osc ls home:Admin:ISO parse_project_failed {latest_csv_path}"
    _, out, _ = run(cmd, print_out=True)
    update_flag = False
    is_exist = False
    if "does not exist" in out:
        update_flag = True
    elif latest_csv_path in out:
        update_flag = True
        is_exist = True
    else:
        logging.error("osc ls command failed")
        return False
    if update_flag:
        cmd = "osc co home:Admin:ISO parse_project_failed"
        _, out, _ = run(cmd, print_out=True)
        if "At revision" in out:
            obs_path = "./home:Admin:ISO/parse_project_failed/"
            if is_exist:   # compare with obs latest csv
                obs_latest_csv = f"{obs_path}{latest_csv_path}"
                same = filecmp.cmp(file_path, obs_latest_csv)
                if same:
                    logging.info(f"{file_path} is same with obs latest file.")
                    return True
            # not exist or not same, both need to copy and update
            shutil.copyfile(file_path, latest_csv_path)
            shutil.copy(file_path, obs_path)
            shutil.copy(latest_csv_path, obs_path)
            os.chdir(obs_path)
            cmd = "osc addremove && osc ci -n"
            _, out, _ = run(cmd, print_out=True)
            if "Committed revision" in out:
                logging.info(f"update to obs finish")
                return True
            else:
                logging.error("update to obs failed")
                return False
        else:
            logging.error("osc co command failed")
            return False
    return True


class ProjectParser:
    """project build result parser"""

    def __init__(self, **kwargs):
        """param init"""
        self.kwargs = kwargs
        self.project = self.kwargs.get("project", "")
        self.arch = self.kwargs.get("arch", "")
        self.failed_package_list = []

    def parse_failed_package(self):
        """
        parse project failed packages
        :return: failed package info list
        """
        arch_list = self.arch.split(",")
        for arch in arch_list:
            cmd = f"osc r {self.project} -a {arch} --csv | grep failed"
            _, out, _ = run(cmd, print_out=True)
            if out:
                for line in out.splitlines():
                    package_dict = {}
                    if ";" in line:
                        package = line.split(";")[0]
                        package_dict["package"] = package
                        package_dict["project"] = self.project
                        package_dict["arch"] = arch
                        failed_type = self.get_package_failed_type(package, arch)
                        package_dict["failed_type"] = failed_type
                        self.failed_package_list.append(package_dict)

        if self.failed_package_list:
             logging.warning(f"failed package num: {len(self.failed_package_list)}")
             logging.warning(f"failed package list: {self.failed_package_list}")
        else:
             logging.info("failed package num: 0")
        return self.failed_package_list

    def get_package_failed_type(self, package, arch):
        """
        get package failed type
        :param package: package
        :param arch: arch
        :return: package failed type, default: unknown_failed
        """
        failed_type = "unknown_failed"
        build_log_cmd = f"osc remotebuildlog {self.project} {package} standard_{arch} {arch}"
        _, out, _ = run(build_log_cmd)
        if out:
            for line in out.splitlines():
                if "error: Bad exit status" in line:
                    failed_type = line.split()[-1]
                    failed_type = failed_type.replace("(%", "")
                    failed_type = failed_type.replace(")", "")
                    failed_type = f"{failed_type}_failed"

        return failed_type


if __name__ == "__main__":
    par = argparse.ArgumentParser()
    par.add_argument("-p", "--project", default="", help="obs project", required=False)
    par.add_argument("-a", "--arch", default="x86_64,aarch64", help="obs project arch", required=False)
    par.add_argument("-w", "--write_to_csv", default="True", help="write failed to csv or not", required=False)
    par.add_argument("-u", "--update_csv_to_obs", default="True", help="update failed csv to obs", required=False)
    args = par.parse_args()

    kw = {
        "project": args.project,
        "arch": args.arch,
    }

    project_parser = ProjectParser(**kw)
    failed_package_list = project_parser.parse_failed_package()

    exit_code = 0
    if args.write_to_csv == "True":
        if failed_package_list:
            project_name = args.project.replace(":", "_")
            time = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
            csv_path = f"{project_name}-{time}.csv"
            write_to_csv(csv_path, failed_package_list)
            logging.info(f"write to csv file: {csv_path} finish.")

            if args.update_csv_to_obs == "True":
                if not update_csv_to_obs(csv_path):
                    exit_code = 1
    sys.exit(exit_code)

