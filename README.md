
<div align="center">

# BGE 开放平台 SDK - Python 版


<p>
    <!-- Place this tag where you want the button to render. -->
    <a class="github-button" href="https://github.com/teambge/bge-python-sdk/subscription" data-color-scheme="no-preference: light; light: light; dark: dark;" data-show-count="true" aria-label="Watch teambge/bge-python-sdk on GitHub">
        <img alt="GitHub forks" src="https://img.shields.io/github/watchers/teambge/bge-python-sdk?style=social">
    </a>
    <a class="github-button" href="https://github.com/teambge/bge-python-sdk" data-color-scheme="no-preference: light; light: light; dark: dark;" data-show-count="true" aria-label="Star teambge/bge-python-sdk on GitHub">
        <img alt="GitHub forks" src="https://img.shields.io/github/stars/teambge/bge-python-sdk?style=social">
    </a>
    <a class="github-button" href="https://github.com/teambge/bge-python-sdk/fork" data-color-scheme="no-preference: light; light: light; dark: dark;" data-show-count="true" aria-label="Fork teambge/bge-python-sdk on GitHub">
        <img alt="GitHub forks" src="https://img.shields.io/github/forks/teambge/bge-python-sdk?style=social">
    </a>
</p>

<p>
    <img src="https://img.shields.io/github/v/release/teambge/bge-python-sdk" data-origin="https://img.shields.io/github/v/release/teambge/bge-python-sdk" alt="GitHub release (latest by date)">
    <img src="https://img.shields.io/github/languages/top/teambge/bge-python-sdk" data-origin="https://img.shields.io/github/languages/top/teambge/bge-python-sdk" alt="GitHub top language">
    <img src="https://img.shields.io/github/languages/code-size/teambge/bge-python-sdk" data-origin="https://img.shields.io/github/languages/code-size/teambge/bge-python-sdk" alt="GitHub code size in bytes">
    <img src="https://img.shields.io/github/commit-activity/w/teambge/bge-python-sdk" data-origin="https://img.shields.io/github/commit-activity/w/teambge/bge-python-sdk" alt="GitHub commit activity">
    <img src="https://static.pepy.tech/personalized-badge/bge-python-sdk?period=total&units=international_system&left_color=grey&right_color=blue&left_text=Downloads" data-origin="https://static.pepy.tech/personalized-badge/bge-python-sdk?period=total&units=international_system&left_color=grey&right_color=blue&left_text=Downloads" alt="PyPI - Downloads">
</p>

<pre>
    ____  ____________   ______  __________  ______  _   __   _____ ____  __ __
   / __ )/ ____/ ____/  / __ \ \/ /_  __/ / / / __ \/ | / /  / ___// __ \/ //_/
  / __  / / __/ __/    / /_/ /\  / / / / /_/ / / / /  |/ /   \__ \/ / / / ,<   
 / /_/ / /_/ / /___   / ____/ / / / / / __  / /_/ / /|  /   ___/ / /_/ / /| |  
/_____/\____/_____/  /_/     /_/ /_/ /_/ /_/\____/_/ |_/   /____/_____/_/ |_| 
</pre>

</div>

BGE 开放平台 是一个跨越多级数据的（多）组学数据平台，开发者在获得用户授权后，将可以通过开放平台提供的 API 访问关联用户的（多）组学数据，甚至写入数据。

基于开放平台 API，开发者可避免重复开发采样、提取、测序和生信分析等繁复的流程，直接使用清洁的结构化数据。

开发者可以通过开放平台提供的 API 创建极具创意性的（多）组学应用，如：

* 包含药物代谢或药物服用建议的应用
* 包含体检数据和营养代谢基因的餐饮应用
* 包含肠道菌群数据和痛风相关基因的痛风管理应用
* 基于祖源成分的社交网络应用，等等

BGE 开放平台 API 基于 OAuth 2.0 开发，并使用 SSL/TLS 加密传输，确保用户数据正确无误地授权，并安全地传输到第三方应用，确保用户数据不会被未经授权的应用获得。

# 安装

推荐使用 pip 进行安装。

```shell
$ pip install bge-python-sdk
```

或者

```shell
$ make install
```

再或者

```shell
$ python setup.py install

# 测试

运行单元测试。

```shell
$ pip install pytest
$ make test
```

# 快速开始

BGE 开放平台支持 OAuth2 的两种模式，分别是用户授权模式、客户端模式。

详情请参考开放平台文档 [https://api.bge.genomics.cn/doc](https://api.bge.genomics.cn/doc) 。

## 授权码模式

```python
from bgesdk import OAuth2

code = '???????'  # 用户确认授权后平台返回的授权码
client_id = 'demo'
client_secret = 'demo'
redirect_uri = 'http://test.cn'
oauth2 = OAuth2(client_id, client_secret)
token = oauth2.exchange_authorization_code(code, redirect_uri)
api = oauth2.get_api(token.access_token)
print(api.get_user())
```

## 客户端模式

```python
from bgesdk import OAuth2

