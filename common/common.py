#/bin/env python3
# -*- encoding=utf8 -*-
"""
created by: miaokaibo
date: 2020-10-20 15:50
function for all
"""


def str_to_bool(s):
    """
    change string to bool
    """
    return s.lower() in ("yes", "true", "t", "1")
