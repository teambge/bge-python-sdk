import json
import sys

from bgesdk.client import API
from bgesdk.error import APIError
from bgesdk.management import constants
from bgesdk.management.command import BaseCommand
from bgesdk.management.utils import get_active_project, config_get, read_config
from bgesdk.models import ModelEncoder
from bgesdk.version import __version__


DEFAULT_OAUTH2_SECTION = constants.DEFAULT_OAUTH2_SECTION
DEFAULT_TOKEN_SECTION = constants.DEFAULT_TOKEN_SECTION


class Command(BaseCommand):

    order = 5
    help = '获取微生物功能丰度。'

    def add_arguments(self, parser):
        parser.add_argument(
            'biosample_id',
            type=str,
            help='生物样品编号。'
        )
        parser.add_argument(
            'catalog',
            type=str,
            choices=[
                'go', 'ko', 'eggnog', 'pfam', 'kegg-pwy', 'kegg-mdl', 'level4ec',
                'metacyc-rxn', 'metacyc-pwy'
            ],
            help='目录标签。'
        )
        parser.add_argument(
            '--ids',
            type=str,
            help='BGE物种功能编号，多个值以逗号隔开。'
        )
        parser.add_argument(
            '--pretty',
            default=False,
            action='store_true',
            help='打印可读性高的 JSON 字符串。'
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
        pretty = args.pretty
        access_token = args.access_token
        biosample_id = args.biosample_id
        catalog = args.catalog
        project = get_active_project()
        oauth2_section = DEFAULT_OAUTH2_SECTION
        token_section = DEFAULT_TOKEN_SECTION
        config = read_config(project)
        if not access_token:
            access_token = config_get(config.get, token_section, 'access_token')
        endpoint = config_get(config.get, oauth2_section, 'endpoint')
        api = API(access_token, endpoint=endpoint, timeout=18.)
        try:
            result = api.get_func_abundance(
                biosample_id,
                catalog,
                ids=args.ids,
                next_page=args.next_page,
                limit=args.limit
            )
        except APIError as e:
            print('请求失败：{}'.format(e))
            sys.exit(1)
        if pretty:
            result = json.dumps(
                result, ensure_ascii=False, indent=4, cls=ModelEncoder
            )
        else:
            result = json.dumps(result, ensure_ascii=False, cls=ModelEncoder)
        print('请求成功，返回值：')
        print(result)
