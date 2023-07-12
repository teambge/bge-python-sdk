#-*- coding: utf-8 -*-

from bgesdk.error import APIError

import pytest


class TestOAuth2:

    def test_authorization_url_is_str(self, authorization_oauth2,
                                      redirect_uri):
        """获取用户授权页面链接"""
        url = authorization_oauth2.get_authorization_url(redirect_uri)
        assert isinstance(url, str)

    def test_invalid_code(self, authorization_oauth2):
        """错误的用户授权 code 和 redirect_uri"""
        with pytest.raises(APIError) as e:
            authorization_oauth2.exchange_authorization_code(
                'code',
                'http://test.cn'
            )
        assert e.value.code == 400
        assert e.value.msg == u'错误的请求'

    def test_invalid_access_token(self, authorization_oauth2):
        """错误的 access_token"""
        access_token = 'demo'
        api = authorization_oauth2.get_api(access_token)
        with pytest.raises(APIError) as e:
            api.get_user()
        assert e.value.code == 403
        assert e.value.msg == u'access_token 已失效或错误'
