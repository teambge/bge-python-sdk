#-*- coding: utf-8 -*-

from bgesdk.error import APIError

import pytest


class TestVariant:

    @pytest.mark.parametrize('rsids', ['rs333', 'rs1,rs2'])
    def test_valid_request(self, api, self_biosample_id, rsids):
        # 获取不归属于自己的样品的变异数据
        ret = api.get_variants(self_biosample_id, rsids)
        assert isinstance(ret, list), u'成功返回数据的类型必须为列表'

    @pytest.mark.parametrize('rsids', ['rs333', 'rs1,rs2'])
    def test_raise_errors(self, api, logger, other_biosample_id, rsids):
        """获取不归属于自己的样品的变异数据"""
        with pytest.raises(APIError) as e:
            api.get_variants(other_biosample_id, rsids)
        logger.debug(e.value)
        assert e.value.code == 41303
        assert e.value.msg == u'请提供本人的 biosample_id'

    @pytest.mark.parametrize(
        'rsids', ['rs1,rs2,rs3,rs4,rs5,rs6,rs7,rs8,rs9,rs10,rs11,rs12,rs13,'
                  'rs14,rs15,rs16,rs17,rs18,rs19,rs20,rs21,rs22,rs23,rs24,r'
                  's25,rs26,rs27,rs28,rs29,rs30,rs31,rs32,rs33,rs34,rs35,rs'
                  '36,rs37,rs38,rs39,rs40,rs41,rs42,rs43,rs44,rs45,rs46,rs4'
                  '7,rs48,rs49,rs50,rs51,rs52,rs53,rs54,rs55,rs56,rs57,rs58'
                  ',rs59,rs60,rs61,rs62,rs63,rs64,rs65,rs66,rs67,rs68,rs69,'
                  'rs70,rs71,rs72,rs73,rs74,rs75,rs76,rs77,rs78,rs79,rs80,r'
                  's81,rs82,rs83,rs84,rs85,rs86,rs87,rs88,rs89,rs90,rs91,rs'
                  '92,rs93,rs94,rs95,rs96,rs97,rs98,rs99,rs100,rs101'])
    def test_too_many_rsids(self, api, logger, self_biosample_id, rsids):
        """测试超出数量限制"""
        with pytest.raises(APIError) as e:
            api.get_variants(self_biosample_id, rsids)
        logger.debug(e.value)
        assert e.value.code == 41001
        assert e.value.msg == u'参数错误'

    @pytest.mark.parametrize(
        'rsids', ['333', '55333,rs3', 'srs3', 'rs3,,rs34', 'rs3,,', ''])
    def test_invalid_rsid(self, api, logger, self_biosample_id, rsids):
        """测试格式错误的变异位点"""
        with pytest.raises(APIError) as e:
            api.get_variants(self_biosample_id, rsids)
        logger.debug(e.value)
        assert e.value.code == 41001
        assert e.value.msg == u'参数错误'

    @pytest.mark.parametrize('biosample_id', ['demo', 'E-B112'])
    def test_invalid_biosample_id(self, api, logger, biosample_id):
        """测试不存在或者格式异常的的样品编号"""
        rsids = 'rs333'
        with pytest.raises(APIError) as e:
            api.get_variants(biosample_id, rsids)
        logger.debug(e.value)
        assert e.value.code == 41302
        assert e.value.msg == u'基因组报告不存在或未下机'
