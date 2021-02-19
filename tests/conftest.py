#-*- coding: utf-8 -*-

from bgesdk.client import OAuth2

import logging
import pytest
import os


ENDPOINT = os.environ.get('ENDPOINT')
CLIENT_ID = os.environ.get('CLIENT_ID')
CLIENT_SECRET = os.environ.get('CLIENT_SECRET')
REDIRECT_URL = os.environ.get('REDIRECT_URL')
ACCESS_TOKEN = os.environ.get('ACCESS_TOKEN')
SELF_BIOSAMPLE_ID = os.environ.get('SELF_BIOSAMPLE_ID')
OTHER_BIOSAMPLE_ID = os.environ.get('OTHER_BIOSAMPLE_ID')


@pytest.fixture(scope='session')
def redirect_url():
    return REDIRECT_URL


@pytest.fixture(scope='session')
def logger():
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    return logger


@pytest.fixture(scope='session')
def oauth2():
    return OAuth2(CLIENT_ID, CLIENT_SECRET, endpoint=ENDPOINT)


@pytest.fixture(scope='session')
def access_token():
    return ACCESS_TOKEN


@pytest.fixture(scope='session')
def api(oauth2, access_token):
    return oauth2.get_api(access_token)


@pytest.fixture(scope='session')
def self_biosample_id():
    """本人的样品编号"""
    return SELF_BIOSAMPLE_ID


@pytest.fixture(scope='session')
def other_biosample_id():
    """其他人的样品编号"""
    return OTHER_BIOSAMPLE_ID
