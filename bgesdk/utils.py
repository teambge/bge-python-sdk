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
