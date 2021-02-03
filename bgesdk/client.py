#-*- coding: utf-8 -*-

"""
BGE 开放平台 SDK 客户端模块。

当前模块提供了两个主要的类 OAuth2 和 API，他们分别提供了对 BGE 开放平台的 OAuth2 相关
接口和其他接口的调用方法。

使用示例：

    >>> oauth2 = OAuth2('demo', 'demo')
    >>> token = oauth2.get_credentials_token()
    >>> api = oauth2.get_api(token.access_token)
    >>> api.invoke_model('demo_model_id')
    Model({...})
"""

from . import contants
from . import models
from .error import BGEError
from .http import HTTPRequest
from .utils import major_version

if major_version <= 2:
    from urlparse import urljoin
    from urllib import urlencode
else:
    from urllib.parse import urljoin, urlencode
from weakref import proxy


BASE_URL = contants.BASE_URL
DEFAULT_TIMEOUT = contants.HTTP_DEFAULT_TIMEOUT
GRANT_AUTHORIZATION_CODE = contants.GRANT_AUTHORIZATION_CODE
GRANT_TYPE_CREDENTIALS = contants.GRANT_TYPE_CREDENTIALS


class OAuth2(object):
    """OAuth2 授权客户端类。
    
    管理关于 OAuth2 相关接口的调用，包括获取授权页面地址、授权码交换访问令牌等；
    
    Args:
        client_id (字符串): 第三方客户端 client_id；
        client_secret (字符串): 第三方客户端 client_secret；
        base_url (字符串, 非必填): 开放平台域名地址，默认值为 BASE_URL；
        timeout (数字, 非必填): 接口请求默认超时间，默认值为 DEFAULT_TIMEOUT；
    """

    def __init__(self, client_id, client_secret, base_url=BASE_URL,
                 timeout=DEFAULT_TIMEOUT):
        self.client_id = client_id
        self.client_secret = client_secret
        self.timeout = timeout
        self.base_url = base_url

    def get_authorization_url(self, redirect_uri, state=None, scopes=None):
        """获取用户授权页链接地址。

        Args:
            redirect_uri (str): 回调地址；
            state (str, 非必填): 第三方自定义信息，返回授权码时原样返回，
                                默认值为 None；
            scopes (list, 非必填): 权限范围，支持多个。默认值为 None；

        Returns:
            str: 用户授权页面地址；
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
        return '?'.join((urljoin(self.base_url, '/oauth2/authorize'), qs))

    def exchange_authorization_code(self, code, redirect_uri):
        """用户授权码交换访问令牌

        Args:
            code (str): 用户授权后平台返回的授权码；
            redirect_uri (str): 回调地址；

        Returns:
            Model: 与授权用户关联的访问令牌，同时包含有刷新令牌、过期时间等信息；
        """
        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'grant_type': GRANT_AUTHORIZATION_CODE,
            'redirect_uri': redirect_uri,
            'code': code
        }
        timeout = self.timeout
        request = HTTPRequest(self.base_url)
        result = request.post(
            '/oauth2/access_token', data=data, timeout=timeout)
        return models.Model(result)

    def exchange_refresh_token(self, refresh_token):
        """刷新令牌 access_token

        Args:
            refresh_token (str): 授权码模式所获得的 refresh_token；

        Returns:
            Model: 新的令牌数据；
        """
        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token
        }
        timeout = self.timeout
        request = HTTPRequest(self.base_url)
        result = request.post(
            '/oauth2/access_token', data=data, timeout=timeout)
        return models.Model(result)

    def get_credentials_token(self):
        """客户端授权模式下获取访问令牌

        Returns:
            Model: 访问令牌，包含 access_token、过期时间等；
        """
        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'grant_type': GRANT_TYPE_CREDENTIALS
        }
        timeout = self.timeout
        request = HTTPRequest(self.base_url)
        result = request.post(
            '/oauth2/access_token', data=data, timeout=timeout)
        return models.Model(result)

    def get_api(self, access_token):
        """获取平台 API 调用客户端对象

        Args:
            access_token (str): 访问令牌；

        Returns:
            API: API 对象；
        """
        return API(self, access_token)


class API(object):
    """BGE 开放平台接口调用客户端

    Args:
        oauth2 (OAuth2): OAuth2 对象；
        access_token (str): 访问令牌；
    """

    def __init__(self, oauth2, access_token):
        self.oauth2 = oauth2
        self.access_token = access_token

    def get_user(self, **params):
        """获取用户信息

        Returns:
            Model: 用户数据；
        """
        timeout = self.oauth2.timeout
        request = HTTPRequest(self.oauth2.base_url)
        request.set_authorization(self.access_token)
        result = request.get('/user', params=params, timeout=timeout)
        return models.Model(result)

    def get_variants(self, biosample_id, rsids, **params):
        """根据rsid查询变异位点信息

        Args:
            biosample_id (str): 生物样品编号；
            rsids (str): 多个 rs 编号，逗号分割（必填）；如：rs1229984；
                         最多一次提供100个；

        Returns:
            list: 变异位点信息；
        """
        params.update({
            'rsids': rsids,
            'biosample_id': biosample_id
        })
        timeout = self.oauth2.timeout
        request = HTTPRequest(self.oauth2.base_url)
        request.set_authorization(self.access_token)
        result = request.get('/variants', params=params, timeout=timeout)
        data = []
        for item in result:
            data.append(models.Model(item))
        return data

    def get_samples(self, biosample_ids=None, biosample_sites=None,
                    omics=None, project_ids=None, organisms=None,
                    data_availability=None, statuses=None,
                    page=1, limit=50, **params):
        """获取样品列表

        授权码模式: 可通过本接口获取授权用户的样品；
        客户端模式: 可通过本接口获取客户端应用通过注册接口注册(或预先生成)的样品；

        Args:
            biosample_ids ([str], 非必填): 生物样品 id，逗号分割多个；
            biosample_sites ([str], 非必填): 采样部位，取值范围：1-15；
            omics ([str], 非必填): 所属组学，取值范围：1-2；
            project_ids ([str], 非必填): 所属项目，逗号分割多个；
            organisms ([str], 非必填): 样品生物体，取值范围：1-3；
            data_availability ([boolean], 非必填): 数据可用性；
            statuses ([str], 非必填): 数据状态，详情见 BGE 开放平台文档；
            page (int, 非必填): 要获取的页码，默认值为 1；
            limit (int, 非必填): 每页返回数量，默认值为 50；

        Returns:
            list: 样品列表；
        """
        params.update({
            'biosample_ids': biosample_ids,
            'biosample_sites': biosample_sites,
            'omics': omics,
            'project_ids': project_ids,
            'organisms': organisms,
            'data_availability': data_availability,
            'statuses': statuses,
            'page': page,
            'limit': limit
        })
        timeout = self.oauth2.timeout
        request = HTTPRequest(self.oauth2.base_url)
        request.set_authorization(self.access_token)
        result = request.get('/samples', params=params, timeout=timeout)
        result = models.Model(result)
        data = []
        for item in result['result']:
            data.append(models.Model(item))
        result['result'] = data
        return result

    def get_sample(self, biosample_id):
        """获取样品

        授权码模式: 可通过本接口获取授权用户的样品；
        客户端模式: 可通过本接口获取客户端应用通过注册接口注册(或预先生成)的样品；

        Args:
            biosample_id (str): 生物样品编号；

        Returns:
            Model: 样品数据；
        """
        url = '/samples/{}'.format(biosample_id)
        timeout = self.oauth2.timeout
        request = HTTPRequest(self.oauth2.base_url)
        request.set_authorization(self.access_token)
        result = request.get(url, timeout=timeout)
        return models.Model(result)

    def register_sample(self, external_sample_id, biosample_site,
                        project_id, **kwargs):
        """注册样品

        Args:
            external_sample_id (str): 外部生物样品id；
            biosample_site (int):  采样部位；
            project_id (str): 项目编号；
            **kwargs: 其他非必填数据，例：library_id="HWJBAYTGAA170328-18"；

        Returns:
            str: 生物样品编号；
        """
        data = {}
        data.update(kwargs)
        data.update({
            'external_sample_id': external_sample_id,
            'biosample_site': int(biosample_site),
            'project_id': project_id
        })
        timeout = self.oauth2.timeout
        request = HTTPRequest(self.oauth2.base_url)
        request.set_authorization(self.access_token)
        result = request.post(
            '/samples/register', data=data, timeout=timeout)
        return result['biosample_id']

    def improve_sample(self, biosample_id, **kwargs):
        """补充样品中未被赋值的信息

        已赋值数据无法变更，否则接口报错；

        Args:
            biosample_id (str): 生物样品编号；
            **kwargs: 需要赋值的字段和值；
        """
        if not kwargs:
            # 无更新
            return
        data = {}
        data.update(kwargs)
        data['biosample_id'] = biosample_id
        timeout = self.oauth2.timeout
        request = HTTPRequest(self.oauth2.base_url)
        request.set_authorization(self.access_token)
        request.post(
            '/samples/improve', data=data, timeout=timeout)

    def get_taxon_abundance(self, biosample_id, taxon_ids=None,
                            next_page=None, limit=50, **params):
        """获取类群丰度

        Args:
            biosample_id (str): 生物样品编号；
            taxon_ids ([str], 非必填): BGE 物种编号，多个以逗号分割；
            next_page ([int], 非必填): 当前页码，默认值为 1，即首页；
            limit (int, 非必填): [description]. 默认值为 50；

        Returns:
            Model: 类群丰度数据详情；
        """
        params.update({
            'biosample_id': biosample_id,
            'taxon_id': taxon_ids,
            'limit': limit
        })
        page = 1
        if next_page is not None:
            page -= 1
        params['page'] = page
        timeout = self.oauth2.timeout
        request = HTTPRequest(self.oauth2.base_url)
        request.set_authorization(self.access_token)
        result, pagination = request.get(
            '/microbiome/taxon_abundance', params=params, timeout=timeout)
        # TODO: upgrade in the future
        # 暂时特殊处理此接口，统一丰度数据的返回方式
        ret = {}
        ret['count'] = count = pagination['count']
        next_page = pagination['page'] + 1
        if count == 0:
            next_page = None
        ret['next_page'] = next_page
        ret['result'] = [models.Model(item) for item in result]
        return ret

    def get_func_abundance(self, biosample_id, catalog, ids=None, limit=50,
                           next_page=None, **params):
        """获取功能丰度

        Args:
            biosample_id (str): 生物样品编号；
            catalog (str): 目录标签，可选值为：go、ko、eggnog、pfam、kegg-pwy、
                           kegg-mdl、level4ec、metacyc-rxn、metacyc-pwy；
            ids (str, 非必填): BGE物种功能编号，多个值以逗号隔开；
            limit (int, 非必填): 一页返回数量，默认值为 50；
            next_page (str, 非必填): 下一页，用于获取下一页数据；

        Returns:
            Model: 功能丰度数据详情；
        """
        params.update({
            'biosample_id': biosample_id,
            'catalog': catalog,
            'ids': ids,
            'next_page': next_page,
            'limit': limit
        })
        timeout = self.oauth2.timeout
        request = HTTPRequest(self.oauth2.base_url)
        request.set_authorization(self.access_token)
        result = request.get(
            '/microbiome/func_abundance', params=params,
            timeout=timeout)
        result = models.Model(result)
        result['result'] = [models.Model(item) for item in result['result']]
        return result

    def get_gene_abundance(self, biosample_id, catalog, data_type, ids=None,
                           limit=None, next_page=None, **params):
        """获取基因丰度

        Args:
            biosample_id (str): 生物样品编号；
            catalog (str): 分类标签，可选值：IGC_9.9M、UniRef90_HUMAnN2_0.11；
            data_type (str): 返回数据类型，可选值：list、file；
            ids (str, 非必填): BGE 物种 IGC 基因编号，多个值以逗号分割，
                                    如：igc_50,igc_51；
            limit (int, 非必填): 一页最大返回数量，默认 50，最大值为 1000；
            next_page (str, 非必填): 接口返回的下一页参数；

        Returns:
            Model: 基因丰度数据详情；
        """
        params.update({
            'biosample_id': biosample_id,
            'catalog': catalog,
            'data_type': data_type,
            'ids': ids,
            'next_page': next_page,
            'limit': limit
        })
        timeout = self.oauth2.timeout
        request = HTTPRequest(self.oauth2.base_url)
        request.set_authorization(self.access_token)
        result = request.get(
            '/microbiome/gene_abundance', params=params, timeout=timeout)
        result = models.Model(result)
        result['result'] = [models.Model(item) for item in result['result']]
        return result

    def get_upload_token(self, **kwargs):
        """获取文件上传授权
        
        获取的授权仅包括当前目录（不含子目录）下的文件读、写权限；

        Returns:
            Model: 授权数据；
        """
        timeout = self.oauth2.timeout
        request = HTTPRequest(self.oauth2.base_url)
        request.set_authorization(self.access_token)
        result = request.post('/sts/token', data=kwargs, timeout=timeout)
        return models.Model(result)

    def get_download_url(self, object_name, region=None,
                         expiration_time=600, **kwargs):
        """获取阿里云OSS（对象存储）中的文件下载地址

        Args:
            object_name (str): OSS对象；
            region (str, 非必填): 区域（domestic、international），默认值为
                                 domestic；
            expiration_time (int, 非必填): 下载地址过期时间，默认值 600s；

        Returns:
            Model: 文件下载地址；
        """

        data = {}
        data.update(kwargs)
        data.update({
            'object_name': object_name,
            'region': region,
            'expiration_time': expiration_time
        })
        timeout = self.oauth2.timeout
        request = HTTPRequest(self.oauth2.base_url)
        request.set_authorization(self.access_token)
        result = request.post('/oss/sign_url', data=data, timeout=timeout)
        return models.Model(result)

    def invoke_model(self, model_id, **kwargs):
        """模型调用

        Args:
            model_id (str): 模型编号；
            **kwargs: 模型相关参数，由模型定义的参数决定；

        Returns:
            Model: 任务id，时间和状态；
        """
        params = {}
        params.update(kwargs)
        timeout = self.oauth2.timeout
        request = HTTPRequest(self.oauth2.base_url)
        request.set_authorization(self.access_token)
        model_url = '/model/{}'.format(model_id)
        result = request.get(model_url, params=params, timeout=timeout)
        return models.Model(result)
