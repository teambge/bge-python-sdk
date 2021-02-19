#-*- coding: utf-8 -*-

from .error import APIError, BGEError
from .utils import major_version, new_logger

from requests.adapters import HTTPAdapter
if major_version <= 2:
    from urlparse import urljoin
else:
    from urllib.parse import urljoin

import requests


class HTTPRequest(object):
    """HTTP 请求类

    处理 SDK 接口的 HTTP 调用；

    Args:
        endpoint (str): 平台基本地址，如 https://api.bge.genomics.cn；
        max_retries (数字, 非必填): 接口请求重试次数，默认值为 3；
        verbose (布尔, 非必填)：输出测试日志，默认值为 False；
    """


    def __init__(self, endpoint, max_retries=3, verbose=False):
        self.logger = new_logger(self.__class__.__name__, verbose=verbose)
        self.endpoint = endpoint
        self.headers = {}
        self.session = requests.Session()
        if max_retries is not None:
            self.session.mount(
                'http://', HTTPAdapter(max_retries=max_retries))
            self.session.mount(
                'https://', HTTPAdapter(max_retries=max_retries))

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
        return self._request(
            'GET', path, params=params, timeout=timeout)

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

    def _request(self, method, path, timeout=None, **kwargs):
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
        url = urljoin(self.endpoint, path)
        self.logger.debug(
            ('Request: \n\tmethod: %s\n\turl: %s\n\theaders: %s\n\ttimeout'
             ': %s\n\t**kwargs=%s'),
            method, url, headers, timeout, kwargs)
        try:
            resp = self.session.request(
                method=method, url=url, headers=headers, timeout=timeout,
                **kwargs)
            resp.raise_for_status()
        except requests.exceptions.HTTPError as e:
            raise BGEError('API request error: %s' % e)
        except requests.exceptions.ConnectionError as e:
            raise BGEError('Fail to connect: %s' % e)
        content_type_header = resp.headers.get('Content-Type', '')
        if 'application/json' not in content_type_header:
            result = resp.text
            self.logger.debug('Response: \n\t%s', result)
            return result
        result = resp.json()
        self.logger.debug('Response: \n\t%s', result)
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
