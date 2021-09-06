
# For terminal commands
DEFAULT_MODEL_SECTION = 'Model'
DEFAULT_OAUTH2_SECTION = 'OAuth2'
DEFAULT_TOKEN_SECTION = 'Token'
DEFAULT_PROJECT = 'default'
DEFAULT_MODEL_TIMEOUT = None

MODEL_CONTAINER_PREFIX = 'bge-model-'
TEST_SERVER_PORT = 9999
TEST_SERVER_ENDPOINT = 'http://0.0.0.0:{}'.format(TEST_SERVER_PORT)


CLIENT_CREDENTIALS_CONFIGS = [
    ('client_id', {
        'type': 'str',
        'description': '客户端编号',
        'secure': True
    }),
    ('client_secret', {
        'type': 'str',
        'description': '客户端密钥',
        'secure': True
    }),
    ('endpoint', {
        'default': 'https://api.bge.genomics.cn',
        'type': 'str',
        'description': '访问域名'
    })
]

TAB_CHOICES = [
        ('genetic_diseases', '遗传疾病'),
        ('health_risks', '健康风险'),
        ('physiological_index', '生理指标'),
        ('comprehensive', '综合'),
        ('tools', '工具')
    ]
LANGUAGE_CHOICES = [('zh', '中文版'), ('en', 'English')]

TITLE_NAME = {
    'brief_intro': '简介',
    'method': '方法',
    'model_evaluation': '模型评价',
    'data_set_size': '数据规模',
    'ethnicity': '研究族群',
    'limitation': '局限性说明',
}


API_TABLE = {
    'QueryParams': '请求参数',
    'Success': '返回参数',
    'State': '参数'
}
