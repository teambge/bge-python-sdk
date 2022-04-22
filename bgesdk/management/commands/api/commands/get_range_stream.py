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

    order = 8
    help='请求数据流。'

    def add_arguments(self, parser):
        parser.add_argument(
            'data_element_id',
            type=str,
            help='数据元编号。'
        )
        parser.add_argument(
            '-b',
            '--biosample_id',
            type=str,
            help='生物样品编号。'
        )
        parser.add_argument(
            '--start_time',
            type=str,
            help='起始时间。'
        )
        parser.add_argument(
            '--end_time',
            type=str,
            help='终止时间。'
        )
        parser.add_argument(
            '--sort_direction',
            type=str,
            default='desc',
            choices=['desc', 'asc'],
            help='排序方向'
        )
        parser.add_argument(
            '-p',
            '--next_page',
            type=str,
            help='要获取的页码。'
        )
        parser.add_argument(
            '-n',
            '--limit',
            type=int,
            help='每页返回数量，默认值为 100。'
        )
        parser.add_argument(
            '-t',
            '--access_token',
            type=str,
            help='访问令牌，为空时默认使用 bge token 命令获取到的 access_token。'
        )

    def handler(self, args):
        access_token = args.access_token
        data_element_id = args.data_element_id
        project = get_active_project()
        oauth2_section = DEFAULT_OAUTH2_SECTION
        token_section = DEFAULT_TOKEN_SECTION
        config = read_config(project)
        if not access_token:
            access_token = config_get(config.get, token_section, 'access_token')
        endpoint = config_get(config.get, oauth2_section, 'endpoint')
        api = API(access_token, endpoint=endpoint, timeout=18.)
        try:
            result = api.get_range_stream(
                data_element_id,
                biosample_id=args.biosample_id,
                start_time=args.start_time,
                end_time=args.end_time,
                sort_direction=args.sort_direction,
                next_page=args.next_page,
                limit=args.limit
            )
        except APIError as e:
            output('[red]请求失败：[/red]')
            output_json(e.result)
            sys.exit(1)
        output('[green]请求成功：[/green]')
        output_json(
            result,
            cls=ModelEncoder
        )
