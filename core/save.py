#/bin/env python3
# -*- encoding=utf8 -*-
"""
created by: miaokaibo
date: 2020-10-22 9:30
"""
import csv
import os


class SaveInfo(object):
    """
    save info to file for packages which is not be updated
    """
    def __init__(self):
        """
        init
        """
        pass

    def save_package_msg(self, package_name, branch_name):
        """
        save info
        package_name: package which is not be updated
        branch_name: branch of package
        """
        file_path = os.path.join(os.path.split(os.path.realpath(__file__))[0],
                "../log/package_info.csv")
        with open(file_path, 'a') as f:
            csv_writer = csv.writer(f)
            csv_writer.writerow([package_name, branch_name])


if __name__ == "__main__":
    s  = SaveInfo()
    s.save_package_msg("vim","master")