client_id = 'demo'
client_secret = 'demo'
oauth2 = OAuth2(client_id, client_secret)
token = oauth2.get_credentials_token()
api = oauth2.get_api(token.access_token)
print(api.get_variants('E-B1243433', 'rs333'))
```

# OAuth2 相关接口

## get_authorization_url

[![开放平台接口文档](https://img.shields.io/badge/开放平台接口文档-lightgrey)](https://api.bge.genomics.cn/doc/OAUTH2/AUTHORIZATION_CODE.html)

获取用户授权页面链接。

![args](https://img.shields.io/badge/参数-args-blue)

* `redirect_uri`

![kwargs](https://img.shields.io/badge/参数-kwargs-blue)

* `state=None` 
* `scopes=None`

![Python 示例](https://img.shields.io/badge/示例-Python-lightgrey)

```python
code = 'xxxxxxxx'  # 用户授权后平台返回的授权码
redirect_uri = 'http://test.cn'  # 回调地址
oauth2 = OAuth2(client_id, client_secret)
url = oauth2.get_authorization_url(
        redirect_uri, state='demo', scopes='profile.default,variant.rsid')
print(url)
```

![Success](https://img.shields.io/badge/输出-Success-green)

```python
>>> https://api.bge.genomics.cn/oauth2/authorize?client_id=???&response_type=code&redirect_uri=???
```

## exchange_authorization_code

[![开放平台接口文档](https://img.shields.io/badge/开放平台接口文档-lightgrey)](https://api.bge.genomics.cn/doc/OAUTH2/AUTHORIZATION_CODE.html)

通过授权码交换**访问令牌**和**刷新令牌**


![参数](https://img.shields.io/badge/参数-args-blue)

* `code`
* `redirect_uri`


![Python 示例](https://img.shields.io/badge/示例-Python-lightgrey)

```python
code = 'xxxxxxxx'  # 用户授权后平台返回的授权码
redirect_uri = 'http://test.cn'  # 回调地址
oauth2 = OAuth2(client_id, client_secret)
token = oauth2.exchange_authorization_code(code, redirect_uri)
print(token)
print(token.access_token)
print(token.access_token == token['access_token'])
```


![Success](https://img.shields.io/badge/输出-Success-green)

```python
>>> Model({
    "token_type": "Bearer",
    "access_token": "Wr6QmVmx5twsjRoasdfXkwmlgfXAYB",
    "refresh_token": "ME06LQoEssAJ55fS633yS4Qg61YSln",
    "scope": "abundance.default model.default profile.default sample.default:read sample.default:write service.file:read service.file:write survey.default variant.chr variant.rsid",
    "expires_in": 21600
})
>>> Wr6QmVmx5twsjRoasdfXkwmlgfXAYB
>>> True
```

## exchange_refresh_token

[![开放平台接口文档](https://img.shields.io/badge/开放平台接口文档-lightgrey)](https://api.bge.genomics.cn/doc/OAUTH2/AUTHORIZATION_CODE.html)

通过**授权码方式**获取的 `access_token` 已经过期或快要过期时，客户端可以通过 `refresh_token` 获取新的 `access_token` 和 `refresh_token`。

![args](https://img.shields.io/badge/参数-args-blue)

* `refresh_token`

![Python 示例](https://img.shields.io/badge/示例-Python-lightgrey)

```python
token = oauth2.exchange_refresh_token(refresh_token)
print(token)
print(token.access_token)
print(token.refresh_token)
```

![Success](https://img.shields.io/badge/输出-Success-green)

```python
>>> Model({
    "token_type": "Bearer",
    "access_token": "Wr6QmVmx5twsjRoasdfXkwmlgfXAYB",
    "refresh_token": "ME06LQoEssAJ55fS633yS4Qg61YSln",
    "scope": "abundance.default model.default profile.default sample.default:read sample.default:write service.file:read service.file:write survey.default variant.chr variant.rsid",
    "expires_in": 21600
})
>>> Wr6QmVmx5twsjRoasdfXkwmlgfXAYB
>>> ME06LQoEssAJ55fS633yS4Qg61YSln
```

## get_credentials_token

[![开放平台接口文档](https://img.shields.io/badge/开放平台接口文档-lightgrey)](https://api.bge.genomics.cn/doc/OAUTH2/CLIENT_CREDENTIALS.html)

通过**客户端模式**直接获取 `access_token`，无需用户授权，过期后重新调用此方
法获取新的 `access_token` 即可。

![Python 示例](https://img.shields.io/badge/示例-Python-lightgrey)

```python
token = oauth2.get_credentials_token()
print(token)
print(token.access_token)
```

![Success](https://img.shields.io/badge/输出-Success-green)

```python
>>> Model({
    "token_type": "Bearer",
    "access_token": "Wr6QmVmx5twsjRoasdfXkwmlgfXAYB",
    "scope": "abundance.default model.default profile.default sample.default:read sample.default:write service.file:read service.file:write survey.default variant.chr variant.rsid",
    "expires_in": 21600
})
>>> Wr6QmVmx5twsjRoasdfXkwmlgfXAYB
>>> ME06LQoEssAJ55fS633yS4Qg61YSln
```

## get_api

获取 `access_token` 后，可以获取一个 `API` 对象，通过 `API` 对象调用平台的接口。

![args](https://img.shields.io/badge/参数-args-green)

* access_token

![Python 示例](https://img.shields.io/badge/示例-Python-lightgrey)

```python
api = oauth2.get_api(access_token)
print(api.access_token)
print(api.get_user)
print(api.get_variants)
...
```

# API 接口

API 对象可用调用以下方法来调用 BGE 开放平台对应的接口。

## get_user

[![开放平台接口文档](https://img.shields.io/badge/开放平台接口文档-lightgrey)](https://api.bge.genomics.cn/doc/USER.html)

获取用户信息。根据 `access_token` 的权限返回拥有访问权限的字段。

![授权码模式](https://img.shields.io/badge/授权码模式-支持-green) ![客户端模式](https://img.shields.io/badge/客户端模式-不支持-red)

![Python 示例](https://img.shields.io/badge/示例-Python-lightgrey)

```python
api = oauth2.get_api(access_token)
user = api.get_user()
print(user)
```

![Success](https://img.shields.io/badge/Output-Success-green)

```
>>> Model({
    "birthday": "1989-10-01T08:00:00+0800",
    "sex": 1,
    "personnelInfoCode": "B32E8D0024466A84A9BE9A3D3E978949",
    "avatar": null,
    "nickname": "张磊",
    "email": "zhanglei3@genomics.cn",
    "username": "zhanglei3",
    "userId": "5be85a3f04c0fb5e93c8cf45",
    "userAddress": "四川省西充县",
    "phone": "17376868481"
})
```

![Error](https://img.shields.io/badge/Output-Error-red)

错误返回方式一致，`SDK` 主要抛出 `BGEError` 和 `APIError` 两个异常。

以下其他 `API` SDK 文档不再提供错误输出示例。

```python
>>> Traceback (most recent call last):
......
bgesdk.error.APIError: {
    "code": 401,
    "msg": "无访问权限",
    "data": null
}
```

## get_variants

[![开放平台接口文档](https://img.shields.io/badge/开放平台接口文档-lightgrey)](https://api.bge.genomics.cn/doc/ANALYSIS/VARIANTS.html)

查询变异位点数据。

![授权码模式](https://img.shields.io/badge/授权码模式-支持-green)

仅支持获取与 `access_token` 所关联用户的样品变异数据。

![客户端模式](https://img.shields.io/badge/客户端模式-支持-green)

仅支持获取与 `access_token` 所关联 `client_id` 创建的样品或预生成归属于该 `client_id` 的样品变异数据。

![Python 示例](https://img.shields.io/badge/示例-Python-lightgrey)

```python
api = oauth2.get_api(access_token)
ret = api.get_variants('E-B12345678901', 'rs762551')
for variant in ret:
    print(variant.source)
    print(variant['is_assayed'])
    print(variant)
