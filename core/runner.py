#/bin/env python3
# -*- encoding=utf8 -*-
"""
created by: miaokaibo
date: 2020-10-20 9:55

main script for running
"""
from common.log_obs import log


class Runner(object):
    """
    Runner class for all action
    """
    def __init__(self, **kwargs):
        """
        init action
        kwargs: dict, init dict by "a"="A" style
        return:
        """
        self.kwargs = kwargs
        print(self.kwargs)
    
    def run(self):
        """
        run main
        return:
        """
        log.debug("test")
        

