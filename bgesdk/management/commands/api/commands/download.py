import posixpath
import sys

from bgesdk.client import API
from bgesdk.error import APIError
from bgesdk.management import constants
from bgesdk.management.command import BaseCommand
from bgesdk.management.utils import get_active_project, config_get, read_config
from bgesdk.version import __version__


DEFAULT_OAUTH2_SECTION = constants.DEFAULT_OAUTH2_SECTION
DEFAULT_TOKEN_SECTION = constants.DEFAULT_TOKEN_SECTION


class Command(BaseCommand):

    order = 11
    help='下载文件。'

    def add_arguments(self, parser):
        parser.add_argument(
            'object_name',
            help='OSS 对象名。'
        )
        parser.add_argument(
            '-m',
            '--mode',
            default='wb',
            choices=('w', 'wb'),
            type=str,
            help='下载文件打开模式。'
        )
        parser.add_argument(
            '-r',
            '--region',
            default='domestic',
            choices=('domestic', 'international'),
            type=str,
            help='区域。'
        )
        parser.add_argument(
            '-c',
            '--chunk_size',
            type=int,
            default=8192,
            help='下载块大小。'
        )
        parser.add_argument(
            '-e',
            '--expiration_time',
            type=int,
            default=600,
            help='下载地址过期时间。'
        )
        parser.add_argument(
            '-t',
            '--access_token',
            type=str,
            help='访问令牌，为空时默认使用 bge token 命令获取到的 access_token。'
        )

    def handler(self, args):
        access_token = args.access_token
        object_name = args.object_name
        mode = args.mode
        project = get_active_project()
        oauth2_section = DEFAULT_OAUTH2_SECTION
        token_section = DEFAULT_TOKEN_SECTION
        config = read_config(project)
        if not access_token:
            access_token = config_get(config.get, token_section, 'access_token')
        endpoint = config_get(config.get, oauth2_section, 'endpoint')
        api = API(access_token, endpoint=endpoint, timeout=18.)
        filename = posixpath.split(object_name)[1]
        if filename == '':
            print('下载失败，object_name 不是文件：{}'.format(repr(object_name)))
            sys.exit(1)
        if posixpath.exists(filename):
            basename, suffix = posixpath.splitext(filename)
            i = 1
            while True:
                new_basename = '{} ({})'.format(basename, i)
                filename = ''.join((new_basename, suffix))
                if not posixpath.exists(filename):
                    break
                i += 1
        try:
            with open(filename, mode) as fp:
                api.download(
                    object_name,
                    fp,
                    region=args.region,
                    expiration_time=args.expiration_time,
                    chunk_size=args.chunk_size
                )
        except APIError as e:
            print('\n\n请求失败：{}'.format(e))
            sys.exit(1)
        print('\n\n文件下载成功：{}'.format(filename))