```

![Success](https://img.shields.io/badge/Output-Success-green)

```python
>>> {
    "tag": {
        "assembly_synonym": "GRCh38",
        "dbSNP_build": 151
    },
    "update_time": "2019-12-23T23:10:30Z",
    "pipeline_version": "WGSAI3.0-l"
}
>>> True
>>> Model({
    "source": {
        "tag": {
            "assembly_synonym": "GRCh38",
            "dbSNP_build": 151
        },
        "update_time": "2019-12-23T23:10:30Z",
        "pipeline_version": "WGSAI3.0-l"
    },
    "is_assayed": true,
    "genomic_context": {
        "gene": [
            {
                "symbol": "CYP1A2",
                "version": {
                    "mRNA_and_protein": [
                        {
                            "mRNA": "NM_000761",
                            "protein": null
                        }
                    ],
                    "RNA": [],
                    "Genomic": []
                },
                "coding": {
                    "system": "https://www.ncbi.nlm.nih.gov"
                }
            }
        ]
    },
    "variant": {
        "call": {
            "DP": 91,
            "PL": "1384,0,1364",
            "AD": [
                44,
                47
            ],
            "GQ": 99,
            "GT": "0/1"
        },
        "chromosome": "chr15",
        "information": {
            "frequency": {
                "TOPMED": [
                    0.32851522680937817,
                    0.6714847731906218
                ],
                "CAF": [
                    0.3702,
                    0.6298
                ]
            },
            "AN": 2,
            "site_quality": 1355.77,
            "DP": 91
        },
        "type": "snp",
        "genotype": "C/A",
        "reference_base": "C",
        "position": 74749576,
        "alternate_base": [
            "A"
        ]
    },
    "is_genotyped": true,
    "batch_no": 0,
    "alternate_id": [
        "rs762551"
    ],
    "coordinate_system": 0,
    "is_no_call": false,
    "variant_id": "9d82d5fc-b66b-11e9-bfed-00163e104c79"
})
```


## get_samples

[![开放平台接口文档](https://img.shields.io/badge/开放平台接口文档-lightgrey)](https://api.bge.genomics.cn/doc/SAMPLE/)

获取样品列表数据。

![授权码模式](https://img.shields.io/badge/授权码模式-支持-green)

可通过本接口获取授权用户的样品。

![客户端模式](https://img.shields.io/badge/客户端模式-不支持-red)

可通过本接口获取客户端应用通过注册接口注册(或预先生成)的样品。

![kwargs](https://img.shields.io/badge/参数-kwargs-blue)

* `biosample_ids=None`
* `biosample_sites=None`
* `omics=None`
* `project_ids=None`
* `organisms=None`
* `data_availability=None`
* `statuses=None`
* `next_page=None`
* `limit=50`

![Python 示例](https://img.shields.io/badge/示例-Python-lightgrey)

```python
api = oauth2.get_api(access_token)
ret = api.get_samples()
print(ret)
print(ret.next_page)
print(ret.count)
for sample in ret:
    print(sample)
