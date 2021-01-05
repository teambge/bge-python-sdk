# encoding: utf-8
from urllib.parse import urljoin, urlencode

from BGE_sdk.base import BaseAPI
from BGE_sdk.base import ClientError

import json


class BGEApi(BaseAPI):

    def __init__(self, client_id, client_secret, redirect_uri, grant_type,
                 auth_token='', timeout=16.,
                 base_url='https://pre.open.omgut.com'):
        """
        :param client_id: 开发者在 BGE 开放平台 创建的应用的 client_id（必填）；
        :param client_secret: 开发者在 BGE 开放平台 创建的应用的 client_secret（必填）;
        :param redirect_uri: 用户授权后的回调地址（必填）;
        :param grant_type: 授权方式，授权码模式为 "authorization_code"，客户端模式
        为 "client_credentials"（必填）；
        :param auth_token: 用户令牌，客户端授权模式访问接口需要提供 auth_token;
        :param base_url: 开放平台域名;
        """
        super(BGEApi, self).__init__(
            timeout, base_url, grant_type, auth_token
        )
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.grant_type = grant_type
        self.base_url = base_url

    def authorization_url(self, response_type='code', state='', *scope):
        """获取用户授权地址
        
        :param response_type: 响应类型值为'code';
        :param state: 可以为任意值，获取授权后会原样返回该值;
        :param scope: 参数为权限数据域,不提供参数时代表第三方应用要求全部数据权限,
        也可提供任意第三方应用在 BGE 应用平台申请到的 scope；
        :return: 用户授权链接
        """
        path = '/oauth2/authorize'
        url = urljoin(self.base_url, path)
        scope = ' '.join(scope)
        params = {
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'response_type': response_type,
            'state': state,
        }
        if scope:
            params['scope'] = scope
        params = urlencode(params)
        authorization_url = '{}?{}'.format(url, params)
        return authorization_url

    def get_access_token(self, code='', grant_type='authorization_code'):
        """获取令牌
        
        :param code: 回调地址 redirect_uri 获取到的参数授权码 code，
        客户端模式不需要提供；
        :return: 
        """
        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'grant_type': grant_type
        }
        if grant_type == 'authorization_code':
            data['redirect_uri'] = self.redirect_uri
            data['code'] = code
        elif grant_type not in ['authorization_code',
                                'client_credentials']:
            raise ClientError('暂不支持其他授权方式')

        return self.post(
            '/oauth2/access_token',
            data
        )

    def refresh_token(self, refresh_token, grant_type='refresh_token'):
        """刷新令牌 access_token
       
        :param refresh_token: 授权码模式所获得的 refresh_token（必填）；
        :return: 新的访问令牌
        """
        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'grant_type': grant_type,
            'refresh_token': refresh_token
        }
        return self.post(
            '/oauth2/access_token',
            data
        )

    def get_user_info(self, access_token):
        """获取用户信息
        
        :param access_token: 访问令牌（必填）；
        :return: 用户信息;
        """
        headers = self.request_headers(access_token)
        return self.get(
            '/user',
            **headers
        )

    def get_variants(self, access_token, biosample_id, *rsids):
        """根据rsid查询变异位点信息
        
        :param access_token: 访问令牌（必填）;
        :param biosample_id: 生物样品编号（必填）；
        :param rsids: 多个 rs 编号（必填）；如：rs1229984,rs1421085；最多一次提供100个；
        :return: 变异位点信息
        """
        rsids = ','.join(rsids)
        params = { 'rsids': rsids, 'biosample_id': biosample_id }
        headers = self.request_headers(access_token)
        return self.get(
            '/variants',
            params,
            **headers
        )

    def get_sample(self, access_token, biosample_id=None, **kwargs):
        """
        授权码模式: 可通过本接口获取授权用户的样品; 
        客户端模式: 可通过本接口获取客户端应用通过注册接口注册(或预先生成)的样品
        
        :param access_token: 访问令牌（必填）；
        :param biosample_id: 生物样品编号
        :return: 某个样品数据
        """
        headers = self.request_headers(access_token)
        if biosample_id:
            url = '/samples/{}'.format(biosample_id)
        else:
            url = '/samples'
        return self.get(
            url,
            kwargs,
            **headers
        )

    def register_sample(self, access_token, external_sample_id,
                        biosample_site, project_id, **kwargs):
        """注册样品
        
        :param access_token: 访问令牌（必填）
        :param external_sample_id: 外部生物样品id（必填）;
        :param biosample_site: 采样部位（必填）;
        :param project_id: 项目编号（必填）;
        :param kwargs: 其他非必填数据，例：library_id="HWJBAYTGAA170328-18";
        :return: 生物样品编号
        """
        required_data = {
            'external_sample_id': external_sample_id,
            'biosample_site': biosample_site,
            'project_id': project_id
        }
        data = { **required_data, **kwargs }
        headers = self.request_headers(access_token)
        return self.post(
            '/sample_id/register',
            data,
            **headers
        )

    def improve_sample_info(self, access_token, biosample_id, **kwargs):
        """补充样品中未被赋值的信息，已赋值数据无法变更
        
        :param access_token: 访问令牌（必填）；
        :param biosample_id: 生物样品编号（必填）
        :param kwargs: 需要赋值的字段和值;
        :return: 
        """
        headers = self.request_headers(access_token)
        return self.post(
            '/sample_id/{}/improve'.format(biosample_id),
            kwargs,
            **headers
        )

    def get_microbiome_taxon_abundance(self, access_token, biosample_id,
                                       **kwargs):
        """获取类群丰度
        
        :param access_token: 访问令牌（必填）；
        :param biosample_id: 生物样品编号（必填）;
        :param kwargs: taxon_id BGE 物种编号，page 当前页码，limit 页返回的条数;
        :return: 类群丰度数据详情
        """
        headers = self.request_headers(access_token)
        data = { 'biosample_id': biosample_id }
        params = { **data, **kwargs }
        return self.get(
            '/microbiome/taxon_abundance',
            params,
            **headers
        )

    def get_microbiome_func_abundance(self, access_token, biosample_id,
                                      catalog, **kwargs):
        """获取功能丰度
        
        :param access_token: 访问令牌（必填）
        :param biosample_id: 生物样品编号（必填）;
        :param catalog: 目录标签（必填）;
        :param kwargs: ids BGE物种功能编号，多个值以逗号隔开,limit 一页返回的条数,
        next_page 下一页参数，用于获取下一页数据;
        :return: 功能丰度数据详情
        """
        headers = self.request_headers(access_token)
        data = { 'biosample_id': biosample_id, 'catalog': catalog }
        params = { **data, **kwargs }
        return self.get(
            '/microbiome/func_abundance',
            params,
            **headers
        )

    def get_microbiome_gene_abundance(self, access_token, biosample_id,
                                      catalog, data_type, **kwargs):
        """获取基因丰度
        
        :param access_token: 访问令牌（必填）；
        :param biosample_id: 生物样品编号（必填）;
        :param catalog: 分类标签（必填）;
        :param data_type: 返回数据类型（必填）;
        :param kwargs: ids BGE物种功能编号，多个值以逗号隔开,limit 一页返回的条数,
        next_page 下一页参数，用于获取下一页数据;
        :return: 基因丰度数据详情
        """
        headers = self.request_headers(access_token)
        data = {
            'biosample_id': biosample_id,
            'catalog': catalog,
            'data_type': data_type
        }
        params = { **data, **kwargs }
        return self.get(
            '/microbiome/gene_abundance',
            params,
            **headers
        )

    def upload_file(self, access_token):
        """获取文件上传授权，获取的授权仅包括当前目录（不含子目录）下的文件读、写权限；
        
        :param access_token: 访问令牌（必填）；
        :return: 授权数据 
        """
        headers = self.request_headers(access_token)
        return self.post(
            '/sts/token',
            **headers
        )

    def download_file(self, access_token, object_name, **kwargs):
        """获取阿里云OSS（对象存储）中的文件下载地址
        
        :param access_token: 访问令牌（必填）；
        :param object_name: OSS对象（必填）;
        :param kwargs: region 区域,expiration_time 下载地址过期时间;
        :return: 文件下载地址
        """
        headers = self.request_headers(access_token)
        required_data = {
            'object_name': object_name
        }
        data = { **required_data, **kwargs }

        return self.post(
            '/oss/sign_url',
            data,
            **headers
        )

    def get_model(self, access_token, model_id, biosample_id, **kwargs):
        """获取模型
        
        :param access_token: 访问令牌（必填）；
        :param model_id: 模型编号（必填）；
        :param biosample_id: 生物样品编号（必填）；
        :return: 任务id，时间和状态
        """
        headers = self.request_headers(access_token)
        data = { 'biosample_id': biosample_id }
        params = { **data, **kwargs }
        return self.get(
            '/model/{}'.format(model_id),
            params,
            **headers
        )
