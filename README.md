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
    <img src="https://img.shields.io/pypi/dm/bge_python_sdk" data-origin="https://img.shields.io/pypi/dm/bge_python_sdk" alt="PyPI - Downloads">
</p>

</div>

# 安装

推荐使用 pip 进行安装

    $ pip install bgesdk

    或者
    $ cd <BGE_PYTHON_SDK>/
    $ make install

运行单元测试

    $ pip install pytest
    $ cd <BGE_PYTHON_SDK>/
    $ make test

生成本地文档

    $ pip install sphinx sphinx_rtd_theme
    $ cd <BGE_PYTHON_SDK>/
    $ make apidoc


# 快速开始

BGE 开放平台支持 OAuth2 的两种模式，分别是用户授权模式、客户端模式。

详情请参考开放平台文档 https://api.bge.genomics.cn/doc。

## 用户授权模式

```
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

```
from bgesdk import OAuth2

client_id = 'demo'
client_secret = 'demo'
oauth2 = OAuth2(client_id, client_secret)
token = oauth2.get_credentials_token()
api = oauth2.get_api(token.access_token)
print(api.get_variants('E-B1243433', 'rs333'))
```

## SDK 方法列表

### OAuth2 相关接口

* get_authorization_url
* exchange_authorization_code
* exchange_refresh_token
* get_credentials_token
* get_api

示例如下：

```
oauth2 = OAuth2(client_id, client_secret)
token = oauth2.get_credentials_token()
print(token.access_token)
```

### API 接口

* get_user
* get_variants
* get_samples
* get_sample
* register_sample
* improve_sample
* get_taxon_abundance
* get_func_abundance
* get_gene_abundance
* get_upload_token
* get_download_url
* invoke_model

示例如下：

```
oauth2 = OAuth2(client_id, client_secret)
token = oauth2.get_credentials_token()
api = oauth2.get_api(token.access_token)
print(api.get_upload_token())
```

# Contributors

* xiangji1204's [github](https://github.com/xiangji1204)
* leafcoder's [github](https://github.com/leafcoder)