#-*- coding: utf-8 -*-

from bgesdk.client import OAuth2

import logging
import pytest


base_url = 'https://pre.open.omgut.com'
client_id = 'wi0dCdFf4UldHClsBRHkPwFebEEbGuXPqpfKeICf'
client_secret = '9qmCoOHy7fRfRCJnF3vav807MW3m4TTlqMHiNmAOVWFXPBEYbzfBY8La0t6mir0YOyq1NuspZJEwBi876aSYCjwfJ9Akh4v0TIn7doPE4nAZJ3mpAgexhdrAUN1HV7vs'

@pytest.fixture(scope='session')
def redirect_url():
    return 'http://test.cn'


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
    access_token = 'zbvdg36O9ZCC7tTK5EO3U70KfKrgxq'
    return access_token


@pytest.fixture(scope='session')
def api(oauth2, access_token):
    return oauth2.get_api(access_token)


@pytest.fixture(scope='session')
def self_biosample_id():
    """本人的样品编号"""
    return 'E-B19941661351'

@pytest.fixture(scope='session')
def other_biosample_id():
    """其他人的样品编号"""
    return 'E-B19178067144'
