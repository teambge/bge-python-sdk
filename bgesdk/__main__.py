#!/usr/bin/env python

import argparse
import json
import os
try:
    import readline
except ImportError:
    pass
import stat
import sys
import tempfile
import zipfile

from os.path import expanduser
from posixpath import join, exists, abspath, isdir, relpath

from . import version
from .client import OAuth2, API
from .error import APIError
from .utils import major_version

if major_version == 2:
    import ConfigParser as configparser
    input = raw_input
else:
    import configparser

NoSectionError = configparser.NoSectionError
NoOptionError = configparser.NoOptionError

DEFAULT_MODEL_SECTION = 'Model'
DEFAULT_PROJECT = 'default'
DEFAULT_OAUTH2_SECTION = 'OAuth2'
DEFAULT_TOKEN_SECTION = 'Token'

main_py = '''\
import sys
sys.path.insert(0, './lib')

import json
import bgesdk

def handler(event, context):
    event = json.loads(event)
    biosample_id = event['biosample_id']
    params = event['params']
    return json.dumps({
        "model_code": 0,
        "model_msg": "success",
        "model_data": {
            'biosample_id': biosample_id,
            'params': params,
            'sdk': {
                'version': bgesdk.__version__
            },
        }
    })
'''


CLIENT_CREDENTIALS_CONFIGS = [
    ('client_id', {
        'type': 'str',
        'description': '客户端编号',
        'secure': True
    }),
    ('client_secret', {
        'type': 'str',
        'description': '客户端密钥',
        'secure': True
    }),
    ('endpoint', {
        'default': 'https://api.bge.genomics.cn',
        'type': 'str',
        'description': '访问域名'
    })
]

MODEL_CONFIGS = [
    ('model_id', {
        'type': 'str',
        'description': '解读模型编号'
    }),
    ('runtime', {
        'default': 'python3',
        'type': 'str',
        'description': '运行环境'
    }),
    ('memory_size', {
        'default': '128',
        'type': 'int',
        'description': '内存占用'
    }),
    ('timeout', {
        'default': '900',
        'type': 'int',
        'description': '模型运行超时时间'
    })
]


def get_user_home():
    return expanduser("~")


def get_home():
    return abspath('.')


def secure_str(s):
    if len(s) > 6:
        return s.replace(s[3:-3], '*' * 6)
    if len(s) >= 1:
        return s[0] + '*' * 6
    return s


def get_active_project():
    user_home = get_user_home()
    config_dir = join(user_home, '.bge')
    path = join(config_dir, 'project')
    project = DEFAULT_PROJECT
    if exists(path):
        with open(path, 'r') as fp:
            project = fp.read()
    return project


def get_model_config_path():
    home = get_home()
    config_dir = join(home, '.bge')
    if not exists(config_dir):
        print('请确认当前目录是否为 BGE 开放平台解读模型脚手架项目的根目录。')
        sys.exit(1)
    config_path = join(config_dir, 'model.ini')
    return config_path


def _get_config_path(project):
    user_home = get_user_home()
    config_dir = join(user_home, '.bge')
    if not exists(config_dir):
        os.makedirs(config_dir)
    config_path = join(config_dir, '{}.ini'.format(project))
    if not exists(config_path):
        print('项目 {} 不存在，请运行 bge config 命令初始化项目配置'.format(
            project))
        sys.exit(1)
    return config_path


def _read_config(project):
    config_path = _get_config_path(project)
    config = configparser.ConfigParser()
    config.read(config_path)
    return config


