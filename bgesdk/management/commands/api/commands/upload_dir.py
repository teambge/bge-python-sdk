import os
import posixpath
import sys

from posixpath import join, isfile

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
            'dirpath',
            type=str,
            help='要上传的文件夹。'
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
        files = []
        for filename in os.listdir(dirpath):
            filepath = join(dirpath, filename)
            if isfile(filepath):
                files.append(filepath)
                continue
        if not files:
            print('文件夹中没有可上传的文件')
            sys.exit(1)
        try:
            object_names = api.upload_dir(dirpath, cmk_id=cmk_id)
        except APIError as e:
            print('\n\n请求失败：{}'.format(e))
            sys.exit(1)
        print('\n文件上传成功：')
        for i, object_name in enumerate(object_names, 1):
            print('{}. {}'.format(i, object_name))
