#-*- coding: utf-8 -*-

from . import contants
from .error import APIError, BGEError
from .utils import major_version

from requests.adapters import HTTPAdapter
if major_version <= 2:
    from urlparse import urljoin
else:
    from urllib.parse import urljoin

import logging
import requests

logger = logging.getLogger()
DEFAULT_TIMEOUT = contants.HTTP_DEFAULT_TIMEOUT
MAX_RETRIES = contants.HTTP_MAX_RETRIES
HTTP_SESSION = requests.Session()
HTTP_SESSION.mount('http://', HTTPAdapter(max_retries=MAX_RETRIES))
HTTP_SESSION.mount('https://', HTTPAdapter(max_retries=MAX_RETRIES))


class HTTPRequest(object):
    """HTTP 请求类

    处理 SDK 接口的 HTTP 调用；

    Args:
        base_url (str): 平台基本地址，如 https://api.bge.genomics.cn；
    """

    def __init__(self, base_url):
        self.base_url = base_url
        self.headers = {}

    def set_authorization(self, access_token):
        """设置 Authorization 头部

        Args:
            access_token (str): 访问令牌
        """
        self.headers['Authorization'] = 'Bearer {}'.format(access_token)

    def get(self, path, params=None, timeout=None):
        """GET 接口请求

        Args:
            path (str): 请求路径
            params (dict, 非必填): GET 参数；
            timeout (int, 非必填): 请求超时时间；

        Returns:
            object: 请求返回值
        """
        return self._request('GET', path, params=params, timeout=timeout)

    def post(self, path, params=None, data=None, timeout=None):
        """POST

        Args:
            path (str): 请求路径
            params (dict, 非必填): GET 参数；
            data (dict, 非必填): POST 参数；
            timeout (int, 非必填): 请求超时时间；

        Returns:
            object: 请求返回值
        """
        return self._request(
            'POST', path, params=params, data=data, timeout=timeout)

    def _request(self, method, path, **kwargs):
        """发送 HTTP 请求

        Args:
            method (str): 请求方法
            path (str): 请求路径

        Raises:
            BGEError: SDK 错误
            APIError: API 错误

        Returns:
            object: 返回值
        """
        headers = self.headers
        url = urljoin(self.base_url, path)
        logger.debug('%s %s %s', method, url, kwargs)
        timeout = kwargs.get('timeout')
        if timeout is None:
            kwargs['timeout'] = DEFAULT_TIMEOUT
        resp = HTTP_SESSION.request(
            method=method, url=url, headers=headers, **kwargs)
        try:
            resp.raise_for_status()
        except requests.exceptions.HTTPError as e:
            raise BGEError('API request error: %s' % e)
        content_type_header = resp.headers.get('Content-Type', '')
        if 'application/json' not in content_type_header:
            return resp.text
        result = resp.json()
        data = result.get('data')
        code = result['code']
        msg = result['msg']
        if code != 0:
            raise APIError(code, msg, data)
        pagination = result.get('pagination')
        if pagination:
            # 相关接口分页返回方式升级后，可去除此处
            # TODO: upgrade in the future
            return data, pagination
        return data
