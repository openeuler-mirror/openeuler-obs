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
# Create: 2022-06-17
# ******************************************************************************/

from pickle import TRUE
import sys
sys.path.append('/home/oect')
from src.libs.logger import logger
import codecs
import csv
import pandas as pd

class CSVRW(object):
    """
    common useage for reading or writing csv file
    """ 

    @classmethod
    def get_object_type(cls, obj):
        """
        query the type of object
        Args:
            obj:
        Returns:
            obj_type:
        """
        obj_type = None
        if isinstance(obj, tuple):
            obj_type = "tuple"
        elif isinstance(obj, dict):
            obj_type = "dict"
        elif isinstance(obj, list):
            obj_type = "list"
        elif isinstance(obj, set):
            obj_type = "set"

        return obj_type
        
    @classmethod
    def get_keys_of_multi_dict(cls, final_keys, dict_value):
        """
        analyse the dict data and return the key's list
        Args:
            final_keys: store all of the keys of dict_value
            dict_value:
        Returns:

        """
        if cls.get_object_type(dict_value) != 'dict':
            return
        elif cls.get_object_type(dict_value) == 'dict':
            if not final_keys:
                last_key = ''
            else:
                last_key = final_keys[-1]
                final_keys.pop()
            
            for sub_key, sub_value in dict_value.items():
                if not last_key:
                    final_keys.append(sub_key)
                else:
                    final_keys.append('_'.join([last_key, sub_key]))
                cls.get_keys_of_multi_dict(final_keys, sub_value)

        return 
        
    @classmethod
    def get_line_of_multi_dict(cls, res_list, dict_value):
        """
        convert the dict value to list 
        Args:
            res_list: store the list data
            dict_value:
        Returns:
        
        """

        if cls.get_object_type(dict_value) != 'dict':
            res_list.append(dict_value)
            return
        elif cls.get_object_type(dict_value) == 'dict':
            for __, value in dict_value.items():
                cls.get_line_of_multi_dict(res_list, value)

        return


    @classmethod
    def save_by_row(cls, res_name, input_data, csv_title=None, save_mode='w', save_encoding='utf-8'):
        """
        save inputdata to csv file
        Note: If the keys of different elements in the dictionary data to be processed \
            are different or missing, or the order of keys is chaotic, this function is not applicable.
        Args:
            res_name: file name to save
            input_data: input data to save
            csv_title: the title of csv file
            save_mode: 
            save_encoding:
            
        Returns:
        
        """

        if cls.get_object_type(input_data) == 'list':
            if not csv_title:
                logger.warning(f"we need csv_title for list-type input_data")
                return False
            
            with codecs.open(res_name, save_mode, save_encoding) as result_file:
                writer = csv.writer(result_file)
                writer.writerow(csv_title)
                writer.writerows(input_data)

        elif  cls.get_object_type(input_data) == 'dict':
            # Re parse the dictionary key as the csv_title
            csv_title = []
            values = list(input_data.values())

            cls.get_keys_of_multi_dict(csv_title, values[0])
            csv_title.insert(0, 'Main_key')
            # logger.info(f"analyse csv_title: {csv_title}")

            with codecs.open(res_name, save_mode, save_encoding) as result_file:
                writer = csv.writer(result_file)
                writer.writerow(csv_title)

                for main_key, main_value in input_data.items():
                    line = []
                    line.append(main_key)
                    cls.get_line_of_multi_dict(line, main_value)
                    writer.writerow(line)
        else:
            logger.warning("Sorry, we do not support other typed input_data")
            return False
        logger.info("======Successfully save csv========")
        return True

    @staticmethod
    def save_by_column(res_name, input_data, csv_title, save_mode='w', save_encoding='utf-8'):
        """
        save dict inputdata to csv file
        Args:
            res_name: file name
            save_mode: save mode
            csv_title:
            input_data:
        Returns:
        
        """
        final_data = dict()
        num_csv_title = len(csv_title)
        num_data_list = len(input_data)
        if num_csv_title != num_data_list:
            logger.warning(f"csv_title({num_csv_title}) does not match data column({num_data_list}): terminate")
            return
        for i in range(num_csv_title):
            final_data[csv_title[i]] = input_data[i]
        df = pd.DataFrame(final_data, columns=csv_title)
        df.to_csv(res_name, index=False, mode=save_mode, encoding=save_encoding)

        logger.info("======Successfully save csv========")
        

    @staticmethod
    def read_2_dict(file, encoding='utf-8'):
        """
        read csv data and turn to dict: take csv_title[0] as the main key, every csv_title[x] as second key
        Note: This function is not recommended if the first column has duplicate values
            
        Args:
            file: full path of csv file
            encode: default encoding parameter for pandas.read_csv
        Returns:
            openeuler_repo_owner:
                exp:
                openEuler-repos: {
                        'Sig': 'iSulad', 
                        'Team': 'EulerOS', 
                        'Owner': 'zengweifeng', 
                        'Email': 'zwfeng@huawei.com', 
                        'QA': nan, 
                        'maintainers': "['caihaomin', 'lifeng2221dd1', 'duguhaotian', 'jingxiaolu']"
                    }
        """

        res_data = dict()
        if not file.endswith('.csv'):
            logger.warning(f"{file} is not .csv file")

        try:
            csv_data = pd.read_csv(file, encoding=encoding)
        except FileNotFoundError as ferr:
            logger.error(f"{ferr.strerror}")
            return None

        # get csv_title of csv
        csv_title = list(csv_data.head(0))
        # logger.info(f"This is csv_title: {csv_title}")

        num_of_csv_title = len(csv_title)
        csv_data_lines = csv_data.values.tolist()

        for line in csv_data_lines:
            # logger.info(line)
            main_key = line[0]
            res_data[main_key] = dict()
            for idx in range(1, num_of_csv_title):
                res_data[main_key][csv_title[idx]] = line[idx]

        return res_data, csv_title
