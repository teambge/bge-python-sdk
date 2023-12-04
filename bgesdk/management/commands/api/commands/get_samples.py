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

NOT_PARAM_FIELDS = (
    'command',
    'parser',
    'method',
    'access_token',
    'subcommand'
)


class Command(BaseCommand):

    order = 2
    help = '获取样品信息。'

    def add_arguments(self, parser):
        parser.add_argument(
            '-b',
            '--biosample_ids',
            type=str,
            help='生物样品编号，逗号分割多个。'
        )
        parser.add_argument(
            '--omics',
            type=str,
            help='所属组学，取值范围：1-2。'
        )
        parser.add_argument(
            '--project_ids',
            type=str,
            help='所属项目，逗号分割多个。'
        )
        parser.add_argument(
            '--organisms',
            type=str,
            help='样品生物体，取值范围：1-3。'
        )
        parser.add_argument(
            '--data_availability',
            default=None,
            action='store_true',
            help='数据可用。'
        )
        parser.add_argument(
            '--no-data_availability',
            dest='data_availability', 
            action='store_false',
            help='数据不可用。'
        )
        parser.add_argument(
            '--statuses',
            type=str,
            help='数据状态，详情见 BGE 开放平台文档 https://api.bge.genomics.cn/doc/#/ot'
                 'hers/appendix?id=样品状态编码表'
        )
        parser.add_argument(
            '--require_files',
            default=None,
            action='store_true',
            help='要求接口返回值中包含文件相关字段 files。'
        )
        parser.add_argument(
            '-p',
            '--next_page',
            type=int,
            help='要获取的页码。'
        )
        parser.add_argument(
            '-n',
            '--limit',
            type=int,
            help='每页返回数量，默认值为 50。'
        )
        parser.add_argument(
            '-t',
            '--access_token',
            type=str,
            help='访问令牌，为空时默认使用 bge token 命令获取到的 access_token。'
        )

    def handler(self, args):
        access_token = args.access_token
        params = vars(args)
        for field in NOT_PARAM_FIELDS:
            params.pop(field, None)
        project = get_active_project()
        oauth2_section = DEFAULT_OAUTH2_SECTION
        token_section = DEFAULT_TOKEN_SECTION
        config = read_config(project)
        if not access_token:
            access_token = config_get(config.get, token_section, 'access_token')
        endpoint = config_get(config.get, oauth2_section, 'endpoint')
        api = API(access_token, endpoint=endpoint, timeout=18.)
        try:
            result = api.get_samples(**params)
        except APIError as e:
            output('[red]请求失败：[/red]')
            output_json(e.result)
            sys.exit(1)
        output('[green]请求成功：[/green]')
        output_json(
            result,
            cls=ModelEncoder
        )
