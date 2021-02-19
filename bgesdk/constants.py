#-*- coding: utf-8 -*-

# 支持的 OAuth2 授权方式
GRANT_AUTHORIZATION_CODE = 'authorization_code'
GRANT_TYPE_CREDENTIALS = 'client_credentials'

DEFAULT_ENDPOINT = 'https://api.bge.genomics.cn'

ENDPOINTS = [
    {
        'name': '线上环境主服务',
        'endpoint': DEFAULT_ENDPOINT
    },
    {
        'name': '线上环境备份域名',
        'endpoint': 'https://api.bge.omgut.com'
    },
    {
        'name': '预览环境主服务',
        'endpoint': 'https://pre.open.omgut.com'
    },
    {
        'name': '开发环境主服务',
        'endpoint': 'https://dev.open.omgut.com'
    }
]