print(sample.organism)
```

![Success](https://img.shields.io/badge/Output-Success-green)

```python
>>> Model({
    "result": [
        {
            "update_time": "2020-08-31T04:03:09+0000",
            "biosample_id": "E-Bxxxxxxxxxx",
            "sample_collection_time": "2017-12-31T16:00:00+0000",
            "organism": {
                "code": 1,
                "display": "human"
            },
            "sequencing": {
                "platform": [],
                "sequencing_time": [
                    "2019-09-24"
                ],
                "instrument_model": [],
                "read_type": [
                    "150+150+10"
                ]
            },
            "project": [
                {
                    "project_name": "demo",
                    "public_description": "员工数据",
                    "project_id": "P-Wxxxxxxxxxx"
                }
            ],
            "data_availability": true,
            "status": {
                "code": 9001,
                "display": "开始解读"
            },
            "primary": true,
            "biosample_site": {
                "code": 11,
                "display": "blood"
            },
            "omic": {
                "code": 1,
                "display": "genomics"
            },
            "statistics": {
                "human_contamination": null,
                "depth": 86.104,
                "variant_counting": 5160417,
                "base_pairs": 266.38,
                "coverage": 0.998
            }
        }
    ],
    "count": 1,
    "next_page": 2
})
>>> 2
>>> 1
>>> Model({
    "update_time": "2020-08-31T04:03:09+0000",
    "biosample_id": "E-Bxxxxxxxxxx",
    "sample_collection_time": "2017-12-31T16:00:00+0000",
    "organism": {
        "code": 1,
        "display": "human"
    },
    "sequencing": {
        "platform": [],
        "sequencing_time": [
            "2019-09-24"
        ],
        "instrument_model": [],
        "read_type": [
            "150+150+10"
        ]
    },
    "project": [
        {
            "project_name": "demo",
            "public_description": "员工数据",
            "project_id": "P-W19??????3"
        }
    ],
    "data_availability": true,
    "status": {
        "code": 9001,
        "display": "开始解读"
    },
    "primary": true,
    "biosample_site": {
        "code": 11,
        "display": "blood"
    },
    "omic": {
        "code": 1,
        "display": "genomics"
    },
    "statistics": {
        "human_contamination": null,
        "depth": 86.104,
        "variant_counting": 5160417,
        "base_pairs": 266.38,
        "coverage": 0.998
    }
})
>>> {
    "code": 1,
    "display": "human"
}
```

## get_sample

获取某个样品的数据。

![授权码模式](https://img.shields.io/badge/授权码模式-支持-green)

可通过本接口获取授权用户的样品。

![客户端模式](https://img.shields.io/badge/客户端模式-支持-green)

可通过本接口获取客户端应用通过注册接口注册(或预先生成)的样品。


![args](https://img.shields.io/badge/参数-args-blue)

* `biosample_id`

![Python 示例](https://img.shields.io/badge/示例-Python-lightgrey)

```python
api = oauth2.get_api(access_token)
ret = api.get_sample('E-B12345678901')
print(ret)
```

![Success](https://img.shields.io/badge/Output-Success-green)

```python
>>> Model({
    "update_time": "2020-08-31T04:03:09+0000",
    "biosample_id": "E-Bxxxxxxxxxx",
    "sample_collection_time": "2017-12-31T16:00:00+0000",
    "organism": {
        "code": 1,
        "display": "human"
    },
    "sequencing": {
        "platform": [],
        "sequencing_time": [
            "2019-09-24"
        ],
        "instrument_model": [],
        "read_type": [
            "150+150+10"
        ]
    },
    "project": [
        {
            "project_name": "demo",
            "public_description": "员工数据",
            "project_id": "P-Wxxxxxxxxxx"
        }
    ],
    "data_availability": true,
    "status": {
        "code": 9001,
        "display": "开始解读"
    },
    "primary": true,
    "biosample_site": {
        "code": 11,
        "display": "blood"
    },
    "omic": {
        "code": 1,
        "display": "genomics"
    },
    "statistics": {
        "human_contamination": null,
        "depth": 86.104,
        "variant_counting": 5160417,
        "base_pairs": 266.38,
        "coverage": 0.998
    }
})
```

## register_sample

[![开放平台接口文档](https://img.shields.io/badge/开放平台接口文档-lightgrey)](https://api.bge.genomics.cn/doc/SAMPLE/REGISTER.html)

注册样品。

![授权码模式](https://img.shields.io/badge/授权码模式-支持-green) ![客户端模式](https://img.shields.io/badge/客户端模式-支持-green)

![args](https://img.shields.io/badge/参数-args-blue)

* `external_sample_id`
* `biosample_site`
* `project_id`

![kwargs](https://img.shields.io/badge/参数-kwargs-blue)

* `duplicate_enabled=False`

![Python 示例](https://img.shields.io/badge/示例-Python-lightgrey)

```python
api = oauth2.get_api(access_token)
biosample_id = api.register_sample('demo', 1, 'P-W1234567')
print(biosample_id)
```

![Success](https://img.shields.io/badge/Output-Success-green)

```python
>>> E-Bxxxxxxxxx
```


## improve_sample

[![开放平台接口文档](https://img.shields.io/badge/开放平台接口文档-lightgrey)](https://api.bge.genomics.cn/doc/SAMPLE/IMPROVE.html)

补充样品信息。

**注意**：如果已经对某字段赋值，将无法对该字段再做修改。

![授权码模式](https://img.shields.io/badge/授权码模式-支持-green) ![客户端模式](https://img.shields.io/badge/客户端模式-支持-green)

![args](https://img.shields.io/badge/参数-args-blue)

* `biosample_id`

![kwargs](https://img.shields.io/badge/参数-kwargs-blue)

* `library_id`
* `library_strategy`
* `library_source`
* ...
* 参数过多，更多请参考【[开放文档](https://api.bge.genomics.cn/doc/SAMPLE/IMPROVE.html)】的接口参数

![Python 示例](https://img.shields.io/badge/示例-Python-lightgrey)

```python
api = oauth2.get_api(access_token)
api.improve_sample(library_id="HWJBAYTGAA170328-18")
```

## get_taxon_abundance

[![开放平台接口文档](https://img.shields.io/badge/开放平台接口文档-lightgrey)](https://api.bge.genomics.cn/doc/ANALYSIS/ABUNDANCE/TAXON.html)

获取样品的微生物类群丰度。

![授权码模式](https://img.shields.io/badge/授权码模式-支持-green) ![客户端模式](https://img.shields.io/badge/客户端模式-不支持-red)

![args](https://img.shields.io/badge/参数-args-blue)

* `biosample_id`

![kwargs](https://img.shields.io/badge/参数-kwargs-blue)

* `taxon_ids=None`
* `next_page=None`
* `limit=50`

![Python 示例](https://img.shields.io/badge/示例-Python-lightgrey)

```python
api = oauth2.get_api(access_token)
ret = api.get_taxon_abundance('E-B1234213412')
print(ret.next_page)
print(ret.limit)
for abundance in ret.result:
    print(abundance)