def init_parser():
    home = get_home()
    parser = argparse.ArgumentParser(
        description=('BGE 开放平台 SDK 命令行工具提供了初始化模型脚手架、部署模型、'
                     '初始化模型文档配置文件、上传图片、部署模型文档等命令。'),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        '-v',
        '--version',
        action='version',
        help='显示当前 BGE 开放平台 Python SDK 版本号。',
        version='version {}'.format(version.__version__)
    )
    subparsers = parser.add_subparsers(
        dest='command',
        help='SDK 命令行工具可选子命令。'
    )
    workon_p = subparsers.add_parser(
        'workon',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        help='激活某项目配置，其他命令均使用已激活的项目配置作为全局配置。'
    )
    workon_p.add_argument(
        '-p',
        '--project',
        default=DEFAULT_PROJECT,
        help='自定义项目名称保存全局配置，其他命令默认读取正在生效的项目配置。'
    )
    workon_p.set_defaults(method=_write_project, parser=workon_p)
    config_p = subparsers.add_parser(
        'config',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        help='显示、配置 BGE 开放平台的 OAuth2 全局配置，仅支持客户端模式。'
    )
    config_p.add_argument(
        '-p',
        '--print',
        default=False,
        action='store_true',
        help='打印显示当前生效的项目全局配置。'
    )
    config_p.set_defaults(method=_write_oauth2_config, parser=config_p)
    token_p = subparsers.add_parser(
        'token',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        help='获取、保存访问令牌。'
    )
    token_p.add_argument(
        '-t',
        '--timeout',
        default=18,
        type=int,
        help='请求超时时间，可覆盖默认配置。'
    )
    token_p.add_argument(
        '-s',
        '--save',
        default=True,
        action='store_true',
        help='保存令牌到全局配置。'
    )
    token_p.set_defaults(method=_get_token, parser=token_p)
    model_p = subparsers.add_parser(
        'model',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        help='模型初始化脚手架、配置、部署等相关命令。'
    )
    model_p.set_defaults(method=_print_subparser_help, parser=model_p)
    model_subparsers = model_p.add_subparsers(
        dest='subcommand',
        help='可选子命令。'
    )
    # 初始化脚手架命令
    init_p = model_subparsers.add_parser(
        'init',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        help='初始化一个新的模型开发脚手架项目。'
    )
    init_p.add_argument(
        'scaffold_name',
        type=str,
        help='脚手架名字。'
    )
    init_p.add_argument(
        '-f',
        '--force',
        default=False,
        action='store_true',
        help='强制初始化。'
    )
    init_p.add_argument(
        '--home',
        type=str,
        default=home,
        help='脚手架项目生成的父级目录，默认为当前目录。'
    )
    init_p.set_defaults(method=_init_scaffold, parser=init_p)
    config_p = model_subparsers.add_parser(
        'config',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        help='配置模型。'
    )
    config_p.add_argument(
        '-p',
        '--print',
        default=False,
        action='store_true',
        help='打印显示当前模型脚手架的配置。'
    )
    config_p.set_defaults(method=_write_model_config, parser=config_p)
    run_p = model_subparsers.add_parser(
        'run',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        help='调用线上稳定版模型。'
    )
    run_p.add_argument(
        '-d',
        '--draft',
        default=False,
        action="store_true",
        help='调用最新灰度版本模型。'
    )
    run_p.add_argument(
        '-b',
        '--biosample_id',
        help='生物样品编号'
    )
    run_p.add_argument(
        '-t',
        '--timeout',
        default=18,
        type=int,
        help='请求超时时间，可覆盖默认配置。'
    )
    group = run_p.add_mutually_exclusive_group()
    group.add_argument(
        '-a',
        '--args',
        nargs=2,
        action='append',
        help='参数对，示例：--args f1 v1 --args f2 v2'
    )
    group.add_argument(
        '-f',
        '--file',
        help='JSON 格式参数文件，内容示例：{ "f1": "v1", "f2": "v2" }。'
    )
    run_p.set_defaults(method=_run_model, parser=run_p)
    # 部署子命令
    deploy_p = model_subparsers.add_parser(
        'deploy',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        help='部署灰度版本模型。'
    )
    deploy_p.add_argument(
        '-t',
        '--timeout',
        default=900,
        type=int,
        help='请求超时时间，可覆盖默认配置。'
    )
    deploy_p.add_argument(
        '-s',
        '--source_file',
        type=str,
        help='.zip 格式模型源文件。'
    )
    deploy_p.set_defaults(method=_deploy_model, parser=deploy_p)
    publish_p = model_subparsers.add_parser(
        'publish',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        help='发布最新部署的灰度版本模型为稳定版。'
    )
    publish_p.add_argument(
        '-m',
        '--message',
        type=str,
        help='模型发布说明。'
    )
    publish_p.add_argument(
        '-t',
        '--timeout',
        default=18,
        type=int,
        help='请求超时时间，可覆盖默认配置。'
    )
    publish_p.set_defaults(method=_publish_model, parser=publish_p)
    rollback_p = model_subparsers.add_parser(
        'rollback',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        help='模型回滚至某个稳定版本。'
    )
    rollback_p.add_argument(
        '-v',
        '--version',
        type=str,
        help='要回滚的模型版本。'
    )
    rollback_p.add_argument(
        '-m',
        '--message',
        type=str,
        help='模型回滚说明。'
    )
    rollback_p.add_argument(
        '-t',
        '--timeout',
        default=18,
        type=int,
        help='请求超时时间，可覆盖默认配置。'
    )
    rollback_p.set_defaults(method=_rollback_model, parser=rollback_p)
    return parser


