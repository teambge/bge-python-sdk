#-*- coding: utf-8 -*-

import json
import logging
import os
import pkgutil
import six
import sys

from os.path import expanduser
from posixpath import join, exists, abspath
from six.moves import configparser, http_client

from . import __path__, constants

if six.PY2:
    ConfigParser = configparser.SafeConfigParser
else:
    ConfigParser = configparser.ConfigParser

NoSectionError = configparser.NoSectionError
NoOptionError = configparser.NoOptionError
HTTPConnection = http_client.HTTPConnection


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
        print('{} 不存在，请运行 bge config 或 bge config add 命令初始化项目配置'
              .format(project))
        sys.exit(1)
    return config_path


def confirm(prompt=None):
    if prompt is None:
        prompt = '确认'
    prompt = '%s\n[%s]/%s: ' % (prompt, 'Y', 'n')
    while True:
        ans = input(prompt)
        if ans not in ['y', 'Y', 'n', 'N']:
            print('请输入 Y 或 n')
            continue
        if ans == 'y' or ans == 'Y':
            return True
        if ans == 'n' or ans == 'N':
            return False


def find_commands(commands_dir):
    """查找子命令列表"""
    return [
        name for _, name, is_pkg in pkgutil.iter_modules(
            [commands_dir]) if not is_pkg
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