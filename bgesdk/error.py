#-*- coding: utf-8 -*-

from __future__ import unicode_literals


class BGEError(Exception):
    """SDK 错误"""


class APIError(BGEError):
    """接口错误"""

    def __init__(self, code, msg, data=None):
        self.code = code = int(code)
        self.msg = msg
        self.data = data
        self.result = result = {
            'code': code,
            'msg': msg,
            'data': data
        }
        super(APIError, self).__init__(result)