def _write_project(args):
    project = args.project.lower()
    user_home = get_user_home()
    config_dir = join(user_home, '.bge')
    if not exists(config_dir):
        os.makedirs(config_dir)
    path = join(config_dir, 'project')
    with open(path, 'w') as fp:
        fp.write(project)
    print('已激活 {} 的项目配置'.format(project))


def config_get(method, section_name, key, default=None):
    try:
        return method(section_name, key)
    except (NoOptionError, NoSectionError):
        return default


def _write_oauth2_config(args):
    if getattr(args, 'print'):
        return _read_project(args)
    project = get_active_project()
    print('当前生效项目配置为 {}。'.format(project))
    user_home = get_user_home()
    config_dir = join(user_home, '.bge')
    if not exists(config_dir):
        os.makedirs(config_dir)
    print('OAuth2 配置：\n')
    config_path = join(config_dir, '{}.ini'.format(project))
    config = configparser.ConfigParser()
    config.read(config_path)
    section_name = DEFAULT_OAUTH2_SECTION
    if section_name not in config.sections():
        config.add_section(section_name)
    for key, conf in CLIENT_CREDENTIALS_CONFIGS:
        type_ = conf['type']
        if 'str' == type_:
            saved_value = config_get(config.get, section_name, key)
        elif 'int' == type_:
            saved_value = config_get(config.getint, section_name, key)
        elif 'bool' == type_:
            saved_value = config_get(config.getboolean, section_name, key)
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
            config.set(section_name, key, input_value)
        elif saved_value is None:
            if conf.get('default') is not None:
                config.set(section_name, key, conf.get('default'))
            else:
                config.set(section_name, key, '')
    with open(config_path, 'w') as config_file:
        config.write(config_file)
    print('')
    print('配置已保存至：{}'.format(config_path))


def _read_project(args):
    project = get_active_project()
    config_path = _get_config_path(project)
    print('生效项目：{}'.format(project))
    print('配置文件：{}'.format(config_path))
    print('配置详情：')
    print('')
    with open(config_path, 'r') as config_file:
        print(config_file.read())


def _get_token(args):
    timeout = args.timeout
    project = get_active_project()
    config = _read_config(project)
    section_name = DEFAULT_OAUTH2_SECTION
    client_id = config_get(config.get, section_name, 'client_id')
    client_secret = config_get(config.get, section_name, 'client_secret')
    endpoint = config_get(config.get, section_name, 'endpoint')
    oauth2 = OAuth2(
        client_id, client_secret, endpoint=endpoint, timeout=timeout)
    try:
        token_result = oauth2.get_credentials_token()
    except APIError as e:
        print('令牌获取出错: {}'.format(e))
        sys.exit(1)
    if args.save:
        _write_token_config(project, token_result)
    print('令牌内容如下：')
    print('')
    for key in ['access_token', 'token_type', 'expires_in', 'scope']:
        print('{} = {}'.format(key, token_result[key]))


def _print_subparser_help(args):
    """打印 subparser 帮助信息"""
    parser = args.parser
    parser.print_help(sys.stderr)


