#-*- coding: utf-8 -*-

import json
import os
import pkgutil
import platform
import six
import sys

from os.path import expanduser
from posixpath import join, exists, abspath
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm
from rich.syntax import Syntax
from six.moves import configparser

from . import __path__, constants

if six.PY2:
    ConfigParser = configparser.SafeConfigParser
else:
    ConfigParser = configparser.ConfigParser

NoSectionError = configparser.NoSectionError
NoOptionError = configparser.NoOptionError

SYS_STR = platform.system().lower()

console = Console()


class CNConfirm(Confirm):

    validate_error_message = "[prompt.invalid]请输入 Y 或 N"


def get_home():
    return abspath('.')


def get_user_home():
    return expanduser("~")


def get_config_dir():
    user_home = get_user_home()
    bge_home = join(user_home, '.bge')
    if not exists(bge_home):
        os.makedirs(bge_home)
    return bge_home


def get_config_path(project, check_exists=True):
    config_dir = get_config_dir()
    config_path = join(config_dir, '{}.ini'.format(project))
    if not exists(config_path) and check_exists:
        output(
            '{} 不存在，请运行 bge config 或 bge config add 命令初始化项目配置'
                .format(project)
        )
        sys.exit(1)
    return config_path


def confirm(prompt=None):
    if prompt is None:
        prompt = '确认'
    return CNConfirm.ask(prompt)


def find_commands(commands_dir):
    """查找子命令列表"""
    return [
        name for _, name, is_pkg in pkgutil.iter_modules(
            [commands_dir])
    ]


def get_commands():
    """获取全部子命令"""
    return find_commands(join(__path__[0], 'commands'))


def get_active_path():
    config_dir = get_config_dir()
    return join(config_dir, 'activate_project')


def get_active_project():
    active_path = get_active_path()
    project = constants.DEFAULT_PROJECT
    if exists(active_path):
        with open(active_path, 'r') as fp:
            project = fp.read()
    else:
        with open(active_path, 'w') as fp:
            fp.write(project)
    return project


def generate_container_name(model_id):
    return '{}{}'.format(constants.MODEL_CONTAINER_PREFIX, model_id)


def config_get(method, section_name, key, default=None):
    try:
        return method(section_name, key)
    except (NoOptionError, NoSectionError):
        return default


def secure_str(s):
    if len(s) > 6:
        return s.replace(s[3:-3], '*' * 6)
    if len(s) >= 1:
        return s[0] + '*' * 6
    return s


def read_config(project):
    config_path = get_config_path(project)
    config = ConfigParser()
    config.read(config_path)
    return config


def get_config_parser(path):
    config_parser = ConfigParser()
    config_parser.read(path)
    return config_parser


def output_json(data, cls=None):
    syntax = Syntax(
        json.dumps(
            data,
            indent=4,
            sort_keys=True,
            ensure_ascii=False,
            cls=cls
        ),
        lexer='JSON',
        line_numbers=False,
        word_wrap=True,
        theme='monokai'
    )
    console.print(syntax)


def output_file(filepath, title='', subtitle=''):
    syntax = Syntax.from_path(
        filepath,
        line_numbers=True,
        word_wrap=True,
        theme='monokai'
    )
    panel = Panel(syntax, title=title, subtitle=subtitle)
    console.print(panel)


def output_panel(content, title='', subtitle='', lexer='python'):
    syntax = Syntax(
        content,
        lexer=lexer,
        line_numbers=True,
        word_wrap=True,
        theme='monokai'
    )
    panel = Panel(syntax, title=title, subtitle=subtitle)
    console.print(panel)


def output_syntax(content,
                  lexer='python',
                  line_numbers=True,
                  theme='monokai'):
    syntax = Syntax(
        content,
        lexer=lexer,
        line_numbers=line_numbers,
        word_wrap=True,
        theme=theme
    )
    console.print(syntax)


def output(*args, sep=' '):
    args = map(lambda x: str(x), args)
    content = '{}'.format(sep).join(args)
    console.print(content)


def get_sys_user():
    if SYS_STR == 'windows':
        user = '1000:1000'
    else:
        import pwd
        pwd_info = pwd.getpwuid(os.getuid())
        uid = pwd_info.pw_uid
        gid = pwd_info.pw_gid
        user = '{}:{}'.format(uid, gid)
    return user
