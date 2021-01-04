# encoding: utf-8
from urllib.parse import urljoin

import requests
import logging

logger = logging.getLogger(__name__)


class ClientError(Exception):

    def __init__(self, error_info):
        self.error_info = error_info

    def __str__(self):
        return self.error_info


class BaseAPI(object):

    def __init__(self, timeout, base_url, grant_type, auth_token):
        self.timeout = timeout
        self.base_url = base_url
        self.grant_type = grant_type
        self.auth_token = auth_token

    def request(self, method, uri, **kwargs):
        if not uri.startswith(('http://', 'https://')):
            api_base_url = kwargs.pop('api_base_url', self.base_url)
            url = urljoin(api_base_url, uri)
        else:
            url = uri
        params = kwargs.setdefault('params', {})
        kwargs['headers'] = kwargs.setdefault('headers', {})
        kwargs['timeout'] = kwargs.setdefault('timeout', self.timeout)
        if self.grant_type == 'client_credentials':
            params['auth_token'] = self.auth_token
        res = requests.request(method=method, url=url, **kwargs)
        try:
            res.raise_for_status()
        except requests.exceptions.ReadTimeout:
            raise ClientError('request timeout')
        except requests.RequestException:
            raise ClientError('request api error')
        headers = res.headers
        if 'json' not in headers.get('Content-Type', ''):
            return res.text
        return res.json()

    def request_headers(self, access_token, **kwargs):
        """构建请求头
        
        :param access_token: 访问令牌
        :param kwargs: 
        :return: 请求头
        """
        Authorization = 'Bearer {}'.format(access_token)
        headers = { 'Authorization': Authorization }
        data = { **headers, **kwargs }
        request_headers = { 'headers': data }
        return request_headers

    def get(self, uri, params=None, **kwargs):
        """get 接口请求

        :param uri: 请求url
        :param params: get 参数（dict 格式）
        """
        if params is not None:
            kwargs['params'] = params
        return self.request('GET', uri, **kwargs)

    def post(self, uri, data=None, params=None, **kwargs):
        """post 接口请求

        :param uri: 请求url
        :param data: post 数据
        :param params: post接口中url问号后参数（dict 格式）
        """
        if data is not None:
            kwargs['data'] = data
        if params is not None:
            kwargs['params'] = params
        return self.request('POST', uri, **kwargs)
