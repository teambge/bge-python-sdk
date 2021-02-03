#-*- coding: utf-8 -*-

from .utils import major_version

if major_version <= 2:
    from UserDict import UserDict
else:
    from collections import UserDict


class Model(UserDict):
    """统一的接口返回数据包装模型类

    所有接口的返回值都使用本类进行封装。

    使用示例:

        >>> print(Model({}))
        Model({})
        >>> inst = Model({})
        >>> inst['demo'] = 1
        >>> print(inst.demo)
        1
        >>> print(inst['demo'])
        1
    """

    def __getattr__(self, name):
        try:
            return self.data[name]
        except KeyError:
            raise AttributeError

    def __str__(self):
        return 'Model(%s)' % self.data