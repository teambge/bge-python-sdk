#-*- coding: utf-8 -*-

from bgesdk.client import OAuth2
from six.moves.urllib.parse import parse_qsl, urlparse

import logging
import os
import pytest
import requests
import six


ENDPOINT = os.environ.get('ENDPOINT')
CLIENT_ID = os.environ.get('CLIENT_ID')
CLIENT_SECRET = os.environ.get('CLIENT_SECRET')
REDIRECT_URI = os.environ.get('REDIRECT_URI')
AUTHORIZATION_EXTRA_QUERY = os.environ.get('AUTHORIZATION_EXTRA_QUERY')
SELF_BIOSAMPLE_ID = os.environ.get('SELF_BIOSAMPLE_ID')
SELF_META_BIOSAMPLE_ID = os.environ.get('SELF_META_BIOSAMPLE_ID')
OTHER_BIOSAMPLE_ID = os.environ.get('OTHER_BIOSAMPLE_ID')


@pytest.fixture(scope='session')
def redirect_uri():
    return REDIRECT_URI


@pytest.fixture(scope='session')
def authorization_url(oauth2, redirect_uri):
    authorization_url = oauth2.get_authorization_url(redirect_uri)
    return '&'.join((authorization_url, AUTHORIZATION_EXTRA_QUERY))


@pytest.fixture(scope='session')
def authorization_code(authorization_url):
    r = requests.get(authorization_url)
    assert r.status_code == 200
    query = dict(parse_qsl(urlparse(r.url).query))
    code = query.get('code')
    assert isinstance(code, six.string_types)
    return code


@pytest.fixture(scope='session')
def logger():
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    return logger


@pytest.fixture(scope='session')
def oauth2():
    return OAuth2(CLIENT_ID, CLIENT_SECRET, endpoint=ENDPOINT, max_retries=3)


@pytest.fixture(scope='session')
def access_token(oauth2, authorization_code, redirect_uri):
    token = oauth2.exchange_authorization_code(
        authorization_code,
        redirect_uri
    )
    return token.access_token


@pytest.fixture(scope='session')
def api(oauth2, access_token):
    return oauth2.get_api(access_token)


@pytest.fixture(scope='session')
def self_biosample_id():
    """本人的样品编号"""
    return SELF_BIOSAMPLE_ID


@pytest.fixture(scope='session')
def self_meta_biosample_id():
    """本人的 Meta 样品编号"""
    return SELF_META_BIOSAMPLE_ID


@pytest.fixture(scope='session')
def other_biosample_id():
    """其他人的样品编号"""
    return OTHER_BIOSAMPLE_ID
