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

    order = 16
    help = (
        '下载科服文件。通过当前接口，从科技服务的文件服务中下载文件并上传至 BGE 平台的 '
        'OSS 服务中。'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            'account',
            type=str,
            help='华大科技账号。'
        )
        parser.add_argument(
            'password',
            type=str,
            help='华大科技密码。'
        )
        parser.add_argument(
            'project_no',
            type=str,
            help='华大科技项目编号。'
        )
        parser.add_argument(
            'biosample_cnt',
            type=int,
            help='样本数，必须大于或等于 0；接口将通过计算下载文件中样本名（参考参数 '
                 'sample_names 解释）去重后与接口提供参数对比，数量无误才会下载文件。'
        )
        parser.add_argument(
            '-e',
            '--included_filename_exts',
            type=str,
            help='下载的文件后缀名可选范围：.txt、.xls、.pdf、.tar.gz、.tar.gz、'
                 '.md5、.fq.gz，默认包含全部可选后缀，多个后缀用英文逗号分割，'
                 '如: .txt,.pdf。'
        )
        parser.add_argument(
            '-n',
            '--sample_names',
            type=str,
            help='样品名，将从过滤后将要下载的文件中，使用样本名过滤所有 .fq.gz 的文'
                 '件；样品名为要下载文件中文件名为 *_1.fq.gz 或者 *_2.fq.gz 的文件,'
                 ' 如 E-V20000006992A_1.fq.gz 文件的样品名即为 E-V20000006992A，'
                 '多个样本名用逗号分割。'
        )
        parser.add_argument(
            '-a',
            '--action',
            type=str,
            help='动作名，可选值：restart，如果接口调用包含参数 action=restart，接'
                 '口将使用接口调用的参数重新启动一个新的任务（如果相同参数的任务已经在'
                 '运行，将无法重新启动任务，且接口将报错）。'
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
        account = args.account
        password = args.password
        project_no = args.project_no
        biosample_cnt = args.biosample_cnt
        included_filename_exts = args.included_filename_exts
        sample_names = args.sample_names
        action = args.action
        config = read_config(project)
        if not access_token:
            access_token = config_get(config.get, token_section, 'access_token')
        endpoint = config_get(config.get, oauth2_section, 'endpoint')
        api = API(access_token, endpoint=endpoint, timeout=18.)
        try:
            result = api.ferry_to_oss(
                account,
                password,
                project_no,
                biosample_cnt,
                included_filename_exts=included_filename_exts,
                sample_names=sample_names,
                action=action,
            )
        except APIError as e:
            output('[red]请求失败：[/red]')
            output_json(e.result)
            sys.exit(1)
        output_json(
            result,
            cls=ModelEncoder
        )
