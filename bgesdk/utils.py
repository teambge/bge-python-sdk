#-*- coding: utf-8 -*-

import logging
import sys

try:
    from http.client import HTTPConnection
except ImportError:
    from httplib import HTTPConnection


def new_logger(name, verbose=False):
    logging.basicConfig()
    if verbose:
        HTTPConnection.debuglevel = 0
        requests_log = logging.getLogger("urllib3")
        requests_log.setLevel(logging.INFO)
        requests_log.propagate = False
        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)
        return logger
    else:
        logger = logging.getLogger(name)
        logger.setLevel(logging.INFO)
        return logger


def get_major_version():
    return sys.version_info.major


major_version = get_major_version()