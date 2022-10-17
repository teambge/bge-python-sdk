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

    order = 10
    help='聚合组学数据（目前仅支持聚合数据流中符合平台设定 JSONPath 规则的数值型数据）。'

    def add_arguments(self, parser):
        parser.add_argument(
            'data_element_id',
            type=str,
            help='数据元编号。'
        )
        parser.add_argument(
            'time_dimension',
            choices=(
                'year', 'quarter', 'month', 'week', 'day', 'minute', 'second'
            ),
            default='day',
            type=str,
            help='子聚合的时间维度。'
        )
        parser.add_argument(
            '--start_time',
            required=True,
            type=str,
            help='数据流生成时间的起始时间。'
        )
        parser.add_argument(
            '--end_time',
            type=str,
            help='数据流生成时间的结束时间，为空时默认取当前时间。'
        )
        parser.add_argument(
            '-b',
            '--biosample_id',
            type=str,
            help='生物样品编号。'
        )
        parser.add_argument(
            '-i',
            '--interval',
            type=int,
            default=1,
            help='聚合时间维度间隔。'
        )
        parser.add_argument(
            '--periods',
            type=int,
            default=100,
            help='聚合时间维度返回数。'
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
        config = read_config(project)
        if not access_token:
            access_token = config_get(config.get, token_section, 'access_token')
        endpoint = config_get(config.get, oauth2_section, 'endpoint')
        api = API(access_token, endpoint=endpoint, timeout=18.)
        try:
            result = api.aggregate_omics_data(
                args.data_element_id,
                args.time_dimension,
                args.start_time,
                end_time=args.end_time,
                biosample_id=args.biosample_id,
                interval=args.interval,
                periods=args.periods
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
