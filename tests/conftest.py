#-*- coding: utf-8 -*-

from bgesdk.client import OAuth2

import logging
import pytest


base_url = 'https://api.bge.genomics.cn'
client_id = 'demo'      # XXX change this for test
client_secret = 'demo'  # XXX change this for test


@pytest.fixture(scope='session')
def redirect_url():
    return 'http://test.cn'  # XXX change this for test


@pytest.fixture(scope='session')
def logger():
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    return logger


@pytest.fixture(scope='session')
def oauth2():
    return OAuth2(client_id, client_secret, base_url=base_url)


@pytest.fixture(scope='session')
def access_token():
    access_token = 'demo'  # XXX change this for test
    return access_token


@pytest.fixture(scope='session')
def api(oauth2, access_token):
    return oauth2.get_api(access_token)


@pytest.fixture(scope='session')
def self_biosample_id():
    """本人的样品编号"""
    return 'E-Bxxxxxxxx'  # XXX change this for test


@pytest.fixture(scope='session')
def other_biosample_id():
    """其他人的样品编号"""
    return 'E-B12341324'  # XXX change this for test