```

![Success](https://img.shields.io/badge/Output-Success-green)

```python
>>> None
>>> 1
>>> Model({
    "platform_labels": [
        "BGISEQ-500"
    ],
    "background": {
        "reference_cohort": "Chinese Adult",
        "background": {
            "75%": 1.379645,
            "50%": 0.12617,
            "100%": 60.03881,
            "25%": 0.00413,
            "0%": 0,
            "5%": 0,
            "95%": 10.7985825
        },
        "freq": 0.912877697841727,
        "rank_ratio": ">=73%",
        "mean": 2.18322365707434
    },
    "sample_info": {
        "biosample_id": "E-F19149953317",
        "sample_time": "2017-07-01",
        "biosample_site": "feces"
    },
    "observation": {
        "unit": "percent",
        "type": "relative abundance",
        "value": 1.31182
    },
    "taxonomy": {
        "taxon_name": "s__Bacteroides_thetaiotaomicron",
        "coding": {
            "system": "https://open.bge.genomics.cn"
        },
        "taxon_id": "BT1",
        "lineage": "k__Bacteria|p__Bacteroidetes|c__Bacteroidia|o__Bacteroidales|f__Bacteroidaceae|g__Bacteroides|s__Bacteroides_fragilis",
        "rank": "species"
    }
})
```

## get_func_abundance

[![开放平台接口文档](https://img.shields.io/badge/开放平台接口文档-lightgrey)](https://api.bge.genomics.cn/doc/ANALYSIS/ABUNDANCE/FUNCTION.html)

获取样品的微生物功能丰度。

![授权码模式](https://img.shields.io/badge/授权码模式-支持-green) ![客户端模式](https://img.shields.io/badge/客户端模式-不支持-red)

![args](https://img.shields.io/badge/参数-args-blue)

* `biosample_id`
* `catalog`

![kwargs](https://img.shields.io/badge/参数-kwargs-blue)

* `ids=None`
* `next_page=None`
* `limit=50`

![Python 示例](https://img.shields.io/badge/示例-Python-lightgrey)

```python
api = oauth2.get_api(access_token)
ret = api.get_func_abundance('E-B1234213412', 'go')
print(ret.next_page)
print(ret.limit)
for abundance in ret.result:
    print(abundance)
