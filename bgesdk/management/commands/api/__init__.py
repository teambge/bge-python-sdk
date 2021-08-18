import argparse
import json
import posixpath
import sys

from importlib import import_module

from bgesdk.client import API
from bgesdk.error import APIError
from bgesdk.management import constants
from bgesdk.management.command import BaseCommand
from bgesdk.management.utils import (
    get_active_project, config_get, get_home, read_config, find_commands
)
from bgesdk.models import ModelEncoder
from bgesdk.version import __version__


DEFAULT_OAUTH2_SECTION = constants.DEFAULT_OAUTH2_SECTION
DEFAULT_TOKEN_SECTION = constants.DEFAULT_TOKEN_SECTION

# 用户信息
COMMAND_NAME = 'api'

class Command(BaseCommand):

    help='BGE 开放平台接口测试工具，可命名行调用部分常用接口。'

    def add_arguments(self, parser):
        api_subparsers = parser.add_subparsers(
            dest='subcommand',
            help='可选子命令。'
        )
        commands_dir = posixpath.join(__path__[0], 'commands')
        command_names = find_commands(commands_dir)
        sort_items = []
        for sub_command_name in command_names:
            module = import_module(
                'bgesdk.management.commands.{}.commands.{}'.format(
                    COMMAND_NAME, sub_command_name
                )
            )
            command_klass = getattr(module, 'Command', None)
            if command_klass and not issubclass(command_klass, BaseCommand):
                continue
            order = int(getattr(command_klass, 'order', 1))
            sort_items.append((order, sub_command_name, command_klass))
        sort_items.sort()
        for _, sub_command_name, command_klass in sort_items:
            command_klass(api_subparsers, sub_command_name)

    def handler(self, args):
        """打印 subparser 帮助信息"""
        parser = args.parser
        parser.print_help(sys.stderr)