# -*- coding: utf-8 -*-

from bgesdk.error import APIError

import pytest


class TestPhenotype:

    @pytest.mark.parametrize('data_element_id, stream_generate_time', [
        ('02393f70-c7e4-11e9-bfed-00163e104c79', '2021-03-02T10:00:00Z'),
    ])
    def test_unsupport_grant_type(self, authorization_api, logger,
                                  self_biosample_id, data_element_id,
                                  stream_generate_time):
        """该接口不支持授权码模式客户端调用"""
        with pytest.raises(APIError) as e:
            authorization_api.write_phenotype(
                self_biosample_id,
                data_element_id,
                stream_generate_time,
                {"name": "test"},
                duplicate_enabled=True
            )
        assert e.value.code == 40014
        assert e.value.msg == '本接口不支持授权码模式的应用访问'

    @pytest.mark.parametrize('data_element_id, stream_generate_time', [
        ('02393f70-c7e4-11e9-bfed-00163e104c79', '2021-03-02T10:00:00Z'),
    ])
    def test_write_phenotype(self, credentials_api, logger,
                             self_biosample_id, data_element_id,
                             stream_generate_time):
        """写入表型数据"""
        result = credentials_api.write_phenotype(
            self_biosample_id,
            data_element_id,
            stream_generate_time,
            {"name": "test"},
            duplicate_enabled=True
        )
        assert 'stream_id' in result

    @pytest.mark.parametrize('data_element_id, stream_generate_time', [
        ('unsetting_deid', '2021-03-02T10:00:00Z'),
    ])
    def test_write_unsetting_phenotype(self, credentials_api, logger,
                                       self_biosample_id, data_element_id,
                                       stream_generate_time):
        """写入表型数据"""
        with pytest.raises(APIError) as e:
            credentials_api.write_phenotype(
                self_biosample_id,
                data_element_id,
                stream_generate_time,
                {"name": "test"},
                duplicate_enabled=True
            )
        assert e.value.code == 41001
        assert e.value.msg == '参数错误'