```

![Success](https://img.shields.io/badge/Output-Success-green)

```python
>>> V0hAMzdiYzdkZDItOWJjMi00YzdiLWE4Y2MtMTJjNjVhYTg1NWFm
>>> 1
>>> Model({
    "sample_info": {
        "biosample_id": "E-F19634792132",
        "sample_time": null,
        "biosample_site": "feces"
    },
    "platform_labels": [],
    "data_element_id": "000b52a6-b364-11e9-bfed-00163e104c79",
    "coding": {
        "system": "go_HUMAnN2_0.11",
        "id": "GO:1990063"
    },
    "observation": {
        "unit": "percent",
        "type": "relative abundance",
        "value": 4.38145e-06
    }
})
```

## get_gene_abundance

[![开放平台接口文档](https://img.shields.io/badge/开放平台接口文档-lightgrey)](https://api.bge.genomics.cn/doc/ANALYSIS/ABUNDANCE/GENE.html)

本接口用户获取用户微生物样本的基因定量结果, 样品类型仅限于肠道微生物。

![授权码模式](https://img.shields.io/badge/授权码模式-支持-green) ![客户端模式](https://img.shields.io/badge/客户端模式-不支持-red)

![args](https://img.shields.io/badge/参数-args-blue)

* `biosample_id`
* `catalog`
* `data_type`

![kwargs](https://img.shields.io/badge/参数-kwargs-blue)

* `ids=None`
* `next_page=None`
* `limit=50`


![Python 示例](https://img.shields.io/badge/示例-Python-lightgrey)

```python
api = oauth2.get_api(access_token)
ret = api.get_gene_abundance('E-B1234213412', 'IGC_9.9M', 'list')
print(ret.next_page)
print(ret.limit)
for abundance in ret.result:
    print(abundance)
```

![Success](https://img.shields.io/badge/Output-Success-green)

```python
>>> R2VuZUFidW5kYW5jZUAx
>>> 1
>>> Model({
    "platform_labels": null,
    "sample_info": {
        "biosample_id": "E-F19800147921",
        "sample_time": "2017-05-17T16:00:00+0000",
        "biosample_site": "feces"
    },
    "observation": {
        "value": 2.18932050758568e-10,
        "software": "IGC_PROFILING(10.1038/nbt.2942/)",
        "type": "relative abundance",
        "unit": "percent"
    },
    "igc_gene": {
        "igc_gene_id": "igc_1",
        "coding": {
            "system": "http://meta.genomics.cn"
        },
        "annotation": {
            "kegg_annotation": "K01824",
            "phylum": "unknown",
            "genus": "unknown",
            "gene_completeness": "Complete",
            "eggnog_annotation": "COG5184",
            "gene_length": 88230
        },
        "igc_gene_name": "T2D-6A_GL0083352"
    }
})
```

## get_upload_token

[![开放平台接口文档](https://img.shields.io/badge/开放平台接口文档-lightgrey)](https://api.bge.genomics.cn/doc/INPUT/FILE.html)

本接口获取的返回数据是用于授权给第三方上传文件用，该接口使用了“阿里云”授权给第三方上传服务的【临时访问凭证】实现方式；

![授权码模式](https://img.shields.io/badge/授权码模式-支持-green) ![客户端模式](https://img.shields.io/badge/客户端模式-支持-green)

![Python 示例](https://img.shields.io/badge/示例-Python-lightgrey)

```python
api = oauth2.get_api(access_token)
ret = api.get_upload_token()
credentials = ret.credentials
destination = ret.destination
bucket_name = ret.bucket_name
endpoint = ret.endpoint
print(ret)


# 阿里云 sdk 部分用于上传文件
from aliyunsdkcore import client
from aliyunsdksts.request.v20150401 import AssumeRoleRequest

import json
import oss2
import requests

auth = oss2.StsAuth(credentials['access_key_id'],
                    credentials['access_key_secret'],
                    credentials['security_token'])

# 使用StsAuth实例初始化存储空间。
bucket = oss2.Bucket(auth, endpoint, bucket_name)

# 上传一个字符串
bucket.put_object('%s/demo.txt' % destination, b'hello world')

