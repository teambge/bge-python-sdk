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
    help = '请求数据项。'

    def add_arguments(self, parser):
        parser.add_argument(
            'biosample_id',
            type=str,
            help='生物样品编号。'
        )
        parser.add_argument(
            'namespace',
            type=str,
            help='命名空间'
        )
        parser.add_argument(
            '--data_element_ids',
            type=str,
            help='数据元编号，与 collection_id 互斥。'
        )
        parser.add_argument(
            '--collection_id',
            type=str,
            help='数据集编号，与 data_element_ids 互斥。'
        )
        parser.add_argument(
            '-p',
            '--next_page',
            type=int,
            help='要获取的页码。'
        )
        parser.add_argument(
            '-t',
            '--access_token',
            type=str,
            help='访问令牌，为空时默认使用 bge token 命令获取到的 access_token。'
        )

    def handler(self, args):
        access_token = args.access_token
        namespace = args.namespace
        biosample_id = args.biosample_id
        project = get_active_project()
        oauth2_section = DEFAULT_OAUTH2_SECTION
        token_section = DEFAULT_TOKEN_SECTION
        config = read_config(project)
        if not access_token:
            access_token = config_get(config.get, token_section, 'access_token')
        endpoint = config_get(config.get, oauth2_section, 'endpoint')
        api = API(access_token, endpoint=endpoint, timeout=18.)
        try:
            result = api.get_data_items(
                namespace,
                biosample_id,
                collection_id=args.collection_id,
                data_element_ids=args.data_element_ids,
                next_page=args.next_page
            )
        except APIError as e:
            output('[red]请求失败：[/red]')
            output_json(e.result)
            sys.exit(1)
        output_json(
            result,
            cls=ModelEncoder
        )
