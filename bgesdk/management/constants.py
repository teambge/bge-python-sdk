
# For terminal commands
DEFAULT_MODEL_SECTION = 'Model'
DEFAULT_OAUTH2_SECTION = 'OAuth2'
DEFAULT_TOKEN_SECTION = 'Token'
DEFAULT_PROJECT = 'default'
DEFAULT_MODEL_TIMEOUT = 60

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