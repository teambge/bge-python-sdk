
import argparse
import sys

from importlib import import_module

try:
    import readline
except ImportError:
    pass

from . import version
from .management.command import BaseCommand
from .management.utils import get_commands


def init_parser():
    parser = argparse.ArgumentParser(
        description=('BGE 开放平台 SDK 命令行工具提供了初始化模型脚手架、部署模型、'
                     '初始化模型文档配置文件、上传图片、部署模型文档等命令。'),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        '-V',
        '--version',
        action='version',
        help='显示当前 BGE 开放平台 Python SDK 版本号。',
        version='version {}'.format(version.__version__)
    )
    try:
        subparsers = parser.add_subparsers(
            dest='command',
            help='SDK 命令行工具可选子命令。'
        )
    except TypeError:
        # required: Whether or not a subcommand must be provided, 
        # by default False (added in 3.7)
        subparsers = parser.add_subparsers(
            dest='command',
            help='SDK 命令行工具可选子命令。',
            required=False
        )
    command_names = get_commands()
    sort_items = []
    for sub_command_name in command_names:
        module = import_module(
            'bgesdk.management.commands.{}'.format(sub_command_name)
        )
        command_klass = getattr(module, 'Command', None)
        if command_klass and not issubclass(command_klass, BaseCommand):
            continue
        order = int(getattr(command_klass, 'order', 1))
        sort_items.append((order, sub_command_name, command_klass))
    sort_items.sort()
    for _, sub_command_name, command_klass in sort_items:
        command_klass(subparsers, sub_command_name)
    return parser


def main():
    parser = init_parser()
    if len(sys.argv) < 2:
        parser.print_help(sys.stderr)
        sys.exit(1)
    input_args = sys.argv[1:]
    args = parser.parse_args(input_args)
    try:
        args.method(args)
    except KeyboardInterrupt:
        sys.exit(1)


if '__main__' == __name__:
    main()
