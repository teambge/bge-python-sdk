#-*- coding: utf-8 -*-

import logging

from six.moves import http_client


def new_logger(name, verbose=False):
    logging.basicConfig()
    if verbose:
        http_client.HTTPConnection.debuglevel = 0
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


def human_byte(size, dot=2):
    size = float(size)
    if size < pow(1024, 2):
        size = str(round(size / pow(1024, 1), dot)) + 'KB'
    elif pow(1024, 2) <= size < pow(1024, 3):
        size = str(round(size / pow(1024, 2), dot)) + 'MB'
    else:
        size = str(round(size / pow(1024, 3), dot)) + 'GB'
    return size