# destination 禁止上传带有子目录的文件地址，如下代码会抛出权限错误。
# bucket.put_object('%s/subdir/demo.txt' % destination, b'hello world')
```

![Success](https://img.shields.io/badge/Output-Success-green)

```python
>>> Model({
    "base_uri": "https://pre-bge-developer.oss-cn-shenzhen.aliyuncs.com/DUS-19847281036-AydD47PPV1Z1tYa9aqFnOkUuSnRlbwlQCLSqRVGD/20190716TZ-fc566b0eab42401992c41b9ddf0d80b9",
    "credentials": {
      "access_key_secret": "8FU67XNj5nDXxuzGf2PZ1WKiWnm7Sh14uQKT5RwUviRp",
      "security_token": "CAIShgV1q6Ft5B2yfSjIr4j+fe+CpYtUg/SaaEfJ0zlhf9porrPb1zz2IHBEfnBqCOkcvvsylGhV6f0elqZfdqQAHB2UMZQqvs0Pql35u1kyHBvwv9I+k5SANTW5rXWZtZag6YybIfrZfvCyEQ6m8gZ43br9cxi7QlWhKufnoJV7b9MRLH/aCD1dH4VuOxdFos0XPmezUPG2KUzFj3b3BkhlsRYGQQodj56y2cqB8BHToUTnw+sO3eTLL4OjctNnMeWUOrVdteV9bfjGyzUCqUoIpq15gelI9CnKutaFDkMWzyi9drOFooEwdl8gPvNkXodVoNSgysVAhLXhzpjGwkdEJM9TdCfiWbum+s/OB+eQHfICbIzFFFiKiIjWZ8Gq6l0YUzcVP14UJdB5J3Z6VUZwEmiLe/WspAnAMwuvRfCJgPk8gN03vd6Bn7amKl6eOev7tQ8TJp47aW4xKhcSxhaPW6QacgtKASUFYrGOVtdLcQx5o6HlthGwMyp71SN4suHZbfHbsbxlo+ydOKhLyo0Afp9LnnI3RlDsMdKUh1wTaXZuTMS7ucsHUJa08+2C2/7BI7yEWPoItxBWfC7cqy2VRGkXARDKo4RyOQbHoZSIlPeStrpxHCdyuehnM1i3KMpcpg1v+oW0yBeu7dTlaHSg4W4B0f3j5rNxxmcjJK/90rfN52DijjmeavRnxs2PVWRlHU7rIyUokaqZ2isN9hwNnTm4a04VuhPTkiSSBJRGi63amysUXP8JwLqIE22akz8+WY7T0dEiQvh/ee1CaPG40Dxyy+fvxx/K4N2R604/NreuJ+R7M9YVXEmv+t+2d91TgeZ4Ey67daNCp49Z3xSNz76QUjXW02VRGoABGi3aHhYwCq/z1gxJsSwFSNTn5ppuZXDfVG93zWRhbFEHctExgG9zIsLc/iEuXrtd9gykYavYObpBScdVlQrwvzF8xzGwlzkbKV6pyMgYVEGGeP1rzcPpTe99I2ofu0k1T0VvNpk1dVwmMhi+kOLyFJx4oNcKMesp/W7QnIkiT7Y=",
      "expiration": "2019-07-16T08:29:45Z",
      "access_key_id": "STS.NKK6U6HTu46qjax794sUDAvp5"
    },
    "endpoint": "https://oss-cn-shenzhen.aliyuncs.com",
    "destination": "DUS-19847281036-AydD47PPV1Z1tYa9aqFnOkUuSnRlbwlQCLSqRVGD/20190716TZ-fc566b0eab42401992c41b9ddf0d80b9",
    "bucket": "pre-bge-developer"
})
```

## upload

[![开放平台接口文档](https://img.shields.io/badge/开放平台接口文档-lightgrey)](https://api.bge.genomics.cn/doc/INPUT/FILE.html)

本接口封装了 OSS2 上传部分的代码，用户可以直接上传文件；

![授权码模式](https://img.shields.io/badge/授权码模式-支持-green) ![客户端模式](https://img.shields.io/badge/客户端模式-支持-green)

![Python 示例](https://img.shields.io/badge/示例-Python-lightgrey)

```python
api = oauth2.get_api(access_token)
object_name = api.upload('demo.txt', 'demo')
print(object_name)
with open('demo.txt', 'rb') as fp
    object_name = api.upload('demo_fp.txt', fp)
