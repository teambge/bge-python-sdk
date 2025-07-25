#-*- coding: utf-8 -*-

from bgesdk.error import ArgError

import pytest


class TestWGS:

    def test_report_collection(self, authorization_api, self_biosample_id):
        """测试获取解码基因报告结合详情"""
        ret = authorization_api.report_collection(self_biosample_id)
        assert 'report_collection_id' in ret
        assert 'report_collection_type' in ret
        assert 'biosample_id' in ret
        assert 'create_timestamp' in ret

    @pytest.mark.parametrize('domain', [
        'traits',
        'pgx',
        'common_disease_risk',
        'genetic_disease_mendelian',
        'genetic_disease_risk',
    ])
    def test_reports(self, authorization_api, self_biosample_id, domain):
        """测试获取解码基因报告列表数据"""
        ret = authorization_api.report_details(self_biosample_id, domain)
        assert 'total' in ret
        total = ret['total']
        assert isinstance(total, int)
        assert 'list' in ret
        list_ = ret['list']
        assert isinstance(list_, list)

    @pytest.mark.parametrize('domain', ['invalid_domain'])
    def test_reports_invalid_domain(self, authorization_api, self_biosample_id, domain):
        """测试非法 domain 数据获取解码基因报告列表数据"""
        with pytest.raises(ArgError) as e:
            authorization_api.report_details(self_biosample_id, domain)

    @pytest.mark.parametrize('domain', [
        'traits',
        'pgx',
        'common_disease_risk',
        'genetic_disease_mendelian',
        'genetic_disease_risk',
    ])
    def test_report(self, authorization_api, self_biosample_id, domain):
        ret = authorization_api.report_details(self_biosample_id, domain)
        if len(ret['list']) == 0:
            return
        report_detail = ret['list'][0]
        domain_version = report_detail['domain_version']
        report_id = report_detail['report_id']
        ret = authorization_api.report_detail(self_biosample_id, domain_version, report_id)
        assert ret.report_id == report_id

    def test_dictionaries(self, authorization_api, self_biosample_id):
        ret = authorization_api.dictionaries(self_biosample_id)
        assert isinstance(ret, list)
