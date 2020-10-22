#/bin/env python3
# -*- encoding=utf8 -*-
"""
created by: miaokaibo
date: 2020-10-22 9:30
"""
import csv
import os
import sys

current_path = os.path.join(os.path.split(os.path.realpath(__file__))[0])
sys.path.append(os.path.join(current_path, ".."))
from common.log_obs import log
from common.parser_config import ParserConfigIni

class SaveInfo(object):
    """
    save info to file for packages which is not be updated
    """
    def __init__(self):
        """
        init
        """
        parc = ParserConfigIni()
        self.file_name = parc.get_package_info_file()

    def save_package_msg(self, package_name, branch_name):
        """
        save info
        package_name: package which is not be updated
        branch_name: branch of package
        """
        file_path = os.path.join(current_path, "../log", self.file_name)
        log.info("package: %s, branch: %s" % (package_name, branch_name))
        with open(file_path, 'a') as f:
            csv_writer = csv.writer(f)
            csv_writer.writerow([package_name, branch_name])
        cmd="git pull; git add %s; git commit -m 'update package info'; \
                git push" % file_path
        os.system(cmd)


if __name__ == "__main__":
    s  = SaveInfo()
    s.save_package_msg("vim","master")

