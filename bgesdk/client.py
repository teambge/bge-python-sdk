#-*- coding: utf-8 -*-

"""
BGE 开放平台 SDK 客户端模块。

当前模块提供了两个主要的类 OAuth2 和 API,他们分别提供了对 BGE 开放平台的 OAuth2 相关
接口和其他接口的调用方法。

使用示例:

    >>> oauth2 = OAuth2(
            'demo', 'demo', endpoint='https://api.bge.genomics.cn')
    >>> token = oauth2.get_credentials_token()
    >>> api = oauth2.get_api(token.access_token)
    >>> api.invoke_model('demo_model_id')
    Model({...})
"""

from . import constants
from . import models
from .error import BGEError
from .fs import FileItem
from .http import HTTPRequest
from .utils import new_logger, human_byte

from aliyunsdkcore.auth.credentials import StsTokenCredential
from aliyunsdkcore.client import AcsClient
from posixpath import split, join, isdir, isfile
from requests_toolbelt.multipart import encoder
from six import text_type
from six.moves.urllib.parse import urljoin, urlencode

import json
import os
import oss2
import requests
import sys


__all__ = ['OAuth2', 'API', 'endpoints']

endpoints = [v['endpoint'] for v in constants.ENDPOINTS]

ACCESS_TOKEN_API = '/oauth2/access_token'


def progress_callback(bytes_consumed, total_bytes):
    sys.stdout.write(
        '\r文件大小: {}, 上传进度: {}%, 已上传 {}'.format(
            human_byte(total_bytes, 2),
            '%.2f' % ((bytes_consumed / total_bytes) * 100),
            human_byte(bytes_consumed, 2)
    ))
    sys.stdout.flush()


def alive(self):
    """检查服务可用性

    Returns:
        布尔型: True 代表可用, False 代表不可用
    """
    timeout = self.timeout
    verbose = self.verbose
    max_retries = self.max_retries
    request = HTTPRequest(
        self.endpoint, max_retries=max_retries, verbose=verbose)
    try:
        request.get('/ping', timeout=timeout)
    except Exception:
        return False
    return True


class OAuth2(object):
    """OAuth2 授权客户端类。

    管理关于 OAuth2 相关接口的调用,包括获取授权页面地址、授权码交换访问令牌等;

    Args:
        client_id (字符串): 第三方客户端 client_id;
        client_secret (字符串): 第三方客户端 client_secret;
        endpoint (字符串, 非必填): 平台对外服务的访问域名,
                                 默认值为 https://api.bge.genomics.cn;
        max_retries (数字, 非必填): 接口请求重试次数,默认值为 3;
        timeout (数字, 非必填): 接口请求默认超时间,默认值为 None;
        verbose (布尔, 非必填): 输出测试日志,默认值为 False;
    """

    alive = alive

    def __init__(self, client_id, client_secret, endpoint=None,
                 max_retries=None, timeout=None, verbose=False):
        self.client_id = client_id
        self.client_secret = client_secret
        if endpoint is None:
            endpoint = constants.DEFAULT_ENDPOINT
        self.endpoint = endpoint
        if max_retries is not None:
            max_retries = int(max_retries)
        self.max_retries = max_retries
        if timeout is not None:
            timeout = int(timeout)
        self.timeout = timeout
        self.verbose = verbose
        self.logger = new_logger(self.__class__.__name__, verbose=verbose)

    def get_authorization_url(self, redirect_uri, state=None, scopes=None):
        """获取用户授权页链接地址。

        Args:
            redirect_uri (str): 回调地址;
            state (str, 非必填): 第三方自定义信息,返回授权码时原样返回,
                                默认值为 None;
            scopes (list, 非必填): 权限范围,支持多个。默认值为 None;

        Returns:
            str: 用户授权页面地址;
        """
        params = {
            "client_id": self.client_id,
            "response_type": "code",
            "redirect_uri": redirect_uri
        }
        if scopes is not None:
            params['scope'] = " ".join(scopes)
        if state is not None:
            params["state"] = state
        qs = urlencode(params)
        return '?'.join((urljoin(self.endpoint, '/oauth2/authorize'), qs))

    def exchange_authorization_code(self, code, redirect_uri):
        """用户授权码交换访问令牌

        Args:
            code (str): 用户授权后平台返回的授权码;
            redirect_uri (str): 回调地址;

        Returns:
            AuthorizationCodeToken: 与授权用户关联的访问令牌,同时包含有刷新令牌、
                                    过期时间等信息;
        """
        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'grant_type': constants.GRANT_AUTHORIZATION_CODE,
            'redirect_uri': redirect_uri,
            'code': code
        }
        timeout = self.timeout
        verbose = self.verbose
        max_retries = self.max_retries
        request = HTTPRequest(
            self.endpoint, max_retries=max_retries, verbose=verbose)
        result = request.post(
            ACCESS_TOKEN_API, data=data, timeout=timeout)
        return models.AuthorizationCodeToken(self, result)

    def exchange_refresh_token(self, refresh_token):
        """刷新令牌 access_token

        Args:
            refresh_token (str): 授权码模式所获得的 refresh_token;

        Returns:
            Model: 新的令牌数据;
        """
        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token
        }
        timeout = self.timeout
        verbose = self.verbose
        max_retries = self.max_retries
        request = HTTPRequest(
            self.endpoint, max_retries=max_retries, verbose=verbose)
        result = request.post(
            ACCESS_TOKEN_API, data=data, timeout=timeout)
        return models.AuthorizationCodeToken(self, result)

    def get_credentials_token(self):
        """客户端授权模式下获取访问令牌

        Returns:
            Model: 访问令牌,包含 access_token、过期时间等;
        """
        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'grant_type': constants.GRANT_TYPE_CREDENTIALS
        }
        timeout = self.timeout
        verbose = self.verbose
        max_retries = self.max_retries
        request = HTTPRequest(
            self.endpoint, max_retries=max_retries, verbose=verbose)
        result = request.post(
            ACCESS_TOKEN_API, data=data, timeout=timeout)
        return models.ClientCredentialsToken(self, result)

    def get_api(self, access_token):
        """获取平台 API 调用客户端对象

        Args:
            access_token (str): 访问令牌;

        Returns:
            API: API 对象;
        """
        return API(
            access_token,
            endpoint=self.endpoint,
            max_retries=self.max_retries,
            timeout=self.timeout,
            verbose=self.verbose)