def _init_scaffold(args):
    scaffold_name = args.scaffold_name
    home = args.home
    force = args.force
    if home is None:
        home = get_home()
    scaffold_dir = join(home, scaffold_name)
    if not force:
        if not exists(home):
            print('错误！无法找到 home 目录 %s。' % home)
            return
        if exists(scaffold_dir):
            print('错误！脚手架 %s 已经存在。' % scaffold_dir)
            return
    else:
        if not exists(scaffold_dir):
            os.makedirs(scaffold_dir)
    bge_dir = join(scaffold_dir, '.bge')
    lib_dir = join(scaffold_dir, 'lib')
    for dir_ in [scaffold_dir, bge_dir, lib_dir]:
        sys.stdout.write('创建 {} ... '.format(dir_))
        sys.stdout.flush()
        if not exists(dir_):
            os.makedirs(dir_)
            print('完成')
        elif not isdir(dir_):
            print('失败')
            print('失败！{} 存在但不是目录。'.format(dir_))
            return
        else:
            print('已存在')
    sys.stdout.write('正在安装 bge-python-sdk ... ')
    os.system('pip install --no-deps bge-python-sdk -t {}'.format(lib_dir))
    print('bgesdk 已经安装在目录 {} 中'.format(lib_dir))
    script_name = 'main.py'
    script_path = join(scaffold_dir, script_name)
    with open(script_path, 'wb') as file_out:
        file_out.write(main_py.encode())
    st = os.stat(script_path)
    os.chmod(script_path, st.st_mode | stat.S_IEXEC)
    print('成功初始化')


def _read_model_project(args):
    config_path = get_model_config_path()
    print('配置文件：{}'.format(config_path))
    print('配置详情：')
    print('')
    with open(config_path, 'r') as config_file:
        print(config_file.read())


def _write_model_config(args):
    """写入模型配置"""
    if getattr(args, 'print'):
        return _read_model_project(args)
    config_path = get_model_config_path()
    config = configparser.ConfigParser()
    config.read(config_path)
    section_name = DEFAULT_MODEL_SECTION
    if section_name not in config.sections():
        config.add_section(section_name)
    print('请输入解读模型部署配置：\n')
    for key, conf in MODEL_CONFIGS:
        type_ = conf['type']
        if 'str' == type_:
            saved_value = config_get(config.get, section_name, key)
        elif 'int' == type_:
            saved_value = config_get(config.getint, section_name, key)
        elif 'bool' == type_:
            saved_value = config_get(config.getboolean, section_name, key)
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
            config.set(section_name, key, input_value)
        elif saved_value is None:
            if conf.get('default') is not None:
                config.set(section_name, key, conf.get('default'))
            else:
                config.set(section_name, key, '')
    with open(config_path, 'w') as config_file:
        config.write(config_file)
    print('')
    print('解读模型配置已保存至：{}'.format(config_path))


def _deploy_model(args):
    """部署模型"""
    timeout = args.timeout
    home = get_home()
    project = get_active_project()
    config_path = get_model_config_path()
    config = configparser.ConfigParser()
    config.read(config_path)
    section_name = DEFAULT_MODEL_SECTION
    model_id = config_get(config.get, section_name, 'model_id')
    params = {}
    params['runtime'] = config_get(config.get, section_name, 'runtime')
    params['memory_size'] = config_get(
        config.getint, section_name, 'memory_size')
    params['timeout'] = config_get(config.getint, section_name, 'timeout')
    oauth2_section = DEFAULT_OAUTH2_SECTION
    token_section = DEFAULT_TOKEN_SECTION
    config = _read_config(project)
    access_token = config_get(config.get, token_section, 'access_token')
    endpoint = config_get(config.get, oauth2_section, 'endpoint')
    api = API(access_token, endpoint=endpoint, timeout=timeout)
    with tempfile.NamedTemporaryFile(suffix='.zip') as tmp:
        with zipfile.ZipFile(tmp.name, 'w', zipfile.ZIP_STORED) as zf:
            _zip_codedir(home, zf)
        tmp.flush()
        tmp.seek(0)
        try:
            api.deploy_model(model_id, source_file=tmp.name, **params)
        except APIError as e:
            print(e)
            sys.exit(1)
    print('模型 {} 灰度部署成功。'.format(model_id))


def _zip_codedir(path, ziph):
    for root, dirs, files in os.walk(path):
        for file in files:
            filepath = join(root, file)
            zip_relpath = relpath(filepath, path)
            ziph.write(filepath, zip_relpath)


