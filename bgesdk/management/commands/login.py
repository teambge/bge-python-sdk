import sys
import webbrowser

from six.moves import input
from time import sleep

from bgesdk.client import OAuth2
from bgesdk.error import APIError
from bgesdk.management import constants
from bgesdk.management.command import BaseCommand
from bgesdk.management.utils import (
    get_active_project, config_get, get_config_path, get_config_parser
)


class Command(BaseCommand):

    order = 3
    help='授权码模式登录并获取授权令牌。'

    def add_arguments(self, parser):
        parser.add_argument(
            'redirect_uri',
            help='授权完成后的回调地址。'
        )
        parser.add_argument(
            '--state',
            help='额外信息，原样作为参数返回给回调地址。'
        )
        parser.add_argument(
            '--scopes',
            help='权限标识'
        )

    def handler(self, args):
        project = get_active_project()
        config_path = get_config_path(project)
        config_parser = get_config_parser(config_path)
        oauth2_section = constants.DEFAULT_OAUTH2_SECTION
        client_id = config_get(config_parser.get, oauth2_section, 'client_id')
        client_secret = config_get(
            config_parser.get, oauth2_section, 'client_secret')
        endpoint = config_get(config_parser.get, oauth2_section, 'endpoint')
        redirect_uri = args.redirect_uri
        oauth2 = OAuth2(
            client_id, client_secret, endpoint=endpoint, timeout=60.)
        authorization_url = oauth2.get_authorization_url(
            redirect_uri, state=args.state, scopes=args.scopes
        )
        print('授权页面地址为：{}'.format(authorization_url))
        print('浏览器启动中...')
        webbrowser.open(authorization_url, new=1, autoraise=False)
        sleep(1)
        print('\n请在浏览器登录并完成授权，复制跳转后页面链接的 code 参数并关闭浏览器。\n')
        while True:
            code = input('请输入 code：').strip()
            if code:
                break
        try:
            token_result = oauth2.exchange_authorization_code(
                code, redirect_uri=redirect_uri
            )
        except APIError as e:
            print('令牌获取出错: {}'.format(e))
            sys.exit(1)
        self._write_token_config(project, token_result)
        print('令牌内容如下：')
        print('')
        for key in [
                'access_token', 'token_type', 'expires_in', 'scope',
                'refresh_token']:
            print('{} = {}'.format(key, token_result[key]))

    def _write_token_config(self, project, token_result):
        access_token = token_result['access_token']
        token_type = token_result['token_type']
        expires_in = str(token_result['expires_in'])
        scope = token_result['scope']
        refresh_token = token_result['refresh_token']
        config_path = get_config_path(project)
        config_parser = get_config_parser(config_path)
        section_name = constants.DEFAULT_TOKEN_SECTION
        if section_name not in config_parser.sections():
            config_parser.add_section(section_name)
        config_parser.set(section_name, 'access_token', access_token)
        config_parser.set(section_name, 'token_type', token_type)
        config_parser.set(section_name, 'expires_in', expires_in)
        config_parser.set(section_name, 'scope', scope)
        config_parser.set(section_name, 'refresh_token', refresh_token)
        with open(config_path, 'w') as config_file:
            config_parser.write(config_file)
        print('令牌已保存至：{}'.format(config_path))
