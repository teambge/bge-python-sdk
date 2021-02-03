#-*- coding: utf-8 -*-

from bgesdk.error import APIError

import pytest


class TestUser:

    def test_get_user(self, oauth2):
        """无效 access_token 调用接口报错"""
        api = oauth2.get_api('demo')
        with pytest.raises(APIError) as e:
            api.get_user()
        assert e.value.code == 403
        assert e.value.msg == u'access_token 已失效或错误'
