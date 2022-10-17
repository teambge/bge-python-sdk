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
    }
]

# 上传数据长度大于或等于该值时采用分片上传 100MB
MULTIPART_THRESHOLD = 100 * 1024 * 1024

# 单个分片大小 50MB
PART_SIZE = 50 * 1024 * 1024

# 分片上传缺省线程数
MULTIPART_NUM_THREADS = 4
