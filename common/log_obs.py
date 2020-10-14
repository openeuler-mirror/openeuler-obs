#/bin/env python3
# -*- encoding=utf8 -*-
"""
logger for all scripts
"""
import os
import logging


def get_logger():
    """
    get logger object
    return: logger object
    """
    current_path = os.path.split(os.path.realpath(__file__))[0]
    logfile = os.path.join(current_path, "../log", "openeuler-obs.log")
    logger = logging.getLogger("")
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - '\
            '%(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s')
    file_handler = logging.FileHandler(logfile, mode='w')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.DEBUG)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)
    logger.addHandler(file_handler)
    return logger


logger = get_logger()
