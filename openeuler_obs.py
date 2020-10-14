 #/bin/env python3
# -*- encoding=utf8 -*-
"""
main script for openeuler-obs
"""
import argparse
import os
import sys
from common.log_obs import log
from core.runner import Runner


#ArgumentParser
par = argparse.ArgumentParser()
par.add_argument("-o", "--obs", help="Local path of obs_meta repository", required=True)
par.add_argument("-b", "--branch", default=None, help="gitee repostory branch name", required=False)
par.add_argument("-p", "--project", default=None, help="obs project name", required=False)
args = par.parse_args()

#apply
obs_meta_path = args.obs
log.info(obs_meta_path)
run = Runner(obs_path=args.obs, project=args.project)
run.run()
