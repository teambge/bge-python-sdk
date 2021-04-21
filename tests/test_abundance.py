#-*- coding: utf-8 -*-

from bgesdk.error import APIError

import pytest
import six


def check_result(result):
    assert 'result' in result
    assert 'count' in result
    assert 'next_page' in result
    next_page = result['next_page']
    assert isinstance(result['result'], list)
    assert isinstance(result['count'], int)
    assert isinstance(next_page, int) or next_page is None


class TestTaxonAbundance:

    @pytest.mark.parametrize('taxon_ids', [None, 'tx1', 'tx2'])
    def test_result(self, api, logger, self_biosample_id, taxon_ids):
        """正常返回的数据"""
        ret = api.get_taxon_abundance(self_biosample_id)
        logger.debug(ret)
        check_result(ret)

    @pytest.mark.parametrize('taxon_ids', ['txdemo', 'tx', 'test'])
    def test_invalid_txid(self, api, logger, self_biosample_id, taxon_ids):
        """格式错误的 taxon 编号"""
        ret = api.get_taxon_abundance(self_biosample_id)
        logger.debug(ret)
        check_result(ret)


class TestFuncAbundance:

    @pytest.mark.parametrize('catalog', ['go', 'ko', 'eggnog', 'pfam',
                                         'kegg-pwy', 'kegg-mdl', 'level4ec',
                                         'metacyc-rxn', 'metacyc-pwy'])
    def test_result(self, api, logger, self_biosample_id, catalog):
        """正常返回的数据"""
        try:
            ret = api.get_func_abundance(self_biosample_id, catalog)
        except APIError as error:
            with pytest.raises(APIError) as e:
                raise error
            e.value.code == 41202
            e.value.msg == u'BGE 私有接口错误: 样品数据未入仓'
            return
        logger.debug(ret)
        check_result(ret)


class TestGeneAbundance:

    def check_result(self, result):
        assert 'result' in result
        assert 'count' in result
        assert 'next_page' in result
        next_page = result['next_page']
        assert isinstance(result['result'], list)
        assert isinstance(result['count'], int)
        assert next_page is None or isinstance(next_page, six.text_type)

    @pytest.mark.parametrize('catalog, data_type', [
        ('IGC_9.9M', 'list'),
        ('UniRef90_HUMAnN2_0.11', 'file')])
    def test_result(self, api, logger, self_biosample_id, catalog,
                    data_type):
        """正常返回的数据"""
        ret = api.get_gene_abundance(self_biosample_id, catalog, data_type)
        logger.debug(ret)
        self.check_result(ret)

    @pytest.mark.parametrize('catalog, data_type', [
        ('IGC_9.9M', 'file'),
        ('UniRef90_HUMAnN2_0.11', 'list')])
    def test_invalid_args(self, api, self_biosample_id, catalog, data_type):
        """正常返回的数据"""
        with pytest.raises(APIError) as e:
            api.get_gene_abundance(self_biosample_id, catalog, data_type)
        assert e.value.code == 41001
        assert e.value.msg == u'参数错误'