def _publish_model(args):
    """发布模型到稳定版"""
    timeout = args.timeout
    message = args.message
    home = get_home()
    project = get_active_project()
    config_path = get_model_config_path()
    config = configparser.ConfigParser()
    config.read(config_path)
    section_name = DEFAULT_MODEL_SECTION
    model_id = config_get(config.get, section_name, 'model_id')
    oauth2_section = DEFAULT_OAUTH2_SECTION
    token_section = DEFAULT_TOKEN_SECTION
    config = _read_config(project)
    access_token = config_get(config.get, token_section, 'access_token')
    endpoint = config_get(config.get, oauth2_section, 'endpoint')
    api = API(access_token, endpoint=endpoint, timeout=timeout)
    try:
        result = api.publish_model(model_id, message)
    except APIError as e:
        print(e)
        sys.exit(1)
    print('模型 {} 稳定版已成功发布。\n版本号：{}。'.format(
        model_id, result['version']))


def _rollback_model(args):
    timeout = args.timeout
    version = args.version
    message = args.message
    home = get_home()
    project = get_active_project()
    config_path = get_model_config_path()
    config = configparser.ConfigParser()
    config.read(config_path)
    section_name = DEFAULT_MODEL_SECTION
    model_id = config_get(config.get, section_name, 'model_id')
    oauth2_section = DEFAULT_OAUTH2_SECTION
    token_section = DEFAULT_TOKEN_SECTION
    config = _read_config(project)
    access_token = config_get(config.get, token_section, 'access_token')
    endpoint = config_get(config.get, oauth2_section, 'endpoint')
    api = API(access_token, endpoint=endpoint, timeout=timeout)
    try:
        result = api.rollback_model(model_id, version, message)
    except APIError as e:
        print(e)
        sys.exit(1)
    print('模型 {} 稳定版、灰度版已成功回滚至版本 {}。\n新版本号：{}。'.format(
        model_id, version, result['version']))


def _run_model(args):
    params = {}
    if args.file:
        if not exists(args.file):
            print('文件不存在：{}'.format(args.file))
            sys.exit(1)
        if isdir(args.file):
            print('存在文件夹：{}'.format(args.file))
            sys.exit(1)
    elif args.args:
        params = dict(args.args)
    draft = args.draft
    timeout = args.timeout
    home = get_home()
    project = get_active_project()
    config_path = get_model_config_path()
    config = configparser.ConfigParser()
    config.read(config_path)
    section_name = DEFAULT_MODEL_SECTION
    model_id = config_get(config.get, section_name, 'model_id')
    oauth2_section = DEFAULT_OAUTH2_SECTION
    token_section = DEFAULT_TOKEN_SECTION
    config = _read_config(project)
    access_token = config_get(config.get, token_section, 'access_token')
    endpoint = config_get(config.get, oauth2_section, 'endpoint')
    api = API(access_token, endpoint=endpoint, timeout=timeout)
    try:
        if draft is True:
            result = api.invoke_draft_model(model_id, **params)
        else:
            result = api.invoke_model(model_id, **params)
    except APIError as e:
        print(e)
        sys.exit(1)
    print(json.dumps(result.json(), indent=4, ensure_ascii=False))


def _write_token_config(project, token_result):
    user_home = get_user_home()
    config_dir = join(user_home, '.bge')
    if not exists(config_dir):
        os.makedirs(config_dir)
    config_path = join(config_dir, '{}.ini'.format(project))
    config = configparser.ConfigParser()
    config.read(config_path)
    section_name = DEFAULT_TOKEN_SECTION
    if section_name not in config.sections():
        config.add_section(section_name)
    config.set(section_name, 'access_token', token_result['access_token'])
    config.set(section_name, 'token_type', token_result['token_type'])
    config.set(section_name, 'expires_in', str(token_result['expires_in']))
    config.set(section_name, 'scope', token_result['scope'])
    with open(config_path, 'w') as config_file:
        config.write(config_file)
    print('令牌已保存至：{}'.format(config_path))


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


if __name__ == '__main__':
    main()