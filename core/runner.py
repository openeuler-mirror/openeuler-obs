#/bin/env python3
# -*- encoding=utf8 -*-
"""
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
        print(kwargs)
    
    def run(self):
        """
        run main
        return:
        """
        log.debug("test")
        

