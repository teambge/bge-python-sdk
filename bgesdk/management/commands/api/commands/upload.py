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

    order = 10
    help='上传文件。'

    def add_arguments(self, parser):
        parser.add_argument(
            'filepath',
            type=str,
            help='要上传的文件路径。'
        )
        parser.add_argument(
            '-f',
            '--filename',
            help='服务器存储使用的文件名，不提供时默认使用上传文件的名字。'
        )
        parser.add_argument(
            '-i',
            '--cmk_id',
            help='阿里云 KMS 服务密钥 ID，提供时代表使用加密方式上传文件。'
        )
        parser.add_argument(
            '-t',
            '--access_token',
            type=str,
            help='访问令牌，为空时默认使用 bge token 命令获取到的 access_token。'
        )

    def handler(self, args):
        access_token = args.access_token
        filepath = args.filepath
        project = get_active_project()
        oauth2_section = DEFAULT_OAUTH2_SECTION
        token_section = DEFAULT_TOKEN_SECTION
        config = read_config(project)
        if not access_token:
            access_token = config_get(config.get, token_section, 'access_token')
        endpoint = config_get(config.get, oauth2_section, 'endpoint')
        api = API(access_token, endpoint=endpoint, timeout=18.)
        if not posixpath.isfile(filepath):
            print('只能上传文件')
            sys.exit(1)
        filename = args.filename
        cmk_id = args.cmk_id
        if not filename:
            filename = posixpath.split(filepath)[1]
        try:
            with open(filepath, 'rb') as fp:
                object_name = api.upload(filename, fp, cmk_id=cmk_id)
        except APIError as e:
            print('\n\n请求失败：{}'.format(e))
            sys.exit(1)
        print('\n\n文件上传成功：{}'.format(object_name))
