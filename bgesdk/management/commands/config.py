import argparse
import os
import sys

from posixpath import exists, splitext
from rich.prompt import Prompt
from rich.table import Table

from bgesdk.management import constants
from bgesdk.management.command import BaseCommand
from bgesdk.management.utils import (
    config_get,
    confirm,
    console,
    get_active_project,
    get_config_dir,
    get_config_parser,
    get_config_path,
    output,
    output_file,
    secure_str,
)


class Command(BaseCommand):

    order = 1
    help = '配置、新增、显示、删除 BGE 开放平台的 OAuth2 配置，仅支持客户端模式。'
    project_help = '全局配置项目名。'

    def add_arguments(self, parser):
        try:
            sub_ps = parser.add_subparsers(
                help='新增、删除、显示 OAuth2 配置'
            )
        except TypeError:
            # required: Whether or not a subcommand must be provided, 
            # by default False (added in 3.7)
            sub_ps = parser.add_subparsers(
                help='新增、删除、显示 OAuth2 配置',
                required=False
            )
        add_p = sub_ps.add_parser(
            'add',
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            help='新增 BGE 开放平台配置。'
        )
        add_p.add_argument(
            'project',
            help=self.project_help
        )
        add_p.set_defaults(method=self.add_project, parser=add_p)
        remove_p = sub_ps.add_parser(
            'remove',
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            help='配置、显示、删除 BGE 开放平台的 OAuth2 全局配置，仅支持客户端模式。'
        )
        remove_p.add_argument(
            'project',
            help=self.project_help
        )
        remove_p.set_defaults(method=self.remove_project, parser=remove_p)
        show_p = sub_ps.add_parser(
            'show',
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            help='打印显示全局配置信息。'
        )
        show_p.add_argument(
            'project',
            nargs='?',
            help=self.project_help
        )
        show_p.set_defaults(method=self.show_project, parser=show_p)
        list_p = sub_ps.add_parser(
            'list',
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            help='显示全部已配置的项目。'
        )
        list_p.set_defaults(method=list_projects, parser=list_p)

    def handler(self, args):
        project = get_active_project()
        output('当前正在配置 {}：\n'.format(project))
        config_path = get_config_path(project, check_exists=False)
        self._new_project(config_path)

    def add_project(self, args):
        project = args.project.lower()
        config_path = get_config_path(project, check_exists=False)
        if exists(config_path):
            output('[red]配置 {} 已存在'.format(project))
            sys.exit(1)
        self._new_project(config_path)

    def _get_config_value(self, config_parser, key, type_):
        oauth2_section = constants.DEFAULT_OAUTH2_SECTION
        if 'str' == type_:
            saved_value = config_get(
                config_parser.get, oauth2_section, key)
        elif 'int' == type_:
            saved_value = config_get(
                config_parser.getint, oauth2_section, key)
        elif 'bool' == type_:
            saved_value = config_get(
                config_parser.getboolean, oauth2_section, key)
        else:
            raise ValueError('invalid type: {}'.format(type_))
        return saved_value

    def _new_project(self, config_path):
        config_parser = get_config_parser(config_path)
        oauth2_section = constants.DEFAULT_OAUTH2_SECTION
        if oauth2_section not in config_parser.sections():
            config_parser.add_section(oauth2_section)
        for key, conf in constants.CLIENT_CREDENTIALS_CONFIGS:
            type_ = conf['type']
            saved_value = self._get_config_value(config_parser, key, type_)
            secure = conf.get('secure')
            description = conf.get('description', '')
            value = saved_value or conf.get('default', '')
            show_value = value
            if secure and value:
                show_value = secure_str(value)
            input_value = Prompt.ask(
                '请输入{} {} ([bold cyan]{}[/bold cyan])'.format(
                    description, key, show_value
                ),
                show_default=False,
                default=value
            )
            if input_value:
                config_parser.set(oauth2_section, key, input_value)
            elif saved_value is None:
                if conf.get('default') is not None:
                    config_parser.set(
                        oauth2_section, key, conf.get('default'))
                else:
                    config_parser.set(oauth2_section, key, '')
        with open(config_path, 'w') as config_file:
            config_parser.write(config_file)
        output('')
        output('[green]配置已保存至：[/green]{}'.format(config_path))

    def remove_project(self, args):
        project = args.project.lower()
        activate_project = get_active_project()
        if activate_project == project:
            output(
                '[red]无法删除正在使用的配置，请先使用 bge workon 切换至其他项目[/red]'
            )
            sys.exit(1)
        config_path = get_config_path(project)
        if not confirm(prompt='确认删除配置项目 {}？'.format(project)):
            output('已取消删除')
            sys.exit(0)
        try:
            os.unlink(config_path)
        except (IOError, OSError):
            pass
        output('[green]成功删除配置项目[/green] {}'.format(project))

    def show_project(self, args):
        project = args.project
        if not project:
            project = get_active_project()
        project = project.lower()
        config_path = get_config_path(project)
        title = 'BGE 开放平台 Python SDK 配置文件'
        output_file(config_path, title=title, subtitle=config_path)


def list_projects(args=None):
    active_project = get_active_project()
    config_dir = get_config_dir()
    projects = []
    for filename in os.listdir(config_dir):
        name, ext = splitext(filename)
        if ext != '.ini':
            continue
        projects.append(name)
    projects.sort()
    table = Table(
        title='通过 bge workon <NAME> 切换生效配置',
        expand=True,
        show_header=True,
        header_style="magenta"
    )
    table.add_column(
        "项目",
        justify="center",
        style="dim"
    )
    table.add_column("使用中", justify="center")
    if active_project in projects:
        table.add_row(
            active_project,
            'Y',
            style="green",
        )
    for project in projects:
        if project == active_project:
            continue
        table.add_row(project, '-')
    console.print(table)
