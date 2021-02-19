# OAuth2 接口

## \_\_init\_\_

OAuth2 对象可用调用以下方法来调用 BGE 开放平台关于 OAuth2.0 相关的接口。

![args](https://img.shields.io/badge/参数-args-blue)

* `client_id` —— 客户端编号
* `client_secret` —— 客户端密钥

![kwargs](https://img.shields.io/badge/参数-kwargs-blue)

* `endpoint=https://api.bge.genomics.cn` —— 平台服务基础地址
* `max_retries=3` —— 最大重试次数
* `timeout=18` —— 接口请求超时时间
* `verbose=False` —— 开启日志输出

![Python 示例](https://img.shields.io/badge/示例-Python-lightgrey)

```python
from bgesdk import OAuth2

oauth2 = OAuth2(
    client_id, client_secret,
    endpoint='https://api.bge.genomics.cn', max_retries=3, timeout=18)
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

## get_authorization_url

[![开放平台接口文档](https://img.shields.io/badge/开放平台接口文档-lightgrey)](https://api.bge.genomics.cn/doc/OAUTH2/AUTHORIZATION_CODE.html)

获取用户授权页面链接。

![args](https://img.shields.io/badge/参数-args-blue)

* `redirect_uri` —— 第三方应用回调地址

![kwargs](https://img.shields.io/badge/参数-kwargs-blue)

* `state=None` —— 用户授权跳转到回调地址时，本参数将原封不动传递到回调地址
* `scopes=None` —— 权限

![Python 示例](https://img.shields.io/badge/示例-Python-lightgrey)

```python
code = 'xxxxxxxx'  # 用户授权后平台返回的授权码
redirect_uri = 'http://test.cn'  # 回调地址
oauth2 = OAuth2(
    client_id, client_secret,
    endpoint='https://api.bge.genomics.cn', max_retries=3, timeout=18)
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

* `code` —— 授权码
* `redirect_uri` —— 第三方应用回调地址


![Python 示例](https://img.shields.io/badge/示例-Python-lightgrey)

```python
code = 'xxxxxxxx'  # 用户授权后平台返回的授权码
redirect_uri = 'http://test.cn'  # 回调地址
oauth2 = OAuth2(
    client_id, client_secret,
    endpoint='https://api.bge.genomics.cn', max_retries=3, timeout=18)
token = oauth2.exchange_authorization_code(code, redirect_uri)
print(token)
print(token.access_token)
print(token.access_token == token['access_token'])
print(token.refresh())
```

![Success](https://img.shields.io/badge/输出-Success-green)

```python
>>> AuthorizationCodeToken({
    "token_type": "Bearer",
    "access_token": "Wr6QmVmx5twsjRoasdfXkwmlgfXAYB",
    "refresh_token": "ME06LQoEssAJ55fS633yS4Qg61YSln",
    "scope": "abundance.default model.default profile.default sample.default:read sample.default:write service.file:read service.file:write survey.default variant.chr variant.rsid",
    "expires_in": 21600
})
>>> Wr6QmVmx5twsjRoasdfXkwmlgfXAYB
>>> True
>>> AuthorizationCodeToken({
    "token_type": "Bearer",
    "access_token": "ar6QewVmx5twsjewoasdfXkwmlgfXAYB",
    "refresh_token": "ME0ewweLQoEssAJasdf323332S4Qg61YSln",
    "scope": "abundance.default model.default profile.default sample.default:read sample.default:write service.file:read service.file:write survey.default variant.chr variant.rsid",
    "expires_in": 21600
})
```

## exchange_refresh_token

[![开放平台接口文档](https://img.shields.io/badge/开放平台接口文档-lightgrey)](https://api.bge.genomics.cn/doc/OAUTH2/AUTHORIZATION_CODE.html)

通过**授权码方式**获取的 `access_token` 已经过期或快要过期时，客户端可以通过 `refresh_token` 获取新的 `access_token` 和 `refresh_token`。

![args](https://img.shields.io/badge/参数-args-blue)

* `refresh_token` —— 刷新令牌

![Python 示例](https://img.shields.io/badge/示例-Python-lightgrey)

```python
token = oauth2.exchange_refresh_token(refresh_token)
print(token)
print(token.access_token)
print(token.refresh_token)
```

![Success](https://img.shields.io/badge/输出-Success-green)

```python
>>> AuthorizationCodeToken({
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
>>> ClientCredentialsToken({
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

使用本方法获取 `API` 对象时，将继承 `OAuth2.0` 的参数 `endpoint`、`max_retries`、`timeout`、`verbose`。

![args](https://img.shields.io/badge/参数-args-green)

* `access_token` —— 访问令牌

![Python 示例](https://img.shields.io/badge/示例-Python-lightgrey)

```python
api = oauth2.get_api(access_token)
print(api.access_token)
print(api.get_user)
print(api.get_variants)
...
```