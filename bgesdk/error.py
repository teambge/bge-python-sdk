#-*- coding: utf-8 -*-

import json


class BGEError(Exception):
    """SDK 错误"""


class APIError(BGEError):
    """接口错误"""

    def __init__(self, code, msg, data=None):
        self.code = int(code)
        self.msg = msg
        self.data = data
        super(BGEError, self).__init__(json.dumps({
            'code': code,
            'msg': msg,
            'data': data
        }, indent=4, ensure_ascii=False))