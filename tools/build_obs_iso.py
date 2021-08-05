#!/bin/env python3
# -*- encoding=utf-8 -*-
"""
# **********************************************************************************
# Copyright (c) Huawei Technologies Co., Ltd. 2020-2020. All rights reserved.
# [openeuler-jenkins] is licensed under the Mulan PSL v1.
# You can use this software according to the terms and conditions of the Mulan PSL v1.
# You may obtain a copy of Mulan PSL v1 at:
#     http://license.coscl.org.cn/MulanPSL
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY OR FIT FOR A PARTICULAR
# PURPOSE.
# See the Mulan PSL v1 for more details.
# Author: miaokaibo
# Create: 2021-07-09
# **********************************************************************************
"""
import uuid
import logging
import json
import kafka
import kafka.errors as errors
import os
import jenkins
import datetime
import argparse
import time

logger = logging.getLogger("common")

par = argparse.ArgumentParser()

par.add_argument("-f", "--flag", help="jenkins or kafka", required=True)

par.add_argument("-p", "--project", help="obs project name", required=True)

par.add_argument("-d", "--datestr", help="obs start time, must be given when flag is jenkins", required=False)
par.add_argument("-u", "--user", help="jenkins user name, must be given when flag is jenkins", required=False)
par.add_argument("-w", "--passwd", help="jenkins user passwd, must be given when flag is jenkins", required=False)

par.add_argument("-b", "--broker", default=None, help="kafka broker, must be given when flag is kafka", required=False)
par.add_argument("-t", "--topic", default=None, help="kafka topic, must be given when flag is kafka", required=False)
par.add_argument("-pst", "--project_start_time", default=None, \
        help="project start time, must be given when flag is kafka", required=False)
par.add_argument("-pet", "--project_end_time", default=None, \
        help="project end time, must be given when flag is kafka", required=False)
par.add_argument("-ist", "--iso_start_time", default=None, \
        help="iso start time, must be given when flag is kafka", required=False)
par.add_argument("-iet", "--iso_end_time", default=None, \
        help="iso end time, must be given when flag is kafka", required=False)

args = par.parse_args()


class KafkaProducerProxy(object):
    """
    kafka 代理
    """
    def __init__(self, brokers, timeout=30):
        """

        :param brokers:
        :param timeout:
        """
                #key_serializer=encode('utf-8'),
        self._timeout = timeout
        self._kp = kafka.KafkaProducer(bootstrap_servers=brokers, 
                key_serializer=str.encode,
                value_serializer=lambda v:json.dumps(v).encode("utf-8"))

    def send(self, topic, key=None, value=None):
        """
        生产一条数据
        :param topic:
        :param key:
        :param value:
        :return:
        """
        try:
            logger.debug("kafka send: {}, {}".format(key, value))
            future = self._kp.send(topic, value=value, key=key)
            rs = future.get(timeout=self._timeout)
            logger.debug("kafka send result: {}".format(rs))
            return True
        except errors.KafkaTimeoutError:
            logger.exception("kafka send timeout exception")
            return False
        except errors.KafkaError:
            logger.exception("kafka send document exception")
            return False


def start_jenkins_after_obs(args):
    obs_pro = args.project
    obs_start_time = args.datestr
    cmd = 'osc prjresults {0} --csv | grep "aarch64/published" | grep "x86_64/published"'.format(obs_pro) 
    ret = os.popen(cmd).read()
    while not ret:
        ret = os.popen(cmd).read()
        time.sleep(60)
    obs_end_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    job_name = "Main-" + obs_pro.replace(":", "-") + "-build"
    ja = jenkins.Jenkins("https://openeulerci.osinfra.cn", username=args.user, password=args.passwd, timeout=120)
    num = ja.build_job("OBS-openEuler-build", parameters={"obs_start": obs_start_time, "obs_end": obs_end_time, \
            "iso_start": obs_end_time, "build_job": job_name, "obs_project": obs_pro})


def report(args):
    kp =  KafkaProducerProxy([args.broker])
    uid = str(uuid.uuid1())
    kp.send(args.topic, key=uid, value={"obs_project": args.project, \
            "archive_start": args.project_start_time, "archive_end": args.project_end_time, \
            "iso_start": args.iso_start_time, "iso_end": args.iso_end_time})


if args.flag == "jenkins":
    start_jenkins_after_obs(args)
elif args.flag == "kafka":
    report(args)
else:
    print("flag must be jenkins or kafka")
