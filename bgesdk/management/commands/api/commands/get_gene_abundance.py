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

    order = 9
    help = '获取微生物基因丰度。'

    def add_arguments(self, parser):
        # 基因丰度
        parser.add_argument(
            'biosample_id',
            type=str,
            help='生物样品编号。'
        )
        parser.add_argument(
            'catalog',
            type=str,
            choices=['IGC_9.9M', 'UniRef90_HUMAnN2_0.11'],
            help='目录标签。'
        )
        parser.add_argument(
            '-d',
            '--data_type',
            type=str,
            required=True,
            choices=['list', 'file'],
            help='返回数据类型。'
        )
        parser.add_argument(
            '--ids',
            type=str,
            help='BGE 物种 IGC 基因编号，多个值以逗号分割，如：igc_50,igc_51。'
        )
        parser.add_argument(
            '-t',
            '--access_token',
            type=str,
            help='访问令牌，为空时默认使用 bge token 命令获取到的 access_token。'
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
            help='每页返回数量，默认值为 50。'
        )

    def handler(self, args):
        access_token = args.access_token
        biosample_id = args.biosample_id
        catalog = args.catalog
        data_type = args.data_type
        project = get_active_project()
        oauth2_section = DEFAULT_OAUTH2_SECTION
        token_section = DEFAULT_TOKEN_SECTION
        config = read_config(project)
        if not access_token:
            access_token = config_get(config.get, token_section, 'access_token')
        endpoint = config_get(config.get, oauth2_section, 'endpoint')
        api = API(access_token, endpoint=endpoint, timeout=18.)
        try:
            result = api.get_gene_abundance(
                biosample_id,
                catalog,
                data_type,
                ids=args.ids,
                next_page=args.next_page,
                limit=args.limit
            )
        except APIError as e:
            output('[red]请求失败：[/red]')
            output_json(e.result)
            sys.exit(1)
        output_json(
            result,
            cls=ModelEncoder
        )
