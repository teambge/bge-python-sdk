#-*- coding: utf-8 -*-

from bgesdk.error import APIError

import pytest


class TestSample:

    def check_samples(self, result):
        assert 'result' in result
        assert 'count' in result
        assert 'next_page' in result
        next_page = result['next_page']
        assert isinstance(result['result'], list)
        assert isinstance(result['count'], int)
        assert isinstance(next_page, int) or next_page is None

    @pytest.mark.parametrize('biosample_sites', range(1, 16))
    def test_valid_biosample_sites(self, authorization_api,
                                   biosample_sites):
        """在参数 choices 范围限制内"""
        ret = authorization_api.get_samples(biosample_sites=biosample_sites)
        self.check_samples(ret)

    @pytest.mark.parametrize('biosample_sites', [0, '0,3', 20, '3,20', 'x'])
    def test_invalid_biosample_sites(self, authorization_api,
                                     biosample_sites):
        """超出参数 choices 范围限制"""
        with pytest.raises(APIError) as e:
            authorization_api.get_samples(biosample_sites=biosample_sites)
        assert e.value.code == 41001
        assert e.value.msg == u'参数错误'

    @pytest.mark.parametrize('omics', range(1, 3))
    def test_valid_omics(self, authorization_api, omics):
        """在参数 choices 范围限制内"""
        ret = authorization_api.get_samples(omics=omics)
        self.check_samples(ret)

    @pytest.mark.parametrize('omics', [0, '0,3', 4, '3,4', 'x'])
    def test_invalid_omics(self, authorization_api, omics):
        """超出参数 choices 范围限制"""
        with pytest.raises(APIError) as e:
            authorization_api.get_samples(omics=omics)
        assert e.value.code == 41001
        assert e.value.msg == u'参数错误'

    @pytest.mark.parametrize('organisms', range(1, 3))
    def test_valid_organisms(self, authorization_api, organisms):
        """在参数 choices 范围限制内"""
        ret = authorization_api.get_samples(organisms=organisms)
        self.check_samples(ret)

    @pytest.mark.parametrize('organisms', [0, '0,3', 4, '3,4', 'x'])
    def test_invalid_organisms(self, authorization_api, organisms):
        """超出参数 choices 范围限制"""
        with pytest.raises(APIError) as e:
            authorization_api.get_samples(organisms=organisms)
        assert e.value.code == 41001
        assert e.value.msg == u'参数错误'

    def test_result(self, authorization_api, logger):
        """返回值"""
        ret = authorization_api.get_samples(limit=1)
        self.check_samples(ret)
        next_page = ret['next_page']
        if next_page is not None:
            ret = authorization_api.get_samples(page=next_page)
            self.check_samples(ret)

    @pytest.mark.parametrize('external_sample_ids', [None, ''])
    def test_non_externals(self, authorization_api, logger,
                           external_sample_ids):
        """空的外部编号"""
        project_id = 'P-M0000000000'
        biosample_site = 10
        with pytest.raises(APIError) as e:
            authorization_api.externals(
                external_sample_ids,
                biosample_site,
                project_id
            )
        assert e.value.code == 41001
        assert e.value.msg == u'参数错误'
