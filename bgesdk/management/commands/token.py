import argparse
import sys

from bgesdk.client import OAuth2
from bgesdk.error import APIError
from bgesdk.management import constants
from bgesdk.management.utils import get_active_project, config_get, \
                                    get_config_path, get_config_parser


def init_parser(subparsers):
    token_p = subparsers.add_parser(
        'token',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        help='获取、保存访问令牌。'
    )
    token_p.set_defaults(method=handler, parser=token_p)


def handler(args):
    project = get_active_project()
    config_path = get_config_path(project)
    config_parser = get_config_parser(config_path)
    oauth2_section = constants.DEFAULT_OAUTH2_SECTION
    client_id = config_get(config_parser.get, oauth2_section, 'client_id')
    client_secret = config_get(
        config_parser.get, oauth2_section, 'client_secret')
    endpoint = config_get(config_parser.get, oauth2_section, 'endpoint')
    oauth2 = OAuth2(
        client_id, client_secret, endpoint=endpoint, timeout=60.)
    try:
        token_result = oauth2.get_credentials_token()
    except APIError as e:
        print('令牌获取出错: {}'.format(e))
        sys.exit(1)
    _write_token_config(project, token_result)
    print('令牌内容如下：')
    print('')
    for key in ['access_token', 'token_type', 'expires_in', 'scope']:
        print('{} = {}'.format(key, token_result[key]))


def _write_token_config(project, token_result):
    access_token = token_result['access_token']
    token_type = token_result['token_type']
    expires_in = str(token_result['expires_in'])
    scope = token_result['scope']
    config_path = get_config_path(project)
    config_parser = get_config_parser(config_path)
    section_name = constants.DEFAULT_TOKEN_SECTION
    if section_name not in config_parser.sections():
        config_parser.add_section(section_name)
    config_parser.set(section_name, 'access_token', access_token)
    config_parser.set(section_name, 'token_type', token_type)
    config_parser.set(section_name, 'expires_in', expires_in)
    config_parser.set(section_name, 'scope', scope)
    with open(config_path, 'w') as config_file:
        config_parser.write(config_file)
    print('令牌已保存至：{}'.format(config_path))