print(object_name)
```

![Success](https://img.shields.io/badge/Output-Success-green)

```python
>>> DUS-19847281036-AydD47PPV1Z1tYa9aqFnOkUuSnRlbwlQCLSqRVGD/20190716TZ-fc566b0eab42401992c41b9ddf0d80b9/demo.txt
>>> DUS-19847281036-AydD47PPV1Z1tYa9aqFnOkUuSnRlbwlQCLSqRVGD/20190716TZ-fc566b0eab42401992c41b9ddf0d80b9/demo_fp.txt
```

## get_download_url

[![开放平台接口文档](https://img.shields.io/badge/开放平台接口文档-lightgrey)](https://api.bge.genomics.cn/doc/SIGNURL.html)

通过当前接口，获取阿里云 OSS（对象存储）中的文件下载地址。

![授权码模式](https://img.shields.io/badge/授权码模式-支持-green) ![客户端模式](https://img.shields.io/badge/客户端模式-支持-green)

![args](https://img.shields.io/badge/参数-args-blue)

* `object_name`

![kwargs](https://img.shields.io/badge/参数-kwargs-blue)

* `region=domestic`
* `expiration_time=600`

![Python 示例](https://img.shields.io/badge/示例-Python-lightgrey)

```python
api = oauth2.get_api(access_token)
ret = api.get_download_url('ods/?????/???????/E-F19581820449.rxn.relab.tsv')
print(ret)
print(ret.expires)
```

![Success](https://img.shields.io/badge/Output-Success-green)

```python
>>> Model({
    "url": "https://international-file.omgut.com/ods%2Fmicrobiome%2Fprocessed%2Fprofile%2Fe1863.a1863.100.1571133531699.855babe0.E-F19581820449.rxn.relab.tsv?Expires=1573026921&Signature=XlYJTft3WyDMZAp5RRxJqp4v89I%3D&OSSAccessKeyId=STS.NQU74xZgz8R8mgc2RR7cQpwhx&security-token=CAISjgN1q6Ft5B2yfSjIr5LgfI7Mt7hbj5DTb0HS1lIHO%2Bx9n7LDmjz2IHBEfnBqCOkcvvsylGhV6f0elqZfdqQAHB2UMJcttM4GqFz5nR8GLEfwv9I%2Bk5SANTW5tXeZtZag24ybIfrZfvCyER%2Bm8gZ43br9cxi7QlWhKufnoJV7b9MRLG7aCD1dH4V5KxdFos0XPmerwJ%2FPVCTnmW3NFkFllxNhgGdkk8SFz9ab9wDVgS8So40Dro%2FqcJ%2B%2FdJsubtUtWdi4meB7aKfF1zZd8V9N%2BLwxia1P4zDNv9aYDh5J%2BRKNPvHP%2F9EoNBV%2BaKk%2BFulJ9aiizrtx47yNzMKuk04LZLwKCn2EH937mZWVSaX5a4szfLz2YzLgl%2F7WZ8Sl6lN%2BOS5HZUVQa9xnMHJ0ABZqVirECNf%2BpQmbM1r7G%2FbdivhogcIv9Tiyo4rWfWroaq6CzCMVNqU7a04VLBMM1QTjCPRWI1YVKQI%2BXebKENUrMU8F9bmT5hfeEzVp1G1G%2BvHzef7SvbgSc5V15R%2B2Cy6sDhqAAaGtJtVgCSKUeuwpLclibtS3R9Lz67bJx529mac%2FlF%2Fm3UzG2VzbOo9A7u0ki%2Fz804XMTXUbzcpg4mznddj0spBDTAIIUo2gxwJBB7xoYUu%2FBRxCIM7khupOcEkC6G9PXSu9HrnhASVAupGuJewFomj%2FMBokCVUv7pVbAErEqkwz",
    "expires": "1573026921"
})
>>> 1573026921
```

## invoke_model

[![开放平台接口文档](https://img.shields.io/badge/开放平台接口文档-lightgrey)](https://api.bge.genomics.cn/doc/INTERPRETATION/)

可以通过此接口调用基于 BGE 平台数据开发的所有模型，包括但不限于逻辑判断、机器学习等多种方式，涵盖基于基因组、微生物组等多组学生命数据的解读模型。

![授权码模式](https://img.shields.io/badge/授权码模式-支持-green) ![客户端模式](https://img.shields.io/badge/客户端模式-支持-green)


![args](https://img.shields.io/badge/参数-args-blue)

* `model_id`

![kwargs](https://img.shields.io/badge/参数-kwargs-blue)

由模型自行决定。

![Python 示例](https://img.shields.io/badge/示例-Python-lightgrey)

```python
api = oauth2.get_api(access_token)
ret = api.invoke_model('zS68QlusdT2RWsZ', biosample_id='biosample_id')
print(ret)
```

![Success](https://img.shields.io/badge/Output-Success-green)

```python
>>> Model({
    "model_code": 0,
    "model_msg": "success",
    "model_data": {
        "predict_class": "control",
        "disease_probability": 0.3699,   // 患病的风险值
        "predict_probability": {
            "control": 0.6300,
            "Colorectal cancer": 0.3699
        },
        "plot_object": null,
        "verbose": null,
        "threshold": 0.5,
        "background": [
            {
                "group": "case",
                "plot_coord": {
                    "y": [
                        0.8021784953727422,
                        0.693865971256402,
                        // ...  此处省略多条成员
                        0.7108590070087604,
                        0.9058300546690335,
                        0.9844725383226168
                    ],
                    "x": "case"
                }
            },
            {
                "group": "control",
                "plot_coord": {
                    "probability": [
                        0.18308905112729132,
                        0.18400681838344046,
                        // ...  此处省略多条成员
                        0.3337452192894059,
                        0.12690823211358987
                    ],
                    "group": "control"
                }
            }
        ]
    }
})
```

# 图标使用

当前文档中使用了如下图标 `badge`，图标来源于 [https://shields.io/](https://shields.io/)。

* ![args](https://img.shields.io/badge/参数-args-blue)
* ![kwargs](https://img.shields.io/badge/参数-kwargs-blue)
* ![Python 示例](https://img.shields.io/badge/示例-Python-lightgrey)
* ![Success](https://img.shields.io/badge/输出-Success-green)
* ![授权码模式](https://img.shields.io/badge/授权码模式-支持-green)
* ![客户端模式](https://img.shields.io/badge/客户端模式-不支持-red)
* ![文档](https://img.shields.io/badge/文档-lightgrey)

# Contributors

* xiangji1204's [github](https://github.com/xiangji1204)
* leafcoder(leafcoder@gmail.com)'s [github](https://github.com/leafcoder)
