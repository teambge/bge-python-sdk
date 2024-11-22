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

    order = 2
    help = (
        '用户数据概览。'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--idcard',
            type=str,
            help='身份证号码。'
        )
        parser.add_argument(
            '--phone',
            type=str,
            help='手机号；提供了参数 phone，禁止再提供 biosample_id、project_id、'
                 'external_sample_id。'
        )
        parser.add_argument(
            '--biosample_id',
            type=str,
            help='BGE 样本编号；提供了参数 biosample_id，禁止再提供 phone、'
                 'project_id、external_sample_id。'
        )
        parser.add_argument(
            '--project_id',
            type=str,
            help='BGE 项目编号；提供了参数 project_id 必须提供 '
                 'external_sample_id，且 phone 和 biosample_id 必须为空。'
        )
        parser.add_argument(
            '--external_sample_id',
            type=str,
            help='外部样本编号；提供了参数 external_sample_id 必须提供 '
                 'project_id，且 phone 和 biosample_id 必须为空。'
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
        idcard = args.idcard
        phone = args.phone
        biosample_id = args.biosample_id
        project_id = args.project_id
        external_sample_id = args.external_sample_id
        config = read_config(project)
        if not access_token:
            access_token = config_get(config.get, token_section, 'access_token')
        endpoint = config_get(config.get, oauth2_section, 'endpoint')
        api = API(access_token, endpoint=endpoint, timeout=18.)
        try:
            result = api.get_overview(
                idcard=idcard,
                phone=phone,
                biosample_id=biosample_id,
                project_id=project_id,
                external_sample_id=external_sample_id,
            )
        except APIError as e:
            output('[red]请求失败：[/red]')
            output_json(e.result)
            sys.exit(1)
        output_json(
            result,
            cls=ModelEncoder
        )