class API(object):
    """BGE 开放平台接口调用客户端

    Args:
        access_token (str): 访问令牌;
        endpoint (字符串, 非必填): 平台对外服务的访问域名,默认值为 pro-main;
        max_retries (数字, 非必填): 接口请求重试次数,默认值为 3;
        timeout (数字, 非必填): 接口请求默认超时间,默认值为 18;
        verbose (布尔, 非必填): 输出测试日志,默认值为 False;
    """

    alive = alive
    token_type = 'Bearer'

    def __init__(self, access_token, endpoint=None, max_retries=None,
                 timeout=None, verbose=False):
        self.access_token = access_token
        if endpoint is None:
            endpoint = constants.DEFAULT_ENDPOINT
        self.endpoint = endpoint
        if max_retries is not None:
            max_retries = int(max_retries)
        self.max_retries = max_retries
        if timeout is not None:
            timeout = int(timeout)
        self.timeout = timeout
        self.verbose = verbose
        self.logger = new_logger(self.__class__.__name__, verbose=verbose)

    def introspect(self):
        """验证当前使用的 access_token 有效性

        Returns:
            Model: Token 元数据;
        """
        timeout = self.timeout
        verbose = self.verbose
        max_retries = self.max_retries
        request = HTTPRequest(
            self.endpoint, max_retries=max_retries, verbose=verbose)
        request.set_authorization(self.token_type, self.access_token)
        result = request.get('/oauth2/introspect', params={
            'token': self.access_token
        }, timeout=timeout)
        return models.Model(result)

    def get_user(self, **params):
        """获取用户信息

        Returns:
            Model: 用户数据;
        """
        timeout = self.timeout
        verbose = self.verbose
        max_retries = self.max_retries
        request = HTTPRequest(
            self.endpoint, max_retries=max_retries, verbose=verbose)
        request.set_authorization(self.token_type, self.access_token)
        result = request.get('/profile', params=params, timeout=timeout)
        return models.Model(result)

    def get_overview(
            self,
            idcard=None,
            phone=None,
            biosample_id=None,
            project_id=None,
            external_sample_id=None,
            **kwargs,
        ):
        """获取用户数据概览

        Args:
            idcard (str, 非必填): 身份证；
            phone (str, 非必填): 手机号；提供了参数 phone，禁止再提供 biosample_id、
                project_id、external_sample_id；
            biosample_id (str, 非必填): BGE 样本编号；提供了参数 biosample_id，禁
                止再提供 phone、project_id、external_sample_id；
            project_id (str, 非必填): BGE 项目编号；提供了参数 project_id 必须提
                供 external_sample_id，且 phone 和 biosample_id 必须为空；
            external_sample_id (str, 非必填): 外部样本编号；提供了参数
                external_sample_id 必须提供 project_id，且 phone 和
                biosample_id 必须为空；

        Returns:
            Model: 用户数据概览;
        """
        data = {}
        data.update(kwargs)
        if phone and (biosample_id or project_id or external_sample_id):
            raise BGEError(
                'If the phone parameter is provided, the biosample_id, '
                'project_id, and external_sample_id are prohibited.'
            )
        elif biosample_id and (phone or project_id or external_sample_id):
            raise BGEError(
                'If the biosample_id parameter is provided, the phone, '
                'project_id, and external_sample_id are prohibited.'
            )
        else:
            if (not project_id and external_sample_id) or \
                    (project_id and not external_sample_id):
                raise BGEError(
                    'The project_id and external_sample_id must be provided'
                    ' together.'
                )
            if project_id and external_sample_id and (phone or biosample_id):
                raise BGEError(
                    'The provided parameters external_sample_id must provid'
                    'e the project_id, and the phone and biosample_id must '
                    'be empty.'
                )
        data.update({
            'idcard': idcard,
            'phone': phone,
            'biosample_id': biosample_id,
            'project_id': project_id,
            'external_sample_id': external_sample_id,
        })
        timeout = self.timeout
        verbose = self.verbose
        max_retries = self.max_retries
        request = HTTPRequest(
            self.endpoint, max_retries=max_retries, verbose=verbose)
        request.set_authorization(self.token_type, self.access_token)
        result = request.post('/user/overview', data=data, timeout=timeout)
        return models.Model(result)

    def get_variants(self, biosample_id, rsids, **params):
        """根据rsid查询变异位点信息

        Args:
            biosample_id (str): 生物样品编号;
            rsids (str): 多个 rs 编号,逗号分割(必填);如: rs1229984;
                         最多一次提供100个;

        Returns:
            list: 变异位点信息;
        """
        if biosample_id:
            biosample_id = biosample_id.upper().strip()
        params.update({
            'rsids': rsids.strip(),
            'biosample_id': biosample_id
        })
        timeout = self.timeout
        verbose = self.verbose
        max_retries = self.max_retries
        request = HTTPRequest(
            self.endpoint, max_retries=max_retries, verbose=verbose)
        request.set_authorization(self.token_type, self.access_token)
        result = request.get('/variants', params=params, timeout=timeout)
        return models.ListModel(result)

    def professional_variant(self, biosample_id, only_variant_site=True,
                             regions=None, bed_file=None):
        """专业级变异数据接口

        regions 与 bed_file 须且提供其中之一

        Args:
            biosample_id(str): 生物样品编号;
            only_variant_site(bool): 是否仅输出变异位置,默认为True;
            regions(list): 需要抽取区域的坐标数据,数组长度不得超过5000;
            bed_file(str): 需要抽取区域的 bed 文件路径,文件须为 zip 压缩文件
                           且内容不得超过 100w 行
        """
        timeout = self.timeout
        verbose = self.verbose
        max_retries = self.max_retries
        if regions is not None and bed_file is not None:
            raise BGEError(
                'Regions and bed_file needs to provided one of them.')
        if regions is None and bed_file is None:
            raise BGEError(
                'Regions and bed_file cannot be provided at the same time.')
        if biosample_id:
            biosample_id = biosample_id.upper()
        data = {}
        data['biosample_id'] = biosample_id
        data['only_variant_site'] = only_variant_site
        if regions is not None:
            if not isinstance(regions, list):
                raise BGEError(
                    'Regions parameter type is array')
            data['regions'] = json.dumps(regions)
            files = None
        else:
            files = {
                'bed_file': open(str(bed_file), 'rb')
            }
        request = HTTPRequest(
            self.endpoint, max_retries=max_retries, verbose=verbose)
        request.set_authorization(self.token_type, self.access_token)
        result = request.post(
            '/professional/variant', data=data, files=files, timeout=timeout)
        return models.Model(result)

    def get_samples(self, biosample_ids=None, biosample_sites=None,
                    omics=None, project_ids=None, organisms=None,
                    data_availability=None, statuses=None,
                    require_files=None, next_page=None, limit=50,
                    **kwargs):
        """获取样品列表

        授权码模式: 可通过本接口获取授权用户的样品;
        客户端模式: 可通过本接口获取客户端应用通过注册接口注册(或预先生成)的样品;

        Args:
            biosample_ids (str, 非必填): 生物样品 id,逗号分割多个;
            biosample_sites (str, 非必填): 采样部位,取值范围: 1-15;
            omics (str, 非必填): 所属组学,取值范围: 1-2;
            project_ids (str, 非必填): 所属项目,逗号分割多个;
            organisms (str, 非必填): 样品生物体,取值范围: 1-3;
            data_availability (boolean, 非必填): 数据可用性;
            statuses (str, 非必填): 数据状态,详情见 BGE 开放平台文档;
            require_files(boolean, 非必填）: 要求返回关联文件列表
            next_page (int, 非必填): 要获取的页码,默认值为 None;
            limit (int, 非必填): 每页返回数量,默认值为 50;

        Returns:
            list: 样品列表;
        """
        params = {}
        params.update(kwargs)
        page = 1
        if next_page is not None:
            page = next_page
        if biosample_ids:
            biosample_ids = biosample_ids.upper()
        params.update({
            'biosample_ids': biosample_ids,
            'biosample_sites': biosample_sites,
            'omics': omics,
            'project_ids': project_ids,
            'organisms': organisms,
            'data_availability': data_availability,
            'statuses': statuses,
            'page': page,
            'limit': limit,
            'require_files': require_files
        })
        timeout = self.timeout
        verbose = self.verbose
        max_retries = self.max_retries
        request = HTTPRequest(
            self.endpoint, max_retries=max_retries, verbose=verbose)
        request.set_authorization(self.token_type, self.access_token)
        result = request.get('/samples', params=params, timeout=timeout)
        return models.Model(result)

    def get_sample(self, biosample_id, require_files=None):
        """获取样品

        授权码模式: 可通过本接口获取授权用户的样品;
        客户端模式: 可通过本接口获取客户端应用通过注册接口注册(或预先生成)的样品;

        Args:
            biosample_id (str): 生物样品编号;

        Returns:
            Model: 样品数据;
        """
        if biosample_id:
            biosample_id = biosample_id.upper()
        url = '/samples/{}'.format(biosample_id)
        params = {}
        params['require_files'] = require_files
        timeout = self.timeout
        verbose = self.verbose
        max_retries = self.max_retries
        request = HTTPRequest(
            self.endpoint, max_retries=max_retries, verbose=verbose)
        request.set_authorization(self.token_type, self.access_token)
        result = request.get(url, params=params, timeout=timeout)
        return models.Model(result)

    def externals(self, project_id, biosample_site, external_ids):
        """获取样品外部编号对应的 BGE 平台套件编号

        Args:
            external_sample_ids (str): 外部生物样品id(逗号分割多个);
            biosample_site (int): 采样部位;
            project_id (str): 项目编号;

        Returns:
            list: 编号对应数据;
        """
        url = '/samples/external_ids'
        params = {}
        params['external_ids'] = external_ids
        params['biosample_site'] = biosample_site
        params['project_id'] = project_id
        timeout = self.timeout
        verbose = self.verbose
        max_retries = self.max_retries
        request = HTTPRequest(
            self.endpoint, max_retries=max_retries, verbose=verbose)
        request.set_authorization(self.token_type, self.access_token)
        result = request.get(url, params=params, timeout=timeout)
        return models.ListModel(result)

    def register_sample(self, external_sample_id, biosample_site,
                        project_id, **kwargs):
        """注册样品

        Args:
            external_sample_id (str): 外部生物样品id;
            biosample_site (int): 采样部位;
            project_id (str): 项目编号;
            **kwargs: 其他非必填数据,例: library_id="HWJBAYTGAA170328-18";

        Returns:
            Model: 样品数据,包含生物样品编号;
        """
        data = {}
        data.update(kwargs)
        data.update({
            'external_sample_id': external_sample_id,
            'biosample_site': int(biosample_site),
            'project_id': project_id
        })
        timeout = self.timeout
        verbose = self.verbose
        max_retries = self.max_retries
        request = HTTPRequest(
            self.endpoint, max_retries=max_retries, verbose=verbose)
        request.set_authorization(self.token_type, self.access_token)
        result = request.post(
            '/samples/register', data=data, timeout=timeout)
        return models.Model(result)

    def improve_sample(self, biosample_id, **kwargs):
        """补充样品中未被赋值的信息

        已赋值数据无法变更,否则接口报错;

        Args:
            biosample_id (str): 生物样品编号;
            **kwargs: 需要赋值的字段和值;
        """
        if not kwargs:
            # 无更新
            return
        if biosample_id:
            biosample_id = biosample_id.upper()
        data = {}
        data.update(kwargs)
        data['biosample_id'] = biosample_id
        timeout = self.timeout
        verbose = self.verbose
        max_retries = self.max_retries
        request = HTTPRequest(
            self.endpoint, max_retries=max_retries, verbose=verbose)
        request.set_authorization(self.token_type, self.access_token)
        request.post(
            '/samples/improve', data=data, timeout=timeout)

    def get_taxon_abundance(self, biosample_id, taxon_ids=None,
                            next_page=None, limit=50, **params):
        """获取类群丰度

        Args:
            biosample_id (str): 生物样品编号;
            taxon_ids ([str], 非必填): BGE 物种编号,多个以逗号分割;
            next_page ([int], 非必填): 当前页码,默认值为 1,即首页;
            limit (int, 非必填): [description]. 默认值为 50;

        Returns:
            Model: 类群丰度数据详情;
        """
        if biosample_id:
            biosample_id = biosample_id.upper()
        params.update({
            'biosample_id': biosample_id,
            'taxon_id': taxon_ids,
            'limit': limit
        })
        page = 1
        if next_page is not None:
            page = next_page
        params['page'] = page
        timeout = self.timeout
        verbose = self.verbose
        max_retries = self.max_retries
        request = HTTPRequest(
            self.endpoint, max_retries=max_retries, verbose=verbose)
        request.set_authorization(self.token_type, self.access_token)
        result, pagination = request.get(
            '/microbiome/taxon_abundance', params=params, timeout=timeout)
        # TODO: upgrade in the future
        # 暂时特殊处理此接口,统一丰度数据的返回方式
        ret = dict()
        ret['count'] = count = pagination['count']
        next_page = pagination['page'] + 1
        if count == 0:
            next_page = None
        ret['next_page'] = next_page
        ret['result'] = result
        return models.Model(ret)

    def get_func_abundance(self, biosample_id, catalog, ids=None, limit=50,
                           next_page=None, **params):
        """获取功能丰度

        Args:
            biosample_id (str): 生物样品编号;
            catalog (str): 目录标签,可选值为: go、ko、eggnog、pfam、kegg-pwy、
                           kegg-mdl、level4ec、metacyc-rxn、metacyc-pwy;
            ids (str, 非必填): BGE物种功能编号,多个值以逗号隔开;
            limit (int, 非必填): 一页返回数量,默认值为 50;
            next_page (str, 非必填): 下一页,用于获取下一页数据;

        Returns:
            Model: 功能丰度数据详情;
        """
        if biosample_id:
            biosample_id = biosample_id.upper()
        params.update({
            'biosample_id': biosample_id,
            'catalog': catalog,
            'ids': ids,
            'next_page': next_page,
            'limit': limit
        })
        timeout = self.timeout
        verbose = self.verbose
        max_retries = self.max_retries
        request = HTTPRequest(
            self.endpoint, max_retries=max_retries, verbose=verbose)
        request.set_authorization(self.token_type, self.access_token)
        result = request.get(
            '/microbiome/func_abundance', params=params, timeout=timeout)
        return models.Model(result)

    def get_gene_abundance(self, biosample_id, catalog, data_type, ids=None,
                           limit=None, next_page=None, **params):
        """获取基因丰度

        Args:
            biosample_id (str): 生物样品编号;
            catalog (str): 分类标签,可选值: IGC_9.9M、UniRef90_HUMAnN2_0.11;
            data_type (str): 返回数据类型,可选值: list、file;
            ids (str, 非必填): BGE 物种 IGC 基因编号,多个值以逗号分割,
                                    如: igc_50,igc_51;
            limit (int, 非必填): 一页最大返回数量,默认 50,最大值为 1000;
            next_page (str, 非必填): 接口返回的下一页参数;

        Returns:
            Model: 基因丰度数据详情;
        """
        if biosample_id:
            biosample_id = biosample_id.upper()
        params.update({
            'biosample_id': biosample_id,
            'catalog': catalog,
            'data_type': data_type,
            'ids': ids,
            'next_page': next_page,
            'limit': limit
        })
        timeout = self.timeout
        verbose = self.verbose
        max_retries = self.max_retries
        request = HTTPRequest(
            self.endpoint, max_retries=max_retries, verbose=verbose)
        request.set_authorization(self.token_type, self.access_token)
        result = request.get(
            '/microbiome/gene_abundance', params=params, timeout=timeout)
        return models.Model(result)

    def get_upload_token(self, region_id=None, internal=False, **kwargs):
        """获取文件上传授权

        获取的授权仅包括当前目录(不含子目录)下的文件读、写权限;

        Returns:
            Model: 授权数据;
        """
        timeout = self.timeout
        verbose = self.verbose
        max_retries = self.max_retries
        data = {}
        data.update(kwargs)
        data.update({
            'region_id': region_id,
            'internal': internal,
        })
        request = HTTPRequest(
            self.endpoint, max_retries=max_retries, verbose=verbose)
        request.set_authorization(self.token_type, self.access_token)
        result = request.post('/sts/token', data=data, timeout=timeout)
        return models.Model(result)

    def upload(self, filename, file_or_string, part_size=None,
               multipart_threshold=None, multipart_num_threads=None,
               cmk_id=None, region_id=None, internal=False):
        """上传文件

        Args:
            filename (str): 要上传到服务器的文件名;
            file_or_string (file-like-object or str): 文件内容或类文件对象;
            part_size(num): 单个分片大小, 默认 50MB;
            multipart_threshold(num): 上传数据大于或等于该值时分片上传, 默认 100M;
            multipart_num_threads: 分片上传缺省线程数, 默认 4;
            cmk_id (str): 阿里云 KMS 服务用户主密钥 ID,加密上传时提供 CMK ID 即可;
                          提供 cmk_id 后不支持分片上传;
            region_id(str): 阿里云 OSS 区域编号，默认 oss-cn-shenzhen；
            internal(bool): 是否使用内部 VPN 域名，默认 False；

        Returns:
            object_name: 文件的 OSS 对象名;
        """
        token = self.get_upload_token(
            region_id=region_id,
            internal=internal
        )
        return self._upload(
            token,
            filename,
            file_or_string,
            part_size=part_size,
            multipart_threshold=multipart_threshold,
            multipart_num_threads=multipart_num_threads,
            cmk_id=cmk_id,
        )

    def batch_upload(self, files, part_size=None,
                     multipart_threshold=None, multipart_num_threads=None,
                     cmk_id=None, region_id=None, internal=False):
        """批量上传文件

        Args:
            files (FileItem object list): 要上传到服务器的文件列表;
            part_size(num): 单个分片大小, 默认 50MB;
            multipart_threshold(num): 上传数据大于或等于该值时分片上传, 默认 100M;
            multipart_num_threads: 分片上传缺省线程数, 默认 4;
            cmk_id (str): 阿里云 KMS 服务用户主密钥 ID,加密上传时提供 CMK ID 即可;
            region_id(str): 阿里云 OSS 区域编号，默认 oss-cn-shenzhen；
            internal(bool): 是否使用内部 VPN 域名，默认 False；

        Returns:
            object_name: 文件的 OSS 对象名;
        """
        if not files:
            raise BGEError('files is required')
        object_names = []
        if isinstance(files, (list, tuple)):
            files = [files]
        token = self.get_upload_token(
            region_id=region_id,
            internal=internal
        )
        for file_obj in files:
            if not isinstance(file_obj, FileItem):
                continue
            filename = file_obj.filename
            file_or_string = file_obj.file_or_string
            sys.stdout.write('开始上传: {}\n'.format(filename))
            object_name = self._upload(
                token,
                filename,
                file_or_string,
                part_size=part_size,
                multipart_threshold=multipart_threshold,
                multipart_num_threads=multipart_num_threads,
                cmk_id=cmk_id
            )
            sys.stdout.write('\n\n')
            sys.stdout.flush()
            object_names.append(object_name)
        return models.ListModel(object_names)

    def upload_dir(self, dirpath, part_size=None,
                   multipart_threshold=None, multipart_num_threads=None,
                   cmk_id=None, region_id=None, internal=False):
        """上传目录下的文件(不递归上传子文件夹中文件)

        仅上传目录中的文件,软链接、符号链接、文件夹均不会上传至平台。

        Args:
            dirpath (str): 要上传到服务器的文件夹;
            part_size(num): 单个分片大小, 默认 50MB;
            multipart_threshold(num): 上传数据大于或等于该值时分片上传, 默认 100M;
            multipart_num_threads: 分片上传缺省线程数, 默认 4;
            cmk_id (str): 阿里云 KMS 服务用户主密钥 ID,加密上传时提供 CMK ID 即可;

        Returns:
            object_names: 上传的文件 OSS 对象名列表;
        """
        token = self.get_upload_token(
            region_id=region_id,
            internal=internal
        )
        object_names = []
        for filename in os.listdir(dirpath):
            filepath = join(dirpath, filename)
            if isdir(filepath):
                continue
            sys.stdout.write('开始上传: {}\n'.format(filepath))
            object_name = self._upload(
                token,
                filename,
                filepath,
                part_size=part_size,
                multipart_threshold=multipart_threshold,
                multipart_num_threads=multipart_num_threads,
                cmk_id=cmk_id
            )
            sys.stdout.write('\n\n')
            sys.stdout.flush()
            object_names.append(object_name)
        return models.ListModel(object_names)

    def _upload(self, token, filename, file_or_string, part_size=None,
                multipart_threshold=None, multipart_num_threads=None,
                cmk_id=None):
        if part_size is None:
            part_size = constants.PART_SIZE
        if multipart_threshold is None:
            multipart_threshold = constants.MULTIPART_THRESHOLD
        if multipart_num_threads is None:
            multipart_num_threads = constants.MULTIPART_NUM_THREADS
        token_meta = self.introspect()
        if token_meta['active'] == False:
            raise BGEError('access_token has expired')
        client_id = token_meta['client_id']
        credentials = token.credentials
        destination = token.destination
        bucket_name = token.bucket
        endpoint = token.endpoint
        access_key_id = credentials['access_key_id']
        access_key_secret = credentials['access_key_secret']
        security_token = credentials['security_token']
        auth = oss2.StsAuth(
            access_key_id, access_key_secret, security_token)
        if cmk_id is not None:
            region_id = token.region_id
            kms_provider = oss2.AliKMSProvider(
                access_key_id, access_key_secret, region_id, cmk_id)
            # NOTE 官方 oss2 处理 STS 加密上传存在 bug,等待其修复,此处做代码动态修改
            sts_token_credential = StsTokenCredential(
                access_key_id, access_key_secret, security_token)
            kms_provider.kms_client = AcsClient(
                region_id=region_id, credential=sts_token_credential)
            bucket = oss2.CryptoBucket(
                auth, endpoint, bucket_name, crypto_provider=kms_provider)
        else:
            bucket = oss2.Bucket(auth, endpoint, bucket_name)
        object_name = '%s/%s' % (destination, filename)
        bge_open_client_id_header = 'x-oss-meta-bge-open-client-id'
        custom_headers = { bge_open_client_id_header: client_id }
        if isinstance(file_or_string, str) and isfile(file_or_string):
            # 分片上传仅支持文件路径，不支持文件对象
            oss2.resumable_upload(
                bucket,
                object_name,
                file_or_string,
                progress_callback=progress_callback,
                headers=custom_headers,
                part_size=part_size,
                num_threads=multipart_num_threads,
                multipart_threshold=multipart_threshold
            )
        else:
            bucket.put_object(
                object_name,
                file_or_string,
                headers=custom_headers,
                progress_callback=progress_callback
            )
        sys.stdout.write('\n')
        sys.stdout.flush()
        return object_name

    def get_download_url(self, object_name, region=None,
                         expiration_time=600, **kwargs):
        """获取阿里云OSS(对象存储)中的文件下载地址

        Args:
            object_name (str): OSS对象;
            region (str, 非必填): 区域(domestic、international),默认值为
                                 domestic;
            expiration_time (int, 非必填): 下载地址过期时间,默认值 600s;

        Returns:
            Model: 文件下载地址;
        """
        data = {}
        data.update(kwargs)
        data.update({
            'object_name': object_name,
            'region': region,
            'expiration_time': expiration_time
        })
        timeout = self.timeout
        verbose = self.verbose
        max_retries = self.max_retries
        request = HTTPRequest(
            self.endpoint, max_retries=max_retries, verbose=verbose)
        request.set_authorization(self.token_type, self.access_token)
        result = request.post('/oss/sign_url', data=data, timeout=timeout)
        return models.Model(result)

    def download(self, object_name, fp, region=None,
                 expiration_time=600, chunk_size=8192, **kwargs):
        """下载存储在阿里云OSS(对象存储)中的文件

        Args:
            object_name (str): OSS对象;
            fp(file like object): 可写的类文件对象;
            region (str, 非必填): 区域(domestic、international),默认值为
                                 domestic;
            chunk_size(int): 下载块大小
            expiration_time (int, 非必填): 下载地址过期时间,默认值 600s;
        Returns:
            None
        """
        inst = self.get_download_url(
            object_name, region=None, expiration_time=expiration_time,
            **kwargs)
        size = 0
        prog_size = 61  # 单行输出的进度条固定为 80 个字符长度
        url = inst.url
        chunk_size = int(chunk_size)
        sys.stdout.write('\nStart downloading: %s' % object_name)
        sys.stdout.write('\n\n')
        timeout = self.timeout
        try:
            with requests.get(url, stream=True, timeout=timeout) as r:
                total = r.headers.get('content-length')
                if total is not None:
                    total = int(total)
                    for chunk in r.iter_content(chunk_size):
                        size += len(chunk)
                        eq_size = int(size * prog_size / total)
                        equal_s = '=' * eq_size
                        blank_s = ' ' * (prog_size - eq_size)
                        progress = '>'.join((equal_s, blank_s))
                        percent = '%.2f%%' % float(size / total * 100)
                        sys.stdout.write(
                            '\r\t%s [%s]' % (percent.rjust(7), progress)
                        )
                        sys.stdout.flush()
                        fp.write(chunk)
                else:
                    for chunk in r.iter_content(chunk_size):
                        size += len(chunk)
                        sys.stdout.write(
                            '\r\t已下载文件：%s' % human_byte(size).ljust(7)
                        )
                        sys.stdout.flush()
                        fp.write(chunk)
                sys.stdout.write('\n')
                flush_func = getattr(fp, 'flush', None)
                if flush_func:
                    flush_func()
        except requests.exceptions.HTTPError:
            raise BGEError('download request error')
        except Exception as e:
            raise BGEError(e)

    def ferry_to_oss(self, account, password, project_no, biosample_cnt,
                     included_filename_exts=None, sample_names=None,
                     action=None, **kwargs):
        """下载科服文件转存至 BGE OSS

        Args:
            account (str): 华大科技账号；
            password(str): 华大科技密码；
            project_no (str): 华大科技项目编号；
            biosample_cnt(int): 样本数，必须大于或等于 0；接口将通过计算下载文件中样
                本名（参考参数 sample_names 解释）去重后与接口提供参数对比，数量无误
                才会下载文件；
            included_filename_exts (str, 非必填): 下载的文件后缀名可选范围：.txt、
                .xls、.pdf、.tar.gz、.tar.gz.md5、.fq.gz，默认包含全部可选后缀，
                多个后缀用英文逗号分割，如: .txt,.pdf；
            sample_names (str, 非必填)：样品名，将从过滤后将要下载的文件中，使用样本
                名过滤所有 .fq.gz 的文件；样品名为要下载文件中文件名为 *_1.fq.gz 或
                者 *_2.fq.gz 的文件, 如 E-V20000006992A_1.fq.gz 文件的样品名即
                为 E-V20000006992A，多个样本名用逗号分割；
            action (str, 非必填)：动作名，可选值：restart，如果接口调用包含
                参数 action=restart，接口将使用接口调用的参数重新启动一个新的任务（
                如果相同参数的任务已经在运行，将无法重新启动任务，且接口将报错）；
        Returns:
            Model: 科服文件下载转存结果
        """
        data = {}
        data.update(kwargs)
        data.update({
            'account': account,
            'password': password,
            'project_no': project_no,
            'biosample_cnt': biosample_cnt,
            'included_filename_exts': included_filename_exts,
            'sample_names': sample_names,
            'action': action
        })
        timeout = self.timeout
        verbose = self.verbose
        max_retries = self.max_retries
        request = HTTPRequest(
            self.endpoint, max_retries=max_retries, verbose=verbose)
        request.set_authorization(self.token_type, self.access_token)
        result = request.post(
            '/ferry/download_to_oss', data=data, timeout=timeout)
        return models.Model(result)

    def aggregate_omics_data(self, data_element_id, time_dimension, start_time,
                             end_time=None, biosample_id=None,
                             interval=1, periods=100, **kwargs):
        """聚合组学数据(目前仅支持聚合数据流中符合平台设定 JSONPath 规则的数值型数据)

        Args:
            data_element_id (str, 必填): 数据元编号;
            time_dimension (str, 必填): 子聚合的时间维度,可选值: year, quarter,
                                        month, week, day, minute, second
            start_time (str, 必填): 数据流生成时间的起始时间;
            end_time (str, 非必填): 数据流生成时间的结束时间,为空时默认取当前时间;
            biosample_id (str, 非必填): 生物样品编号,客户端模式下为必填;
            interval (int, 非必填): 聚合时间维度间隔,默认:1
            periods (int, 非必填): 聚合时间维度返回数,默认:100,最大值: 100

        Returns:
            Model: 返回的聚合数据
        """
        if biosample_id:
            biosample_id = biosample_id.upper()
        params = {}
        params.update(kwargs)
        params.update({
            'biosample_id': biosample_id,
            'data_element_id': data_element_id,
            'time_dimension': time_dimension,
            'start_time': start_time,
            'end_time': end_time,
            'interval': interval,
            'periods': periods
        })
        timeout = self.timeout
        verbose = self.verbose
        max_retries = self.max_retries
        request = HTTPRequest(
            self.endpoint, max_retries=max_retries, verbose=verbose)
        request.set_authorization(self.token_type, self.access_token)
        result = request.get(
            '/omics_data/aggregate', params=params, timeout=timeout)
        return models.Model(result)

    def get_range_stream(self, data_element_id, biosample_id=None,
                         start_time=None, end_time=None,
                         sort_direction=None, limit=100, next_page=None,
                         **kwargs):
        """返回查询数据流

        Args:
            biosample_id (str, 非必填): 生物样品编号,客户端模式下为必填;
            start_time (str, 非必填): 数据流生成时间的起始时间
            end_time (str, 非必填): 数据流生成时间的结束时间
            sort_direction (str, 非必填): 排序方式,默认: desc
            limit (int, 非必填): 每页返回数量,默认:100
            next_page (str, 非必填): 下一页参数

        Returns:
            Model: 返回的数据流数据
        """
        if biosample_id:
            biosample_id = biosample_id.upper()
        params = {}
        params.update(kwargs)
        params.update({
            'biosample_id': biosample_id,
            'data_element_id': data_element_id,
            'start_time': start_time,
            'end_time': end_time,
            'sort_direction': sort_direction,
            'limit': limit,
            'next_page': next_page
        })
        timeout = self.timeout
        verbose = self.verbose
        max_retries = self.max_retries
        request = HTTPRequest(
            self.endpoint, max_retries=max_retries, verbose=verbose)
        request.set_authorization(self.token_type, self.access_token)
        result = request.get(
            '/stream/range', params=params, timeout=timeout)
        return models.Model(result)

    def write_phenotype(self, biosample_id, data_element_id,
                        stream_generate_time, stream_data,
                        duplicate_enabled=None, **kwargs):
        """根据生物套件编号写入表型数据

        Args:
            biosample_id (str): 生物样品编号;
            data_element_id (str): 数据元编号;
            stream_generate_time (datetime): 数据流生成时间，
                                             如：2021-03-02T10:00:00Z;
            stream_data(dict): 数据流数据；
            duplicate_enabled(boolean, 非必填): 允许重复写入；

        Returns:
            Model: 返回的表型数据流编号数据;
        """
        biosample_id = biosample_id.upper()
        stream_data = json.dumps(stream_data)
        data = dict()
        data.update(kwargs)
        data.update({
            'biosample_id': biosample_id,
            'data_element_id': data_element_id,
            'stream_generate_time': stream_generate_time,
            'stream_data': stream_data,
            'duplicate_enabled': duplicate_enabled,
        })
        timeout = self.timeout
        verbose = self.verbose
        max_retries = self.max_retries
        request = HTTPRequest(
            self.endpoint, max_retries=max_retries, verbose=verbose)
        request.set_authorization(self.token_type, self.access_token)
        result = request.post(
            '/datamall/phenotype/write', data=data, timeout=timeout)
        return models.Model(result)

    def get_data_items(self, namespace, biosample_id,
                       collection_id=None, data_element_ids=None,
                       next_page=None, **kwargs):
        """根据数据元编号或数据集编号获取数据项

        Args:
            namespace(str): 命名空间
            biosample_id (str): 生物样品编号;
            collection_id(str,非必填): 数据集编号,与 data_element_ids 互斥;
            data_element_ids (str,非必填): 多个数据元编号,逗号分割(必填);
                                           最多一次提供100个;
            next_page (int,非必填): 下一页;

        Returns:
            Model: 返回的数据项数据;
        """
        if biosample_id:
            biosample_id = biosample_id.upper()
        params = {}
        params.update(kwargs)
        params.update({
            'biosample_id': biosample_id,
            'data_element_ids': data_element_ids,
            'collection_id': collection_id,
            'namespace': namespace,
            'next_page': next_page
        })
        timeout = self.timeout
        verbose = self.verbose
        max_retries = self.max_retries
        request = HTTPRequest(
            self.endpoint, max_retries=max_retries, verbose=verbose)
        request.set_authorization(self.token_type, self.access_token)
        result = request.get(
            '/data_item/batch_retrieve', params=params, timeout=timeout)
        return models.Model(result)

    def invoke_model(self, model_id, headers=None, **kwargs):
        """模型调用

        Args:
            model_id (str): 模型编号;
            **kwargs: 模型相关参数,由模型定义的参数决定;

        Returns:
            Model: 任务id,时间和状态;
        """
        params = {}
        params.update(kwargs)
        timeout = self.timeout
        verbose = self.verbose
        max_retries = self.max_retries
        request = HTTPRequest(
            self.endpoint, max_retries=max_retries, verbose=verbose)
        request.set_authorization(self.token_type, self.access_token)
        model_url = '/model/{}'.format(model_id)
        result = request.get(
            model_url,
            params=params,
            headers=headers,
            timeout=timeout
        )
        return models.Model(result)

    def invoke_draft_model(self, model_id, headers=None, **kwargs):
        """调用灰度部署版本模型

        Args:
            model_id (str): 模型编号;
            **kwargs: 模型相关参数,由模型定义的参数决定;

        Returns:
            Model: 任务id,时间和状态;
        """
        params = {}
        params.update(kwargs)
        timeout = self.timeout
        verbose = self.verbose
        max_retries = self.max_retries
        request = HTTPRequest(
            self.endpoint, max_retries=max_retries, verbose=verbose)
        request.set_authorization(self.token_type, self.access_token)
        model_url = '/model/{}/draft'.format(model_id)
        result = request.get(
            model_url,
            params=params,
            headers=headers,
            timeout=timeout
        )
        return models.Model(result)

    def deploy_model(self, model_id, object_name=None, runtime=None,
                     memory_size=None, cpu=None, disk_size=None,
                     timeout=None, **kwargs):
        """部署模型

        Args:
            model_id (str): 模型编号。
            object_name (str): 模型源代码文件阿里云 OSS 对象路径。
            runtime (str, 非必填): 运行环境版本。默认值: python3。
            memory_size (int, 非必填): 内存占用量,单位: MB。默认: 128MB。
            cpu(float, 非必填): vCPU 核心数。默认：0.05。
            disk_size(int, 非必填): 函数计算磁盘规格，单位：MB。默认：512。
            timeout (int, 非必填): 模型运行超时时间，单位: 秒。默认: 900。

        Returns:
            Model: 任务id,时间和状态;
        """
        data = {}
        data.update(kwargs)
        data.update({
            'model_id': model_id,
            'runtime': runtime,
            'memory_size': memory_size,
            'cpu': cpu,
            'disk_size': disk_size,
            'timeout': timeout,
            'object_name': object_name
        })
        timeout = self.timeout
        verbose = self.verbose
        max_retries = self.max_retries
        request = HTTPRequest(
            self.endpoint, max_retries=max_retries, verbose=verbose)
        request.set_authorization(self.token_type, self.access_token)
        result = request.post(
            '/model/deploy', data=data, timeout=timeout)
        return models.Model(result)

    def publish_model(self, model_id, message, **kwargs):
        """发布模型稳定版

        Args:
            model_id (str): 模型编号。
            message (str): 本次发布模型的描述信息。

        Returns:
            [int]: 稳定版模型发布成功后返回的版本号
        """

        data = {}
        data.update(kwargs)
        data.update({
            'model_id': model_id,
            'message': message
        })
        timeout = self.timeout
        verbose = self.verbose
        max_retries = self.max_retries
        request = HTTPRequest(
            self.endpoint, max_retries=max_retries, verbose=verbose)
        request.set_authorization(self.token_type, self.access_token)
        result = request.post(
            '/model/publish', data=data, timeout=timeout)
        return models.Model(result)

    def rollback_model(self, model_id, version, **kwargs):
        """回滚模型

        Args:
            model_id (str): 模型编号。
            version (int): 模型版本号。

        Returns:
            [str]: 模型回滚成功后返回的新的版本号
        """
        data = {}
        data.update(kwargs)
        data.update({
            'model_id': model_id,
            'version': version
        })
        timeout = self.timeout
        verbose = self.verbose
        max_retries = self.max_retries
        request = HTTPRequest(
            self.endpoint, max_retries=max_retries, verbose=verbose)
        request.set_authorization(self.token_type, self.access_token)
        result = request.post(
            '/model/rollback', data=data, timeout=timeout)
        return models.Model(result)

    def model_versions(self, model_id, limit=10, next_page=None, **kwargs):
        """模型历史版本列表

        Args:
            model_id (str): 模型编号。
            limit (int): 每页返回数量,默认值为 10。
            next_page (int): 下一页;

        Returns:
            [list]: 模型历史版本列表
        """
        params = {}
        params.update(kwargs)
        params['limit'] = limit
        params['next_page'] = next_page
        timeout = self.timeout
        verbose = self.verbose
        max_retries = self.max_retries
        request = HTTPRequest(
            self.endpoint, max_retries=max_retries, verbose=verbose)
        request.set_authorization(self.token_type, self.access_token)
        model_url = '/model/{}/versions'.format(model_id)
        result = request.get(model_url, params=params, timeout=timeout)
        return models.Model(result)

    def upload_model_expfs(self, model_id, expfs, **kwargs):
        """上传模型扩展文件集

        Args:
            model_id (str): 模型编号。
            expfs (path): 模型扩展文件集。

        Returns:
            Model: 任务id、时间、状态和返回值;
        """
        if isinstance(expfs, text_type):
            filename = split(expfs)[1]
        else:
            filename = expfs.name
        def upload_callback(monitor):
            total_bytes = monitor.len
            bytes_consumed = monitor.bytes_read
            sys.stdout.write(
                '\r文件大小: {}, 上传进度: {}%, 已上传 {}'.format(
                    human_byte(total_bytes, 2),
                    '%.2f' % ((bytes_consumed / total_bytes) * 100),
                    human_byte(bytes_consumed, 2)
                )
            )
            sys.stdout.flush()
        e = encoder.MultipartEncoder(
            fields={
                'model_id': model_id,
                'expfs': (filename, open(expfs, 'rb'), 'application/zip')
            }
        )
        m = encoder.MultipartEncoderMonitor(e, upload_callback)
        timeout = self.timeout
        verbose = self.verbose
        max_retries = self.max_retries
        request = HTTPRequest(
            self.endpoint, max_retries=max_retries, verbose=verbose)
        request.set_authorization(self.token_type, self.access_token)
        model_url = '/model/expfs/upload'
        result = request.post(model_url, data=m, timeout=timeout, headers={
            'Content-Type': m.content_type
        })
        sys.stdout.write('')
        return models.Model(result)

    def model_license(self, model_id, expires=60, params=None):
        """模型运行许可

        Args:
            model_id (str): 模型编号。
            **kwargs: 模型相关参数,由模型定义的参数决定;

        Returns:
            Model: 授权模型运行的对称加密相关参数;
        """
        data = {}
        data['model_id'] = model_id
        data['expires'] = expires
        if params:
            params = json.dumps(params)
        data['params'] = params
        timeout = self.timeout
        verbose = self.verbose
        max_retries = self.max_retries
        request = HTTPRequest(
            self.endpoint, max_retries=max_retries, verbose=verbose)
        request.set_authorization(self.token_type, self.access_token)
        model_url = '/model/license'
        result = request.post(model_url, data=data, timeout=timeout)
        return models.Model(result)

    def task(self, task_id):
        """获取任务结果

        Args:
            task_id (str): 任务编号。

        Returns:
            Model: 任务id、时间、状态和返回值;
        """
        timeout = self.timeout
        verbose = self.verbose
        max_retries = self.max_retries
        request = HTTPRequest(
            self.endpoint, max_retries=max_retries, verbose=verbose)
        request.set_authorization(self.token_type, self.access_token)
        model_url = '/task/{}'.format(task_id)
        result = request.get(model_url, timeout=timeout)
        return models.Model(result)

    def upload_model_doc(self, doc_tab, model_id, doc_content):
        """上传模型文档

        Args:
            doc_tab (str): 文档所在的 tab。
            model_id (str): 模型编号。
            doc_content (list): 文档内容
        Returns:
            Model_id: 模型编号;
            version: 文档版本号。
        """
        data = {}
        data['doc_tab'] = doc_tab
        data['model_id'] = model_id
        data['doc_content'] = doc_content
        doc = json.dumps(data)
        timeout = self.timeout
        verbose = self.verbose
        max_retries = self.max_retries
        request = HTTPRequest(
            self.endpoint, max_retries=max_retries, verbose=verbose)
        request.set_authorization(self.token_type, self.access_token)
        result = request.post(
            '/model/doc_upload', data=doc, timeout=timeout)
        return models.Model(result)

    def send_sms(self, template, mobiles, **kwargs):
        """发送短信

        Args:
            template (str): 短信模板;
            mobiles (str): 手机号，多个手机号用逗号分割;

        template：pay_code（积分消费通知短信）
            pay_code(str): 消费验证码；

        template: research_download_notice（科研数据下载提示短信）
            org_name(str): 机构名称；
            project_name(str): 科研调查标题名称；
            applied_date(str): 申请数据日期；
            expiry_date(str): 数据有效期日期；

        template: microarray_delivery（芯片版发报告提示短信）
            user_nick_name(str): 用户昵称；

        Returns:
            Model: 返回的表型数据流编号数据;
        """
        data = dict()
        data.update(kwargs)
        data.update({
            'template': template,
            'mobiles': mobiles,
        })
        timeout = self.timeout
        verbose = self.verbose
        max_retries = self.max_retries
        request = HTTPRequest(
            self.endpoint, max_retries=max_retries, verbose=verbose)
        request.set_authorization(self.token_type, self.access_token)
        request.post('/sms/send', data=data, timeout=timeout)

    def applet_url(self, code, path=None, query=None, **kwargs):
        """小程序链接

        Args:
            code (字符串): BGE 平台微信应用中控所对应的编号(平台后台配置，需管理员处理）;
            path (字符串，非必填): 通过 URL Link 进入的小程序页面路径，必须是已经发布的
                小程序存在的页面，不可携带 query 。path 为空时会跳转小程序主页;
            query (字符串，非必填): 通过 URL Link 进入小程序时的query，最大1024个字符，
                只支持数字，大小写英文以及部分特殊字符：!#$&’()*+,/:;=?@-._~%;

        Returns:
            Model: 返回的小程序链接数据;
        """
        data = dict()
        data.update(kwargs)
        data.update({
            'code': code,
            'path': path,
            'query': query,
        })
        timeout = self.timeout
        verbose = self.verbose
        max_retries = self.max_retries
        request = HTTPRequest(
            self.endpoint, max_retries=max_retries, verbose=verbose)
        request.set_authorization(self.token_type, self.access_token)
        result = request.post(
            '/service/wechat/applet/url', data=data, timeout=timeout)
        return models.Model(result)

    def verify_id_meta(self, idcard, realname, phone=None, **kwargs):
        """身份要素核验

        传入姓名和身份证号，通过权威数据源验证其真实性和一致性。
        传入手机号、姓名、身份证号，通过权威数据源验证其真实性和一致性，如果不一致，返回不一致
        的原因。

        Args:
            idcard (字符串): 身份证;
            realname (字符串): 真名;
            phone (字符串，非必填): 手机号;

        Returns:
            Model: 返回的身份要素核验结果;
        """
        data = dict()
        data.update(kwargs)
        data.update({
            'idcard': idcard,
            'realname': realname,
            'phone': phone,
        })
        timeout = self.timeout
        verbose = self.verbose
        max_retries = self.max_retries
        request = HTTPRequest(
            self.endpoint, max_retries=max_retries, verbose=verbose)
        request.set_authorization(self.token_type, self.access_token)
        result = request.post(
            '/service/verify/id_meta', data=data, timeout=timeout)
        return models.Model(result)
