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
    def test_result(self, authorization_api, logger, self_meta_biosample_id,
                    taxon_ids):
        """正常返回的数据"""
        ret = authorization_api.get_taxon_abundance(self_meta_biosample_id)
        logger.debug(ret)
        check_result(ret)

    @pytest.mark.parametrize('taxon_ids', ['txdemo', 'tx', 'test'])
    def test_invalid_txid(self, authorization_api, logger,
                          self_meta_biosample_id, taxon_ids):
        """格式错误的 taxon 编号"""
        ret = authorization_api.get_taxon_abundance(
            self_meta_biosample_id,
            taxon_ids
        )
        logger.debug(ret)
        check_result(ret)
        assert ret['count'] == 0

    @pytest.mark.parametrize('taxon_ids', ['txid815'])
    def test_valid_txid(self, authorization_api, logger,
                        self_meta_biosample_id, taxon_ids):
        """在平台类群丰度 taxon_id 集合内的编号"""
        ret = authorization_api.get_taxon_abundance(
            self_meta_biosample_id,
            taxon_ids
        )
        logger.debug(ret)
        check_result(ret)
        assert ret['count'] == 1

    @pytest.mark.parametrize('taxon_ids', ['txid1323'])
    def test_outter_txid(self, authorization_api, logger,
                         self_meta_biosample_id, taxon_ids):
        """不在平台类群丰度 taxon_id 集合内的编号"""
        ret = authorization_api.get_taxon_abundance(
            self_meta_biosample_id,
            taxon_ids
        )
        logger.debug(ret)
        check_result(ret)
        assert ret['count'] == 0


class TestFuncAbundance:

    @pytest.mark.parametrize('catalog', ['go', 'ko', 'eggnog', 'pfam',
                                         'kegg-pwy', 'kegg-mdl', 'level4ec',
                                         'metacyc-rxn', 'metacyc-pwy'])
    def test_result(self, authorization_api, logger, self_meta_biosample_id,
                    catalog):
        """正常返回的数据"""
        ret = authorization_api.get_func_abundance(
            self_meta_biosample_id,
            catalog
        )
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
        ('UniRef90_HUMAnN2_0.11', 'file')])
    def test_result(self, authorization_api, logger, self_meta_biosample_id,
                    catalog, data_type):
        """正常返回的数据"""
        ret = authorization_api.get_gene_abundance(
            self_meta_biosample_id,
            catalog,
            data_type
        )
        logger.debug(ret)
        self.check_result(ret)

    @pytest.mark.parametrize('catalog, data_type', [
        ('UniRef90_HUMAnN2_0.11', 'list')])
    def test_invalid_args(self, authorization_api, self_meta_biosample_id,
                          catalog, data_type):
        """正常返回的数据"""
        with pytest.raises(APIError) as e:
            authorization_api.get_gene_abundance(
                self_meta_biosample_id,
                catalog,
                data_type
            )
        assert e.value.code == 41001
        assert e.value.msg == u'参数错误'
