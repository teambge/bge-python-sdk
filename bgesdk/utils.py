#-*- coding: utf-8 -*-

import logging
import posixpath
import re
import time

from six.moves import http_client
from urllib.parse import unquote


filename_sub = re.compile(r'[\\/*?:"<>|]').sub


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


def sanitize_filename(url):
    """从URL中提取并清理文件名"""
    clean_url = url.split('#')[0]
    clean_url = clean_url.split('?')[0]
    clean_url = unquote(clean_url)
    filename = posixpath.basename(clean_url)
    if not filename or clean_url.endswith('/'):
        filename = f"untitled_{int(time.time())}"
    filename = filename_sub('_', filename)
    return filename.strip()
