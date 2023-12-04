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
    help = '获取套件外部编号对应表。'

    def add_arguments(self, parser):
        parser.add_argument(
            'project_id',
            type=str,
            help='项目编号。'
        )
        parser.add_argument(
            'biosample_site',
            type=str,
            help='采样位置。'
        )
        parser.add_argument(
            'external_ids',
            type=str,
            help='外部编号，逗号分割多个。'
        )

    def handler(self, args):
        access_token = args.access_token
        project_id = args.project_id
        biosample_site = args.biosample_site
        external_ids = args.external_ids
        project = get_active_project()
        oauth2_section = DEFAULT_OAUTH2_SECTION
        token_section = DEFAULT_TOKEN_SECTION
        config = read_config(project)
        if not access_token:
            access_token = config_get(config.get, token_section, 'access_token')
        endpoint = config_get(config.get, oauth2_section, 'endpoint')
        api = API(access_token, endpoint=endpoint, timeout=18.)
        try:
            result = api.externals(project_id, biosample_site, external_ids)
        except APIError as e:
            output('[red]请求失败：[/red]')
            output_json(e.result)
            sys.exit(1)
        output('[green]请求成功：[/green]')
        output_json(
            result,
            cls=ModelEncoder
        )
