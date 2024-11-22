import sys

from bgesdk.client import API
from bgesdk.error import APIError
from bgesdk.management import constants
from bgesdk.management.command import BaseCommand
from bgesdk.management.utils import (
    config_get,
    get_active_project,
    output,
    output_json,
    read_config
)
from bgesdk.models import ModelEncoder


DEFAULT_OAUTH2_SECTION = constants.DEFAULT_OAUTH2_SECTION
DEFAULT_TOKEN_SECTION = constants.DEFAULT_TOKEN_SECTION


class Command(BaseCommand):

    order = 17
    help = (
        '用于获取小程序加密 URL Link，链接默认于29天后过期，返回的 expire_time 字段'
        '代表过期的时间戳（单位：秒）。'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            'code',
            type=str,
            help='BGE 平台微信应用中控所对应的编号(平台后台配置，需管理员处理）。'
        )
        parser.add_argument(
            '-p',
            '--path',
            type=str,
            help='小程序路径；通过 URL Link 进入的小程序页面路径，必须是已经发布的小'
                 '程序存在的页面，不可携带 query 。path 为空时会跳转小程序主页。'
        )
        parser.add_argument(
            '-q',
            '--query',
            type=str,
            help='小程序参数；通过 URL Link 进入小程序时的query，最大1024个字符。'
        )
        parser.add_argument(
            '-t',
            '--access_token',
            type=str,
            help='访问令牌，为空时默认使用 bge token 命令获取到的 access_token。'
        )

    def handler(self, args):
        access_token = args.access_token
        project = get_active_project()
        oauth2_section = DEFAULT_OAUTH2_SECTION
        token_section = DEFAULT_TOKEN_SECTION
        code = args.code
        path = args.path
        query = args.query
        config = read_config(project)
        if not access_token:
            access_token = config_get(config.get, token_section, 'access_token')
        endpoint = config_get(config.get, oauth2_section, 'endpoint')
        api = API(access_token, endpoint=endpoint, timeout=18.)
        try:
            result = api.applet_url(code, path=path, query=query)
        except APIError as e:
            output('[red]请求失败：[/red]')
            output_json(e.result)
            sys.exit(1)
        output_json(
            result,
            cls=ModelEncoder
        )
