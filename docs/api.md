# API 接口

API 对象可用调用以下方法来调用 BGE 开放平台对应的接口。

## \_\_init\_\_

可直接初始化 `API` 对象，效果同 `OAuth2.get_api` 方法，不过可以单独使用，无
需初始化 `OAuth2` 对象。

![args](https://img.shields.io/badge/参数-args-blue)

* `access_token` —— 访问令牌

![kwargs](https://img.shields.io/badge/参数-kwargs-blue)

* `endpoint=https://api.bge.genomics.cn` —— 平台服务基础地址
* `max_retries=3` —— 最大重试次数
* `timeout=18` —— 接口请求超时时间
* `verbose=False` —— 开启日志输出

![Python 示例](https://img.shields.io/badge/示例-Python-lightgrey)

```python
from bgesdk import OAuth2, API

oauth2 = OAuth2(
    client_id, client_secret,
    endpoint='https://api.bge.genomics.cn', max_retries=3, timeout=18)
...
api = oauth2.get_api(access_token)
...

api = API(
    access_token, endpoint='https://api.bge.genomics.cn',
    max_retries=3, timeout=18)
print(api.access_token)
print(api.get_user)
print(api.get_variants)
...
```

## alive

判断 BGE 开放平台的可用性。

![Python 示例](https://img.shields.io/badge/示例-Python-lightgrey)

```python
from bgesdk import OAuth2

oauth2 = OAuth2(
    client_id, client_secret,
    endpoint='https://api.bge.genomics.cn', max_retries=3, timeout=18)
print(oauth2.alive())
```

![Success](https://img.shields.io/badge/输出-Success-green)

```python
>>> True
```

## get_user

[![开放平台接口文档](https://img.shields.io/badge/开放平台接口文档-lightgrey)](https://api.bge.genomics.cn/doc/USER.html)

获取用户信息。根据 `access_token` 的权限返回拥有访问权限的字段。

![授权码模式](https://img.shields.io/badge/授权码模式-支持-green) ![客户端模式](https://img.shields.io/badge/客户端模式-不支持-red)

![Python 示例](https://img.shields.io/badge/示例-Python-lightgrey)

```python
api = API(
    access_token, endpoint='https://api.bge.genomics.cn',
    max_retries=3, timeout=18)
user = api.get_user()
print(user)
print(user.json())
print(user.dumps(indent=4))
```

![Success](https://img.shields.io/badge/Output-Success-green)

```
>>> Model({
    "birthday": "1989-10-01T08:00:00+0800",
    "sex": 1,
    "personnelInfoCode": "32333333333332323232323232323",
    "avatar": null,
    "nickname": "zhangsan",
    "email": "leafcoder@gmail.com",
    "username": "leafcoder",
    "userId": "323234132412412341234",
    "userAddress": "广东省有钱市",
    "phone": "17376??????"
})
>>> {u'username': u'zhanglei3', u'userAddress': u'广东省有钱市', u'userId': u'323234132412412341234', u'sex': 1, u'phone': u'17376??????', u'personnelInfoCode': u'32333333333332323232323232323', u'birthday': u'1989-10-01T08:00:00+0800', u'avatar': None, u'nickname': u'zhangsan', u'email': u'leafcoder@gmail.com'}
>>> {
    "birthday": "1989-10-01T08:00:00+0800",
    "sex": 1,
    "personnelInfoCode": "32333333333332323232323232323",
    "avatar": null,
    "nickname": "zhangsan",
    "email": "leafcoder@gmail.com",
    "username": "zhangsan",
    "userId": "323234132412412341234",
    "userAddress": "广东省有钱市",
    "phone": "17376??????"
}
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
api = API(
    access_token, endpoint='https://api.bge.genomics.cn',
    max_retries=3, timeout=18)
ret = api.get_variants('E-B12345678901', 'rs762551,rs333')
for variant in ret:
    print(variant.source)
    print(variant['is_assayed'])
    print(variant)
    break
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

* `biosample_ids=None` —— 生物样品编号，逗号分割多个
* `biosample_sites=None` —— 采样位置，逗号分割多个
* `omics=None` —— 组学，逗号分割多个
* `project_ids=None` —— 项目编号，逗号分割多个
* `organisms=None` —— 生物体，逗号分割多个
* `data_availability=None` —— 数据可用性
* `statuses=None` —— 样品状态，逗号分割多个
* `next_page=None` —— 下一页
* `limit=50` —— 单页返回数量

![Python 示例](https://img.shields.io/badge/示例-Python-lightgrey)

```python
api = API(
    access_token, endpoint='https://api.bge.genomics.cn',
    max_retries=3, timeout=18)
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
api = API(
    access_token, endpoint='https://api.bge.genomics.cn',
    max_retries=3, timeout=18)
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

* `external_sample_id` —— 外部样品编号（生产编号）
* `biosample_site` —— 采样位置
* `project_id` —— 项目编号

![kwargs](https://img.shields.io/badge/参数-kwargs-blue)

* `duplicate_enabled=False` —— 是否允许注册重复的外部样品编号（生产编号）

![Python 示例](https://img.shields.io/badge/示例-Python-lightgrey)

```python
api = API(
    access_token, endpoint='https://api.bge.genomics.cn',
    max_retries=3, timeout=18)
ret = api.register_sample('demo', 1, 'P-W1234567')
print(ret)
print(ret.biosample_id)
```

![Success](https://img.shields.io/badge/Output-Success-green)

```python
>>> Model({
    'biosample_id': 'E-Bxxxxxxxxx'
})
>>> E-Bxxxxxxxxx
```


## improve_sample

[![开放平台接口文档](https://img.shields.io/badge/开放平台接口文档-lightgrey)](https://api.bge.genomics.cn/doc/SAMPLE/IMPROVE.html)

补充样品信息。

**注意**：如果已经对某字段赋值，将无法对该字段再做修改。

![授权码模式](https://img.shields.io/badge/授权码模式-支持-green) ![客户端模式](https://img.shields.io/badge/客户端模式-支持-green)

![args](https://img.shields.io/badge/参数-args-blue)

* `biosample_id` —— 生物样品编号

![kwargs](https://img.shields.io/badge/参数-kwargs-blue)

* `library_id`
* `library_strategy`
* `library_source`
* ...
* 参数过多，更多请参考【[开放文档](https://api.bge.genomics.cn/doc/SAMPLE/IMPROVE.html)】的接口参数

![Python 示例](https://img.shields.io/badge/示例-Python-lightgrey)

```python
api = API(
    access_token, endpoint='https://api.bge.genomics.cn',
    max_retries=3, timeout=18)
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
api = API(
    access_token, endpoint='https://api.bge.genomics.cn',
    max_retries=3, timeout=18)
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
api = API(
    access_token, endpoint='https://api.bge.genomics.cn',
    max_retries=3, timeout=18)
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
api = API(
    access_token, endpoint='https://api.bge.genomics.cn',
    max_retries=3, timeout=18)
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
api = API(
    access_token, endpoint='https://api.bge.genomics.cn',
    max_retries=3, timeout=18)
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
api = API(
    access_token, endpoint='https://api.bge.genomics.cn',
    max_retries=3, timeout=18)
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

## upload

[![开放平台接口文档](https://img.shields.io/badge/开放平台接口文档-lightgrey)](https://api.bge.genomics.cn/doc/INPUT/FILE.html)

本接口封装了 OSS2 上传部分的代码，用户可以直接上传文件；

![授权码模式](https://img.shields.io/badge/授权码模式-支持-green) ![客户端模式](https://img.shields.io/badge/客户端模式-支持-green)

![args](https://img.shields.io/badge/参数-args-blue)

* `filename` -- 文件名，不能出现 `/`，否则将因权限问题无法成功上传
* `file_or_string` -- 文件对象或字符串，文件对象必须以 `rb` 模式打开

![Python 示例](https://img.shields.io/badge/示例-Python-lightgrey)

```python
api = API(
    access_token, endpoint='https://api.bge.genomics.cn',
    max_retries=3, timeout=18)
object_name = api.upload('demo.txt', 'file content is here')
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

## download

[![开放平台接口文档](https://img.shields.io/badge/开放平台接口文档-lightgrey)](https://api.bge.genomics.cn/doc/SIGNURL.html)

通过当前接口，直接下载阿里云 OSS（对象存储）中的文件到 `File Like Object`。

![授权码模式](https://img.shields.io/badge/授权码模式-支持-green) ![客户端模式](https://img.shields.io/badge/客户端模式-支持-green)

![args](https://img.shields.io/badge/参数-args-blue)

* `object_name` —— upload 方法返回的数据即为 `object_name`
* `fp` —— 可写的类文件对象，如果是文件对象需以 `wb` 模式打开文件

![kwargs](https://img.shields.io/badge/参数-kwargs-blue)

* `region=domestic` —— 下载文件访问的服务器所在区域

![Python 示例](https://img.shields.io/badge/示例-Python-lightgrey)

```python
api = API(
    access_token, endpoint='https://api.bge.genomics.cn',
    max_retries=3, timeout=18)

# 下载到流对象
if py3:
    from io import BytesIO
    stream = BytesIO()
else:
    from cStringIO import StringIO
    stream = StringIO()
api.download('ods/?????/???????/E-F19581820449.rxn.relab.tsv', stream)
print(stream.getvalue())

# 下载到文件
with open('demo/test.txt', 'wb') as fp:
    api.download('ods/?????/???????/E-F19581820449.rxn.relab.tsv', fp)
```


## get_range_stream

根据数据流数据生成时间范围获取数据。

![授权码模式](https://img.shields.io/badge/授权码模式-支持-green) ![客户端模式](https://img.shields.io/badge/客户端模式-支持-green)


![args](https://img.shields.io/badge/参数-args-blue)

* `data_element_id`


![kwargs](https://img.shields.io/badge/参数-kwargs-blue)


* `biosample_id=None`: 客户端模式下，必须提供参数 biosample_id
* `start_time=None`
* `end_time=None`
* `sort_direction=desc`
* `next_page=None`
* `limit=100`

![Python 示例](https://img.shields.io/badge/示例-Python-lightgrey)

```python
api = API(
    access_token, endpoint='https://api.bge.genomics.cn',
    max_retries=3, timeout=18)
namespace = 'test'
fundamental_entity_id = '8be21998-7c8a-11eb-86eb-48a47299ee4a'
data_element_id = '02393f70-c7e4-11e9-bfed-00163e104c79'
ret = api.get_range_stream(
    data_element_id, biosample_id='E-B1234213412'
    start_time='1970-01', end_time='2021-04-01 10:11:00.123456')
print(ret)
print(ret.result[0].stream_id == ret.result[0]['stream_id'])
```

![Success](https://img.shields.io/badge/Output-Success-green)

```python
>>> Model({
        "result": [
            {
                "stream_id": "aa3609d4-7cb9-11eb-b8f3-48a47299ee4a",
                "data_element": {
                    "data_element_name": "oxycodone",
                    "data_element_id": "02393f70-c7e4-11e9-bfed-00163e104c79",
                    "data_element_description": "羟考酮"
                },
                "stream_generate_time_mask": "1111-00-00T00:00:00.000000±1111",
                "stream_meta": {
                    "user_entity_id": "m279xkEaxxPg6x6VP6pagg5K6",
                    "namespace": "aaaa"
                },
                "create_time": "2021-03-04T15:17:23+0800",
                "stream_data": {
                    "name": "leo"
                },
                "stream_generate_time": "1986-01-01T00:00:00+0800"
            },
            {
                "stream_id": "ae355aa8-7cb9-11eb-b8f3-48a47299ee4a",
                "data_element": {
                    "data_element_name": "oxycodone",
                    "data_element_id": "02393f70-c7e4-11e9-bfed-00163e104c79",
                    "data_element_description": "羟考酮"
                },
                "stream_generate_time_mask": "1111-00-00T00:00:00.000000±1111",
                "stream_meta": {
                    "user_entity_id": "m279xkEaxxPg6x6VP6pagg5K6",
                    "namespace": "aaaa"
                },
                "create_time": "2021-03-04T15:17:29+0800",
                "stream_data": {
                    "name": "leo"
                },
                "stream_generate_time": "1987-01-01T00:00:00+0800"
            },
            {
                "stream_id": "bbeca010-7cba-11eb-97e9-48a47299ee4a",
                "data_element": {
                    "data_element_name": "oxycodone",
                    "data_element_id": "02393f70-c7e4-11e9-bfed-00163e104c79",
                    "data_element_description": "羟考酮"
                },
                "stream_generate_time_mask": "1111-00-00T00:00:00.000000±1111",
                "stream_meta": {
                    "user_entity_id": "m279xkEaxxPg6x6VP6pagg5K6",
                    "namespace": "aaaa"
                },
                "create_time": "2021-03-04T15:25:02+0800",
                "stream_data": {
                    "name": "leo"
                },
                "stream_generate_time": "1987-01-01T00:00:00+0800"
            }
        ],
        "count": 3,
        "next_page": null
    })
>>> True
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
api = API(
    access_token, endpoint='https://api.bge.genomics.cn',
    max_retries=3, timeout=18)
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

## deploy_model

可以通过此接口部署模型或修改模型的配置内容。

![授权码模式](https://img.shields.io/badge/授权码模式-支持-green) ![客户端模式](https://img.shields.io/badge/客户端模式-支持-green)


![args](https://img.shields.io/badge/参数-args-blue)

* `model_id`
* `source_file`

![kwargs](https://img.shields.io/badge/参数-kwargs-blue)

* `handler=index.handler`
* `memory_size=128`
* `runtime=python3`
* `comment=None`
* `timeout=900`

![Python 示例](https://img.shields.io/badge/示例-Python-lightgrey)

```python
api = API(
    access_token, endpoint='https://api.bge.genomics.cn',
    max_retries=3, timeout=18)
ret = api.deploy_model('zS68QlusdT2RWsZ', source_file='/home/ubuntu/test_mode.zip')
print(ret)
```

![Success](https://img.shields.io/badge/Output-Success-green)

```python
>>> Model({
    "version": 1
})
```


## rollback_model

回滚至模型之前部署的某个源码版本，配置不回滚。

![授权码模式](https://img.shields.io/badge/授权码模式-支持-green) ![客户端模式](https://img.shields.io/badge/客户端模式-支持-green)


![args](https://img.shields.io/badge/参数-args-blue)

* `model_id`
* `version`

![Python 示例](https://img.shields.io/badge/示例-Python-lightgrey)

```python
api = API(
    access_token, endpoint='https://api.bge.genomics.cn',
    max_retries=3, timeout=18)
ret = api.rollback_model('zS68QlusdT2RWsZ', version=5)
print(ret)
```

![Success](https://img.shields.io/badge/Output-Success-green)

```python
>>> Model({
    "version": 5
})
```
