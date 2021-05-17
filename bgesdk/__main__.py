
import argparse
import sys

from importlib import import_module

try:
    import readline
except ImportError:
    pass

from . import version
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
    subparsers = parser.add_subparsers(
        dest='command',
        help='SDK 命令行工具可选子命令。'
    )
    command_names = ['config', 'workon', 'token', 'model']
    for command_name in get_commands():
        if command_name in command_names:
            continue
        command_names.append(command_name)
    for command_name in command_names:
        module = import_module(
            'bgesdk.management.commands.{}'.format(command_name))
        module.init_parser(subparsers)
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
