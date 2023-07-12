#-*- coding: utf-8 -*-

from bgesdk.client import OAuth2
from six.moves.urllib.parse import parse_qsl, urlparse

import logging
import os
import pytest
import requests
import six


ENDPOINT = os.environ.get('ENDPOINT')

# Authorizaion Code
AUTHORIZATION_CLIENT_ID = os.environ.get('AUTHORIZATION_CLIENT_ID')
AUTHORIZATION_CLIENT_SECRET = os.environ.get('AUTHORIZATION_CLIENT_SECRET')
REDIRECT_URI = os.environ.get('REDIRECT_URI')
AUTHORIZATION_EXTRA_QUERY = os.environ.get('AUTHORIZATION_EXTRA_QUERY')
SELF_BIOSAMPLE_ID = os.environ.get('SELF_BIOSAMPLE_ID')
SELF_META_BIOSAMPLE_ID = os.environ.get('SELF_META_BIOSAMPLE_ID')
OTHER_BIOSAMPLE_ID = os.environ.get('OTHER_BIOSAMPLE_ID')

# Client Credentials
CREDENTIALS_CLIENT_ID = os.environ.get('CREDENTIALS_CLIENT_ID')
CREDENTIALS_CLIENT_SECRET = os.environ.get('CREDENTIALS_CLIENT_SECRET')


@pytest.fixture(scope='session')
def redirect_uri():
    return REDIRECT_URI


@pytest.fixture(scope='session')
def authorization_url(authorization_oauth2, redirect_uri):
    authorization_url = authorization_oauth2.get_authorization_url(
        redirect_uri
    )
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
def authorization_oauth2():
    return OAuth2(
        AUTHORIZATION_CLIENT_ID,
        AUTHORIZATION_CLIENT_SECRET,
        endpoint=ENDPOINT,
        max_retries=3
    )


@pytest.fixture(scope='session')
def authorization_access_token(authorization_oauth2, authorization_code,
                               redirect_uri):
    token = authorization_oauth2.exchange_authorization_code(
        authorization_code,
        redirect_uri
    )
    return token.access_token


@pytest.fixture(scope='session')
def authorization_api(authorization_oauth2, authorization_access_token):
    return authorization_oauth2.get_api(authorization_access_token)


@pytest.fixture(scope='session')
def credentials_oauth2():
    return OAuth2(
        CREDENTIALS_CLIENT_ID,
        CREDENTIALS_CLIENT_SECRET,
        endpoint=ENDPOINT,
        max_retries=3
    )


@pytest.fixture(scope='session')
def credentials_access_token(credentials_oauth2):
    token = credentials_oauth2.get_credentials_token()
    return token.access_token


@pytest.fixture(scope='session')
def credentials_api(credentials_oauth2, credentials_access_token):
    return credentials_oauth2.get_api(credentials_access_token)


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
