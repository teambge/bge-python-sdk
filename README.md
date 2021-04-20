
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
$ pip install -U bge-python-sdk
```

或者

```shell
$ make install
```

再或者

```shell
$ python setup.py install
```

# SDK 文档

更加详细的 SDK 文档请查看 [SDK Documents](https://api.bge.genomics.cn/doc/#/sdk/README)。

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
print(api.get_variants('E-B1243433', 'rs333'))

api = API(token.access_token)
print(api.get_variants('E-B1243433', 'rs333'))
```

# Contributors

* xiangji1204's [github](https://github.com/xiangji1204)
* leafcoder(leafcoder@gmail.com)'s [github](https://github.com/leafcoder)
