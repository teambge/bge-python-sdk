import argparse
import os
import six
import sys

from posixpath import join, exists
from six.moves import input

from bgesdk.management import constants
from bgesdk.management.utils import get_config_parser, config_get, \
                                    secure_str, get_config_path, confirm, \
                                    get_active_project


def init_parser(subparsers):
    config_p = subparsers.add_parser(
        'config',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        help='配置、新增、显示、删除 BGE 开放平台的 OAuth2 配置，仅支持客户端模式。'
    )
    config_p.set_defaults(method=config_project, parser=config_p)
    sub_ps = config_p.add_subparsers(help='新增、删除、显示 OAuth2 配置')
    add_p = sub_ps.add_parser(
        'add',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        help='新增 BGE 开放平台配置。'
    )
    add_p.add_argument(
        'project',
        help='全局配置项目名。'
    )
    add_p.set_defaults(method=add_project, parser=add_p)
    remove_p = sub_ps.add_parser(
        'remove',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        help='配置、显示、删除 BGE 开放平台的 OAuth2 全局配置，仅支持客户端模式。'
    )
    remove_p.add_argument(
        'project',
        help='全局配置项目名。'
    )
    remove_p.set_defaults(method=remove_project, parser=remove_p)
    show_p = sub_ps.add_parser(
        'show',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        help='打印显示全局配置信息。'
    )
    show_p.add_argument(
        'project',
        nargs='?',
        help='全局配置项目名。'
    )
    show_p.set_defaults(method=show_project, parser=show_p)


def config_project(args):
    project = get_active_project()
    print('当前正在配置 {}：\n'.format(project))
    config_path = get_config_path(project, check_exists=False)
    config_parser = get_config_parser(config_path)
    oauth2_section = constants.DEFAULT_OAUTH2_SECTION
    if oauth2_section not in config_parser.sections():
        config_parser.add_section(oauth2_section)
    for key, conf in constants.CLIENT_CREDENTIALS_CONFIGS:
        type_ = conf['type']
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
        secure = conf.get('secure')
        description = conf.get('description', '')
        value = saved_value or conf.get('default', '')
        if secure and value:
            value = secure_str(value)
        input_value = input(
            '？请输入{} {} [{}]：'.format(description, key, value))
        if input_value:
            config_parser.set(oauth2_section, key, input_value)
        elif saved_value is None:
            if conf.get('default') is not None:
                config_parser.set(oauth2_section, key, conf.get('default'))
            else:
                config_parser.set(oauth2_section, key, '')
    with open(config_path, 'w') as config_file:
        config_parser.write(config_file)
    print('')
    print('配置已保存至：{}'.format(config_path))


def add_project(args):
    project = args.project.lower()
    print('正在添加配置 {}：\n'.format(project))
    config_path = get_config_path(project, check_exists=False)
    if exists(config_path):
        print('配置 {} 已存在'.format(project))
        sys.exit(1)
    config_parser = get_config_parser(config_path)
    oauth2_section = constants.DEFAULT_OAUTH2_SECTION
    if oauth2_section not in config_parser.sections():
        config_parser.add_section(oauth2_section)
    for key, conf in constants.CLIENT_CREDENTIALS_CONFIGS:
        type_ = conf['type']
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
        secure = conf.get('secure')
        description = conf.get('description', '')
        value = saved_value or conf.get('default', '')
        if secure and value:
            value = secure_str(value)
        input_value = input(
            '？请输入{} {} [{}]：'.format(description, key, value))
        if input_value:
            config_parser.set(oauth2_section, key, input_value)
        elif saved_value is None:
            if conf.get('default') is not None:
                config_parser.set(oauth2_section, key, conf.get('default'))
            else:
                config_parser.set(oauth2_section, key, '')
    with open(config_path, 'w') as config_file:
        config_parser.write(config_file)
    print('')
    print('配置已保存至：{}'.format(config_path))


def remove_project(args):
    project = args.project.lower()
    activate_project = get_active_project()
    if activate_project == project:
        print('无法删除正在使用的配置，删除前请先使用 bge workon project 切换')
        sys.exit(1)
    config_path = get_config_path(project)
    if not confirm(prompt='确认删除配置项目 {}？'.format(project)):
        print('已取消删除')
        sys.exit(0)
    try:
        os.unlink(config_path)
    except (IOError, OSError):
        pass
    print('成功删除配置项目 {}'.format(project))


def show_project(args):
    project = args.project
    if not project:
        project = get_active_project()
    project = project.lower()
    config_path = get_config_path(project)
    print('配置文件：{}'.format(config_path))
    print('配置详情：')
    print('')
    with open(config_path, 'r') as config_file:
        print(config_file.read())
