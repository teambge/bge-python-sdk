import os
import sys


from rich.table import Table
from posixpath import join, isfile

from bgesdk.client import API
from bgesdk.error import APIError
from bgesdk.management import constants
from bgesdk.management.command import BaseCommand
from bgesdk.management.utils import (
    config_get,
    console,
    get_active_project,
    output,
    output_json,
    read_config
)


DEFAULT_OAUTH2_SECTION = constants.DEFAULT_OAUTH2_SECTION
DEFAULT_TOKEN_SECTION = constants.DEFAULT_TOKEN_SECTION


class Command(BaseCommand):

    order = 12
    help = '上传目录下文件（不递归上传子目录中文件）。'

    def add_arguments(self, parser):
        parser.add_argument(
            'dirpath',
            type=str,
            help='要上传的文件夹。'
        )
        parser.add_argument(
            '--part_size',
            default=100,
            type=int,
            help='单个分片大小, 单位 MB。'
        )
        parser.add_argument(
            '--multipart_threshold',
            default=50,
            type=int,
            help='上传数据大于或等于该值时分片上传, 单位 MB。'
        )
        parser.add_argument(
            '--multipart_num_threads',
            default=constants.MULTIPART_NUM_THREADS,
            help='分片上传缺省线程数。'
        )
        parser.add_argument(
            '-i',
            '--cmk_id',
            help='阿里云 KMS 服务密钥 ID，提供时代表使用加密方式上传文件。'
        )
        parser.add_argument(
            '-r',
            '--region_id',
            help='阿里云 OSS 区域编号，默认 oss-cn-shenzhen。'
        )
        parser.add_argument(
            '--internal',
            action="store_true",
            help='是否使用内部 VPC 域名。'
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
        dirpath = args.dirpath
        cmk_id = args.cmk_id
        part_size = args.part_size
        multipart_threshold = args.multipart_threshold
        region_id = args.region_id
        internal = args.internal
        files = []
        for filename in os.listdir(dirpath):
            filepath = join(dirpath, filename)
            if isfile(filepath):
                files.append(filepath)
        if not files:
            output('[red]文件夹中没有可上传的文件[/red]')
            sys.exit(1)
        message = '正在上传目录 {}'.format(dirpath)
        with console.status(message, spinner='earth'):
            try:
                object_names = api.upload_dir(
                    dirpath,
                    part_size=part_size * 1024 * 1024,
                    multipart_threshold=multipart_threshold * 1024 * 1024,
                    multipart_num_threads=args.multipart_num_threads,
                    cmk_id=cmk_id,
                    region_id=region_id,
                    internal=internal,
                )
            except APIError as e:
                output('[red]请求失败：[/red]')
                output_json(e.result)
                sys.exit(1)
            output('[green]文件上传成功：[/green]')
            table = Table(
                title="文件列表",
                expand=True,
                show_header=True,
                header_style="magenta"
            )
            table.add_column("序号", style="cyan", no_wrap=True)
            table.add_column("存储位置", style="magenta", overflow='fold')
            for i, object_name in enumerate(object_names, 1):
                table.add_row(str(i), object_name)
            console.print(table)
