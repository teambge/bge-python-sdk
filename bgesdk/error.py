#-*- coding: utf-8 -*-

from __future__ import unicode_literals

import json


class BGEError(Exception):
    """SDK 错误"""


class APIError(BGEError):
    """接口错误"""

    def __init__(self, code, msg, data=None):
        self.code = int(code)
        self.msg = msg
        self.data = data
        super(APIError, self).__init__({
            'code': self.code,
            'msg': self.msg,
            'data': self.data
        })
