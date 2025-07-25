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

# 解码基因报告域
REPORT_DOMAINS = dict((
    ('traits', '个体特征'),
    ('pgx', '遗传疾病'),
    ('common_disease_risk', '药物'),
    ('genetic_disease_mendelian', '多基因预测'),
    ('genetic_disease_risk', '单基因风险'),
))

REPORT_DOMAIN_VERSIONS = dict((
    ('traits_v1', '个体特征'),
    ('genetic_disease_mendelian_v1', '遗传疾病'),
    ('pgx_v1', '个体用药'),
    ('pgx_v2', '新版个体用药'),
    ('common_disease_risk_v1', '复杂疾病(多基因预测)'),
    ('common_disease_risk_v2', '新版复杂疾病(多基因预测)'),
    ('genetic_disease_risk_v1', '单基因风险'),
    ('vitamin_d_v1', '维生素 D'),
))

# 上传数据长度大于或等于该值时采用分片上传 100MB
MULTIPART_THRESHOLD = 100 * 1024 * 1024

# 单个分片大小 50MB
PART_SIZE = 50 * 1024 * 1024

# 分片上传缺省线程数
MULTIPART_NUM_THREADS = 4
