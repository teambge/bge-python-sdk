# 快速开始

BGE 开放平台支持 OAuth2 的两种模式，分别是用户授权模式、客户端模式。

详情请参考开放平台文档 [https://api.bge.genomics.cn/doc](https://api.bge.genomics.cn/doc) 。

## ENDPOINTS

BGE 开放平台提供了如下可用的 `endpoint`。

| endpoint                    | 解释                                                        |
| --------------------------- | ----------------------------------------------------------- |
| https://api.bge.genomics.cn | **线上环境** 主域名地址                                     |
| https://api.bge.omgut.com   | **线上环境** 副域名地址，主域名地址不可用时可替换此域名地址 |

## 授权码模式

```python
from bgesdk import OAuth2, API

code = '???????'  # 用户确认授权后平台返回的授权码
client_id = 'demo'
client_secret = 'demo'
redirect_uri = 'http://test.cn'
oauth2 = OAuth2(
    client_id, client_secret,
    endpoint='https://api.bge.genomics.cn', max_retries=3, timeout=16,
    verbose=False)
token = oauth2.exchange_authorization_code(code, redirect_uri)

api = oauth2.get_api(token.access_token)
print(api.get_user())

api = API(token.access_token)
print(api.get_user())
```

## 客户端模式

```python
from bgesdk import OAuth2, API

client_id = 'demo'
client_secret = 'demo'
oauth2 = OAuth2(
    client_id, client_secret,
    endpoint='https://api.bge.genomics.cn', max_retries=3, timeout=16,
    verbose=False)
token = oauth2.get_credentials_token()

api = oauth2.get_api(token.access_token)
print(api.get_variants('E-B1243433', 'rs1,rs333'))

api = API(token.access_token)
print(api.get_variants('E-B1243433', 'rs1,rs333'))
```