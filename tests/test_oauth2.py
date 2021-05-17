#-*- coding: utf-8 -*-

from bgesdk.error import APIError

import pytest


class TestOAuth2:

    def test_authorization_url_is_str(self, oauth2, redirect_url):
        """获取用户授权页面链接"""
        url = oauth2.get_authorization_url(redirect_url)
        assert isinstance(url, str)

    def test_invalid_code(self, oauth2):
        """错误的用户授权 code 和 redirect_uri"""
        with pytest.raises(APIError) as e:
            oauth2.exchange_authorization_code('code', 'http://test.cn')
        assert e.value.code == 400
        assert e.value.msg == u'非法请求: invalid_grant'

    def test_invalid_access_token(self, oauth2):
        """错误的 access_token"""
        access_token = 'demo'
        api = oauth2.get_api(access_token)
        with pytest.raises(APIError) as e:
            api.get_user()
        assert e.value.code == 403
        assert e.value.msg == u'access_token 已失效或错误'
