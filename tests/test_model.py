#-*- coding: utf-8 -*-

from bgesdk.error import APIError

import pytest


class TestModel:

    @pytest.mark.parametrize('model_id', ['unknown_model_id'])
    def test_unknown_model(self, api, logger, model_id):
        """格式错误的 taxon 编号"""
        with pytest.raises(APIError) as e:
            api.invoke_model(model_id)
        assert e.value.code == 41202
        assert e.value.msg.startswith(u'BGE 私有接口错误: 模型不存在')
