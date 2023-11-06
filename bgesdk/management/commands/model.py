import argparse
import csv
import docker
import fnmatch
import json
import os
import python_minifier
import qprompt
import re
import shutil
import stat
import sys
import tempfile
import zipfile

from datetime import datetime
from posixpath import join, exists, isdir, relpath, split, abspath
from rich.prompt import Confirm
from time import sleep
from traceback import format_exc
from uuid import uuid4

from bgesdk.client import API
from bgesdk.error import APIError
from bgesdk.management import constants
from bgesdk.management.command import BaseCommand
from bgesdk.management.utils import (
    config_get,
    confirm,
    console,
    get_active_project,
    get_config_parser,
    get_home,
    get_sys_user,
    generate_container_name,
    generate_next_path,
    output,
    output_json,
    output_syntax,
    read_config,
    SYS_STR
)
from bgesdk.utils import human_byte


DEFAULT_OAUTH2_SECTION = constants.DEFAULT_OAUTH2_SECTION
DEFAULT_TOKEN_SECTION = constants.DEFAULT_TOKEN_SECTION
DEFAULT_MODEL_SECTION = constants.DEFAULT_MODEL_SECTION
DEFAULT_MODEL_TIMEOUT = constants.DEFAULT_MODEL_TIMEOUT
TEST_SERVER_ENDPOINT = constants.TEST_SERVER_ENDPOINT
TEST_SERVER_PORT = constants.TEST_SERVER_PORT

model_id_match = re.compile(r'^[a-zA-Z0-9]+$').match

MAIN_PY = '''\
import json
import logging

def handler(event, context):
    logging.debug(event)
    event = json.loads(event)
    access_token = event["access_token"]
    params = event["params"]
    return json.dumps({
        "model_code": 0,
        "model_msg": "success",
        "model_data": {
            "access_token": access_token,
            "params": params,
        }
    })
'''

MODEL_CONFIG_TEMPLATE = '''\
[Model]
model_id =
cpu = 0.05
memory_size = 128
disk_size = 512
timeout = 900
runtime = python3.10
'''

BGEIGNORE_TEMPLATE = '''\
# Unix filename patterns
#
#   *    matches everything
#   ?    matches any single character
#   seq  matches any character in seq
#   !seq matches any character not in seq


# Ignore folder .bge/

.bge/*
lib/*.pyc

'''

BGEMINIFY_TEMPLATE = '''\
# Unix filename patterns
#
#   *    matches everything
#   ?    matches any single character
#   seq  matches any character in seq
#   !seq matches any character not in seq

# Warning: it only can minfiy .py files.

# Minify all files in lib/
# lib/*

# Unminify all python files in lib/
# !lib/*.py

# Minify main.py and unminify lib/*

!lib/*
main.py

'''

RUNTIMES = {
    'python2.7': 'teambge/runtime-python2.7:latest',
    'python3': 'teambge/runtime-python3.6:latest',
    'python3.9': 'teambge/runtime-python3.9:latest',
    'python3.10': 'teambge/runtime-python3.10:latest',
}
WORKDIR = '/code'

RUNTIME_CHOICES = ['python3.10', 'python3.9', 'python3', 'python2.7']
MEMORY_SIZE_CHOICES = [
    128, 256, 512, 1024, 2048, 4096, 8192, 16384, 32768,
]  # MB
CPU_CHOICES = [
    0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.5, 0.75, 1, 1.5, 2, 4,
    6, 8, 12, 16,
]  # vCPU 核心
DISK_SIZE_CHOICES = [512, 10240]  # MB
MIN_TIMEOUT = 1
MAX_TIMEOUT = 900

DEFAULT_MODEL_ID = ''
DEFAULT_RUNTIME = 'python3.10'
DEFAULT_CPU = 0.05
DEFAULT_MEMORY_SIZE = 128
DEFAULT_DISK_SIZE = 512
DEFAULT_TIMEOUT = 900
DEFAULT_MIRROR_MODELS = ''

TOTAL_PROGRESS = {
    'FAILURE' : '任务执行失败',
    'PENDING' : '任务等待中',
    'RECEIVED': '任务已接收',
    'RETRY'   : '任务将被重试',
    'REVOKED' : '任务取消',
    'STARTED' : '任务已开始',
    'SUCCESS' : '任务执行成功'
}

BGE_IGNORE_FILE = '.bgeignore'
BGE_MINIFY_FILE = '.bgeminify'

CREATE_MESSAGE = '创建 {} ...'
INSTALL_DOCKER_MESSAGE = '\
请先安装 docker，参考 https://docs.docker.com/engine/install/'
WAIT_MESSAGE = '已等待 {}s，{}'
TASK_ERROR_MESSAGE = '已等待 {}s，任务状态异常：{}'

WHICH_DOCKER = 'which docker'
WHEREIS_DOCKER = 'whereis docker'

ZIP_COMPRESSION = zipfile.ZIP_DEFLATED


class TestServerPortAction(argparse.Action):

    def __call__(self, parser, namespace, values, option_string=None):
        if not getattr(namespace, 'test', None) and values:
            parser.error(
                'argument -p/--port: only allowed with argument -t/--test'
            )
        else:
            namespace.port = values


class TestServerLicenseKeyAction(argparse.Action):

    def __call__(self, parser, namespace, values, option_string=None):
        if not getattr(namespace, 'test', None) and values:
            parser.error(
                '--license-key only allowed with argument -t/--test'
            )
        else:
            namespace.license_key = values


class Command(BaseCommand):

    order = 5
    help='模型初始化脚手架、配置、部署等相关命令。'

    def add_arguments(self, parser):
        home = get_home()
        try:
            model_subparsers = parser.add_subparsers(
                dest='subcommand',
                help='可选子命令。'
            )
        except TypeError:
            # required: Whether or not a subcommand must be provided, 
            # by default False (added in 3.7)
            model_subparsers = parser.add_subparsers(
                dest='subcommand',
                help='可选子命令。',
                required=False
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
            '--home',
            type=str,
            default=home,
            help='脚手架项目生成的父级目录，默认为当前目录。'
        )
        init_p.set_defaults(method=self.init_scaffold, parser=init_p)

        # 模型配置
        config_p = model_subparsers.add_parser(
            'config',
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            help='配置模型。'
        )
        config_p.add_argument(
            '-s',
            '--show',
            default=False,
            action='store_true',
            help='打印显示当前模型脚手架的配置。'
        )
        config_p.set_defaults(method=self.config_model, parser=config_p)

        # 安装 Python 依赖包
        install_p = model_subparsers.add_parser(
            'install',
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            help='安装 Python 依赖包到 ./lib 目录。'
        )
        install_p.add_argument(
            'package_name',
            nargs="+",
            type=str,
            help='要安装的 Python 软件包，如 numpy 或 numpy==v1.19.5。'
        )
        install_p.add_argument(
            '-r',
            '--requirements',
            nargs=1,
            type=str,
            help='要安装的 Python 软件包依赖文件。'
        )
        install_p.add_argument(
            '-U',
            '--upgrade',
            default=False,
            action='store_true',
            help='是否升级依赖包，同 pip install -U。'
        )
        install_p.add_argument(
            '--no-deps',
            default=False,
            action='store_true',
            help='不安装 Python 包的其他依赖包，同 pip install --no-deps。'
        )
        install_p.add_argument(
            '--force-reinstall',
            default=False,
            action='store_true',
            help='是否强制重新安装依赖包，同 pip install --force-reinstall。'
        )
        install_p.set_defaults(method=self.install_deps, parser=install_p)

        start_p = model_subparsers.add_parser(
            'start',
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            help='启动本地 HTTP 测试服务器。'
        )
        start_p.add_argument(
            '-p',
            '--port',
            default=TEST_SERVER_PORT,
            type=int,
            choices=range(1,65536),
            metavar="[1-65535]",
            help='服务器监听端口。'
        )
        start_p.add_argument(
            '-U',
            '--update-docker',
            default=False,
            action='store_true',
            help='更新 BGE 模型依赖的 docker 镜像。'
        )
        start_p.set_defaults(method=self.start_model, parser=start_p)

        new_license_p = model_subparsers.add_parser(
            'new_license',
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            help='获取模型运行许可凭证。'
        )
        new_license_p.add_argument(
            '-m',
            '--model_id',
            type=str,
            help='模型编号。'
        )
        new_license_p.add_argument(
            '-e',
            '--expires',
            type=int,
            default=3600,
            help='许可证有效期，单位：秒。'
        )
        req_group = new_license_p.add_mutually_exclusive_group()
        req_group.add_argument(
            '-a',
            '--args',
            nargs=2,
            action='append',
            help='参数对，示例：--args f1 v1 --args f2 v2。'
        )
        req_group.add_argument(
            '-f',
            '--file',
            help='参数文件，每行为 JSON 字典，示例：{ "f1": "v1", "f2": "v2" }。'
        )
        new_license_p.add_argument(
            '-c',
            '--csv',
            required=False,
            default='new_license.csv',
            help='输出的 CSV 文件路径。'
        )
        new_license_p.set_defaults(
            method=self.new_model_license,
            parser=new_license_p
        )

        # 测试模型许可证（本命令仅支持调用 bge model start 启动的服务器接口）。
        run_license_p = model_subparsers.add_parser(
            'run_license',
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            help='许可证模式调用模型（仅支持调用 bge model start 启动的服务器接口）。'
        )
        run_license_p.add_argument(
            'license_file',
            help='运行许可证集合文件。'
        )
        run_license_p.add_argument(
            '--csv',
            required=False,
            default='run_license.csv',
            help='运行许可证集合文件。'
        )
        run_license_p.add_argument(
            '-p',
            '--port',
            default=TEST_SERVER_PORT,
            type=int,
            choices=range(1,65536),
            metavar="[1-65535]",
            help='服务器监听端口。'
        )
        run_license_p.set_defaults(
            method=self.run_license,
            parser=run_license_p
        )

        expfs_p = model_subparsers.add_parser(
            'expfs',
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            help='扩展模型文件集。'
        )
        expfs_p.set_defaults(method=self.upload_model_expfs, parser=expfs_p)


        # 打包模型
        package_p = model_subparsers.add_parser(
            'package',
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            help='打包模型代码到 zip 文件。'
        )
        package_p.add_argument(
            '-t',
            '--target',
            default=None,
            help='输出目录。'
        )
        package_p.set_defaults(method=self.package_model, parser=package_p)


        # 部署子命令
        deploy_p = model_subparsers.add_parser(
            'deploy',
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            help='部署灰度版本模型。'
        )
        group = deploy_p.add_mutually_exclusive_group()
        group.add_argument(
            '-i',
            '--ignore-source',
            default=False,
            action="store_true",
            help='部署时不包含模型源代码。'
        )
        group.add_argument(
            '--with-mirrors',
            default=False,
            action="store_true",
            help='部署时同时部署代码到镜像模型中。'
        )
        deploy_p.set_defaults(method=self.deploy_model, parser=deploy_p)

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
            '--with-mirrors',
            default=False,
            action="store_true",
            help='发布模型时同时发布镜像模型中。'
        )
        publish_p.set_defaults(method=self.publish_model, parser=publish_p)

        # 运行模型子命令
        run_p = model_subparsers.add_parser(
            'run',
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            help='调用线上稳定版模型。'
        )
        group = run_p.add_mutually_exclusive_group()
        draft_a = group.add_argument(
            '-d',
            '--draft',
            default=False,
            action="store_true",
            help='调用最新灰度版本模型。'
        )
        group.add_argument(
            '-t',
            '--test',
            default=False,
            action="store_true",
            help='调用本地启动的测试服务器运行模型。'
        )
        group_1 = run_p.add_mutually_exclusive_group()
        license_key_a = group_1.add_argument(
            '--license-key',
            action=TestServerLicenseKeyAction,
            required=False,
            help='运行许可证。'
        )
        # 禁止 -license-key 与 -d 参数同时提供
        group_1._group_actions.append(draft_a)
        group_2 = run_p.add_mutually_exclusive_group()
        group_2.add_argument(
            '-p',
            '--port',
            default=TEST_SERVER_PORT,
            type=int,
            action=TestServerPortAction,
            choices=range(1,65536),
            metavar="[1-65535]",
            help='服务器监听端口。'
        )
        # 禁止 -p 与 -d 参数同时提供
        group_2._group_actions.append(draft_a)
        group_3 = run_p.add_mutually_exclusive_group()
        group_3.add_argument(
            '-m',
            '--model-id',
            type=str,
            help='其他模型编号，该参数将覆盖配置文件中的 model_id 调用接口。'
        )
        # 禁止 --license-key 与 --model-id 参数同时提供
        group_3._group_actions.append(license_key_a)
        group = run_p.add_mutually_exclusive_group()
        group.add_argument(
            '-a',
            '--args',
            nargs=2,
            action='append',
            help='参数对，示例：--args f1 v1 --args f2 v2。'
        )
        group.add_argument(
            '-f',
            '--file',
            help='JSON 格式参数文件，内容示例：{ "f1": "v1", "f2": "v2" }。'
        )
        run_p.add_argument(
            '--no-pretty',
            default=False,
            action="store_true",
            help='取消美化输出 JSON 结果。'
        )
        run_p.add_argument(
            '-o',
            '--output',
            type=str,
            help='输出返回结果到文件的路径。'
        )
        run_p.set_defaults(method=self.run_model, parser=run_p)

        # 回滚子命令
        rollback_p = model_subparsers.add_parser(
            'rollback',
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            help='模型回滚至某个稳定版本。'
        )
        rollback_p.add_argument(
            '-m',
            '--model_id',
            type=str,
            help='模型编号。'
        )
        rollback_p.add_argument(
            '-v',
            '--version',
            type=str,
            help='要回滚的模型版本。'
        )
        rollback_p.set_defaults(method=self.rollback_model, parser=rollback_p)

        # 回滚版本列表子命令
        versions_p = model_subparsers.add_parser(
            'versions',
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            help='模型发布版本列表。'
        )
        versions_p.add_argument(
            '-m',
            '--model_id',
            type=str,
            help='模型编号。'
        )
        versions_p.add_argument(
            '-l',
            '--limit',
            default=5,
            type=int,
            help='每页返回数量。'
        )
        versions_p.add_argument(
            '-p',
            '--next_page',
            type=int,
            help='下一页。'
        )
        versions_p.set_defaults(method=self.model_versions, parser=versions_p)

        # 清空临时文件
        clear_p = model_subparsers.add_parser(
            'clear',
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            help='清空部署模型时生成的打包临时文件。'
        )
        clear_p.set_defaults(method=self.clear_model, parser=clear_p)

    def handler(self, args):
        """打印 subparser 帮助信息"""
        parser = args.parser
        parser.print_help(sys.stderr)

    def init_scaffold(self, args):
        scaffold_name = args.scaffold_name
        home = args.home
        if home is None:
            home = get_home()
        scaffold_dir = join(home, scaffold_name)
        if exists(scaffold_dir):
            output('[red]错误！{} 已存在[/red]'.format(scaffold_dir))
            sys.exit(1)
        if not exists(home):
            output('[red]错误！无法找到 home 目录 {}。[/red]'.format(home))
            sys.exit(1)
        model_id, runtime, cpu, memory_size, disk_size, timeout, \
            mirror_models = self._config_model()
        os.makedirs(scaffold_dir)
        bge_dir = join(scaffold_dir, '.bge')
        lib_dir = join(scaffold_dir, 'lib')
        for dir_ in [scaffold_dir, bge_dir, lib_dir]:
            output(CREATE_MESSAGE.format(dir_))
            if not exists(dir_):
                os.makedirs(dir_)
                output('[green]完成[/green]')
            elif not isdir(dir_):
                output('[red]失败！{} 存在但不是目录。[/red]'.format(dir_))
                sys.exit(1)
            else:
                output('[red]已存在[/red]')
        model_config_path = join(scaffold_dir, 'model.ini')
        output(CREATE_MESSAGE.format(model_config_path))
        if not exists(model_config_path):
            open(model_config_path, 'w').write(MODEL_CONFIG_TEMPLATE)
        # 模型源码打包忽略规则文件
        ignore_path = join(scaffold_dir, BGE_IGNORE_FILE)
        output(CREATE_MESSAGE.format(ignore_path))
        if not exists(ignore_path):
            open(ignore_path, 'w').write(BGEIGNORE_TEMPLATE)
        # 模型源码打包混淆规则文件
        minify_path = join(scaffold_dir, BGE_MINIFY_FILE)
        output(CREATE_MESSAGE.format(minify_path))
        if not exists(minify_path):
            open(minify_path, 'w').write(BGEMINIFY_TEMPLATE)
        script_name = 'main.py'
        script_path = join(scaffold_dir, script_name)
        with open(script_path, 'wb') as file_out:
            file_out.write(MAIN_PY.encode())
        st = os.stat(script_path)
        os.chmod(script_path, st.st_mode | stat.S_IEXEC)
        self._save_model_config(
            model_id, runtime, cpu, memory_size, disk_size, timeout,
            mirror_models, home=scaffold_dir)
        if confirm('是否安装 bge-python-sdk？'):
            os.chdir(scaffold_dir)
            self._install_sdk()
        output('[green]成功创建模型项目脚手架[/green]')

    def config_model(self, args):
        if args.show:
            return self._read_model_project(args)
        config_path = self.get_model_config_path()
        config_parser = get_config_parser(config_path)
        model_id, runtime, cpu, memory_size, disk_size, timeout, \
            mirror_models = self._config_model(config_parser)
        self._save_model_config(
            model_id, runtime, cpu, memory_size, disk_size, timeout,
            mirror_models)

    def _input_model_id(self, default=''):
        prompt = '请输入解读模型编号'
        while True:
            model_id = qprompt.ask_str(prompt, dft=default)
            if not model_id:
                if default:
                    model_id = default
                    break
                output('[red]必须提供模型编号。[/red]')
            else:
                if model_id_match(model_id):
                    break
                output('[red]模型编号只能包含数字、大小写字母。[/red]')
        return model_id

    def _input_runtime(self, default=None):
        try:
            index = RUNTIME_CHOICES.index(default)
        except IndexError:
            index = 0
        prompt = '请选择运行环境 [{}]'.format(default)
        input_prompt = "请选择"
        return qprompt.enum_menu(RUNTIME_CHOICES).show(
            header=prompt,
            dft=index + 1,
            returns="desc",
            msg=input_prompt
        )

    def _input_cpu(self, default=None):
        try:
            index = CPU_CHOICES.index(default)
        except IndexError:
            index = 0
        prompt = '请选择 vCPU 核心数 [{}]'.format(default)
        input_prompt = "请选择"
        return qprompt.enum_menu(CPU_CHOICES).show(
            header=prompt,
            dft=index + 1,
            returns="desc",
            msg=input_prompt
        )

    def _input_memory_size(self, default=None):
        try:
            index = MEMORY_SIZE_CHOICES.index(default)
        except IndexError:
            index = 0
        prompt = '请选择内存占用（MB）[{}]'.format(default)
        input_prompt = "请选择"
        return qprompt.enum_menu(MEMORY_SIZE_CHOICES).show(
            header=prompt,
            dft=index + 1,
            returns="desc",
            msg=input_prompt
        )

    def _input_disk_size(self, default=None):
        try:
            index = DISK_SIZE_CHOICES.index(default)
        except IndexError:
            index = 0
        prompt = '请选择磁盘占用（MB） [{}]'.format(default)
        input_prompt = "请选择"
        return qprompt.enum_menu(DISK_SIZE_CHOICES).show(
            header=prompt,
            dft=index + 1,
            returns="desc",
            msg=input_prompt
        )

    def _input_timeout(self, default=None):
        prompt = '请输入模型运行超时时间，类型为整数'
        while True:
            timeout = qprompt.ask_int(msg=prompt, dft=default)
            if (MIN_TIMEOUT and timeout < MIN_TIMEOUT) \
                    or (MAX_TIMEOUT and timeout > MAX_TIMEOUT):
                output(
                    '超出范围 [{},{}]，请重新输入'.format(
                        MIN_TIMEOUT or '', MAX_TIMEOUT or ''
                    )
                )
                continue
            break
        if not timeout:
            timeout = default
        return timeout

    def _input_mirror_models(self, default=None):
        prompt = '请输入镜像模型编号，逗号分割多个（可选）'
        while True:
            mirror_models = qprompt.ask_str(prompt, dft=default)
            if not mirror_models:
                break
            # 逗号分割多个编号
            for model_id in mirror_models.split(','):
                if model_id_match(model_id):
                    continue
                output('[red]模型编号只能包含数字、大小写字母。[/red]')
                break
            else:
                break
        return mirror_models

    def _config_model(self, config=None):
        output('开始配置解读模型...')
        model_id = runtime = cpu = memory_size = disk_size = timeout \
            = mirror_models = None
        if config is not None:
            section_name = DEFAULT_MODEL_SECTION
            model_id = config_get(config.get, section_name, 'model_id')
            runtime = config_get(config.get, section_name, 'runtime')
            cpu = config_get(config.getfloat, section_name, 'cpu')
            memory_size = config_get(config.getint, section_name, 'memory_size')
            disk_size = config_get(config.getint, section_name, 'disk_size')
            timeout = config_get(config.getint, section_name, 'timeout')
            mirror_models = config_get(config.get, section_name, 'mirror_models')
        default_model_id = model_id or DEFAULT_MODEL_ID
        default_runtime = runtime or DEFAULT_RUNTIME
        default_cpu = cpu or DEFAULT_CPU
        default_memory_size = memory_size or DEFAULT_MEMORY_SIZE
        default_disk_size = disk_size or DEFAULT_DISK_SIZE
        default_timeout = timeout or DEFAULT_TIMEOUT
        default_mirror_models = mirror_models or DEFAULT_MIRROR_MODELS
        model_id = self._input_model_id(default=default_model_id)
        runtime = self._input_runtime(default=default_runtime)
        while True:
            cpu = self._input_cpu(default=default_cpu)
            memory_size = self._input_memory_size(default=default_memory_size)
            ratio = (memory_size / 1024) / cpu
            if ratio < 1 or ratio > 4:
                ratio = '%.2f' % ratio
                output(f'[red]vCPU 大小（核）与内存大小（GB）的比值必须在 1:1 到 1:4 之间，'
                       f'当前为 {ratio}，请重新选择[/red]')
                qprompt.pause()
                continue
            break
        disk_size = self._input_disk_size(default=default_disk_size)
        timeout = self._input_timeout(default=default_timeout)
        mirror_models = self._input_mirror_models(default=default_mirror_models)
        return model_id, runtime, float(cpu), \
            int(memory_size), int(disk_size), int(timeout), mirror_models

    def _save_model_config(self, model_id, runtime, cpu, memory_size, disk_size,
                           timeout, mirror_models, home=None):
        # save
        config_path = self.get_model_config_path(home=home)
        config = get_config_parser(config_path)
        section_name = DEFAULT_MODEL_SECTION
        if section_name not in config.sections():
            config.add_section(section_name)
        output('开始保存解读模型配置...')
        output('配置文件 {}'.format(config_path))
        config.set(section_name, 'model_id', model_id)
        config.set(section_name, 'runtime', runtime)
        config.set(section_name, 'cpu', str(cpu))
        config.set(section_name, 'memory_size', str(memory_size))
        config.set(section_name, 'disk_size', str(disk_size))
        config.set(section_name, 'timeout', str(timeout))
        config.set(section_name, 'mirror_models', mirror_models)
        with open(config_path, 'w') as config_file:
            config.write(config_file)
        output('')
        output('[green]解读模型配置已保存至[/green] {}'.format(config_path))

    def _install_sdk(self):
        output("正在安装 bge-python-sdk")
        config_path = self.get_model_config_path()
        config = get_config_parser(config_path)
        section_name = DEFAULT_MODEL_SECTION
        model_id = config_get(config.get, section_name, 'model_id')
        runtime = config_get(config.get, section_name, 'runtime')
        client = self._get_docker_client()
        command = (
            'pip install --cache-dir /tmp/.cache/ --no-deps '
            'bge-python-sdk pimento requests_toolbelt -t /code/lib'
        )
        image_name = RUNTIMES[runtime]
        self._get_or_pull_image(client, image_name)
        output('开始安装模型依赖包...')
        command = ('sh -c "{}"').format(command)
        container_name = generate_container_name(model_id)
        self._force_remove_container(client, container_name)
        self._run_by_container(
            client,
            image_name,
            command,
            container_name
        )
        output('[green]安装完成[/green]')

    def upload_model_expfs(self, args):
        home = get_home()
        project = get_active_project()
        config_path = self.get_model_config_path()
        config = get_config_parser(config_path)
        section_name = DEFAULT_MODEL_SECTION
        model_id = config_get(config.get, section_name, 'model_id')
        oauth2_section = DEFAULT_OAUTH2_SECTION
        token_section = DEFAULT_TOKEN_SECTION
        config = read_config(project)
        access_token = config_get(config.get, token_section, 'access_token')
        endpoint = config_get(config.get, oauth2_section, 'endpoint')
        api = API(
            access_token, endpoint=endpoint, timeout=DEFAULT_MODEL_TIMEOUT)
        try:
            result = api.upload_model_expfs(model_id, 'uploadtest.zip')
        except APIError as e:
            output('[red]上传模型扩展集失败：[/red]')
            output_json(e.result)
            sys.exit(1)
        task_id = result.task_id
        output('上传模型扩展集任务：{}'.format(task_id))
        task_path = join(home, '.bge', 'expfs.task_id')
        with open(task_path, 'w') as f:
            f.write(task_id)
        output('上传模型扩展集任务返回结果：')
        progress = self._wait_model_task(api, task_id, task_path)
        if 'SUCCESS' == progress:
            output('[green]模型 {} 上传模型扩展集成功。'.format(model_id))
        elif 'FAILURE' == progress:
            output('[red]模型 {} 上传模型扩展集失败。'.format(model_id))
        elif 'REVOKED' == progress:
            output('[white]模型 {} 上传模型扩展集任务已被撤销。'.format(model_id))

    def package_model(self, args):
        target = args.target
        self._package_model(target=target)


    def _package_model(self, zip_filename=None, target=None):
        home = get_home()
        config_path = self.get_model_config_path()
        config = get_config_parser(config_path)
        section_name = DEFAULT_MODEL_SECTION
        model_id = config_get(config.get, section_name, 'model_id')
        timestr = datetime.now().strftime('%Y%m%d%H%M%S%f')
        randstr = uuid4().hex
        if zip_filename is None:
            zip_filename = '{}.{}.{}.zip'.format(model_id, timestr, randstr)
        ignore_path = join(home, BGE_IGNORE_FILE)
        if not exists(ignore_path):
            output(
                '未发现 .bgeignore 文件，初始化 {} ...'.format(ignore_path)
            )
            open(ignore_path, 'w').write(BGEIGNORE_TEMPLATE)
        minify_path = join(home, BGE_MINIFY_FILE)
        if not exists(minify_path):
            output(
                '未发现 .bgeminify 文件，初始化 {} ...'.format(minify_path)
            )
            open(minify_path, 'w').write(BGEMINIFY_TEMPLATE)
        output('开始打包模型源码...')
        zip_tmpdir = target
        if target is None:
            zip_tmpdir = join(home, '.bge', 'tmp')
            if not exists(zip_tmpdir):
                os.makedirs(zip_tmpdir)
        with tempfile.NamedTemporaryFile(
                suffix='.zip',
                prefix='model-',
                dir=zip_tmpdir,
                delete=False) as tmp:
            with zipfile.ZipFile(tmp.name, 'w', ZIP_COMPRESSION) as zf:
                self._zip_codedir(home, zf)
            tmp.flush()
            tmp.seek(0, 2)
            size = tmp.tell()
            tmp.seek(0)
            human_size = human_byte(size)
            output('打包成功：{}'.format(tmp.name))
            output('文件大小：{}'.format(human_size))
        return tmp.name

    def deploy_model(self, args):
        """部署模型"""
        ignore_source = args.ignore_source
        with_mirrors = args.with_mirrors
        project = get_active_project()
        config_path = self.get_model_config_path()
        config = get_config_parser(config_path)
        section_name = DEFAULT_MODEL_SECTION
        model_id = config_get(config.get, section_name, 'model_id')
        mirror_models = config_get(config.get, section_name, 'mirror_models')
        params = {}
        params['runtime'] = config_get(config.get, section_name, 'runtime')
        params['cpu'] = config_get(config.getfloat, section_name, 'cpu')
        params['memory_size'] = config_get(
            config.getint, section_name, 'memory_size')
        params['disk_size'] = config_get(
            config.getint, section_name, 'disk_size')
        params['timeout'] = config_get(
            config.getint, section_name, 'timeout')
        oauth2_section = DEFAULT_OAUTH2_SECTION
        token_section = DEFAULT_TOKEN_SECTION
        config = read_config(project)
        access_token = config_get(config.get, token_section, 'access_token')
        endpoint = config_get(config.get, oauth2_section, 'endpoint')
        api = API(
            access_token, endpoint=endpoint, timeout=DEFAULT_MODEL_TIMEOUT)
        object_name = None
        if not ignore_source:
            model_zip_path = self._package_model()
            zip_filename = split(model_zip_path)[1]
            with open(model_zip_path, 'rb') as fp:
                fp.seek(0, 2)
                size = fp.tell()
                fp.seek(0)
                human_size = human_byte(size)
                if size > 500 * 1024 * 1024:
                    output(
                        '打包后 zip 文件大小为 {}，最大限制 500MB'.format(
                            human_size
                        )
                    )
                    exit(1)
                output('开始上传模型源码...')
                try:
                    object_name = api.upload(zip_filename, fp)
                except APIError as e:
                    output('[red]上传模型源码失败：[/red]')
                    output_json(e.result)
                    sys.exit(1)
                output('[green]上传成功[green]')
        try:
            self._deploy_model_code(api, model_id, object_name, **params)
        except Exception as e:
            output(f'[red] 上传部署模型代码到模型 {model_id} 失败...[/red]')
            output_syntax(str(e))
        if not with_mirrors or not mirror_models:
            return
        if not Confirm.ask(
                f'是否上传部署模型源码到镜像模型 {mirror_models} 中？'):
            output('[yellow]已取消...[/yellow]')
            return
        output('\n\n')
        for idx, model_id in enumerate(mirror_models.split(','), start=1):
            output(f'[{idx}] 开始上传模型源码到镜像模型 {model_id}...')
            try:
                self._deploy_model_code(api, model_id, object_name, **params)
            except Exception as e:
                output(f'[red] 上传部署模型代码到模型 {model_id} 失败...[/red]')
                output_syntax(str(e))
            output('\n\n')

    def _deploy_model_code(self, api, model_id, object_name, **params):
        with console.status('模型部署中...', spinner='earth'):
            try:
                result = api.deploy_model(
                    model_id, object_name=object_name, **params)
            except APIError as e:
                output('[red]部署模型失败：[/red]')
                output_json(e.result)
                return
        home = get_home()
        task_id = result.task_id
        output('模型部署任务：{}'.format(task_id))
        task_path = join(home, '.bge', 'task_id')
        with open(task_path, 'w') as f:
            f.write(task_id)
        output('模型部署任务返回结果：')
        progress = self._wait_model_task(api, task_id, task_path)
        if 'SUCCESS' == progress:
            output('[green]模型 {} 灰度部署成功。'.format(model_id))
        elif 'FAILURE' == progress:
            output('[red]模型 {} 灰度部署失败。任务结果：{}'.format(model_id, result))
        elif 'REVOKED' == progress:
            output('[white]模型 {} 灰度部署任务已被撤销。'.format(model_id))

    def _wait_model_task(self, api, task_id, task_path):
        seconds = 0
        while True:
            result = api.task(task_id)
            progress = result.progress
            if progress not in TOTAL_PROGRESS:
                output(TASK_ERROR_MESSAGE.format(seconds, progress))
                try:
                    os.unlink(task_path)
                except (IOError, OSError):
                    pass
                sys.exit(1)
            output(WAIT_MESSAGE.format(seconds, TOTAL_PROGRESS[progress]))
            if progress in ('SUCCESS', 'FAILURE', 'REVOKED'):
                break
            sleep(1)
            seconds += 1
        try:
            os.unlink(task_path)
        except (IOError, OSError):
            pass
        return progress

    def _zip_codedir(self, home, ziph):
        home = home.rstrip('/')
        total_files = {}
        zip_relpaths = set()
        for root, _, files in os.walk(home):
            for file in files:
                filepath = join(root, file)
                zip_relpath = relpath(filepath, home)
                zip_relpaths.add(zip_relpath)
                total_files[zip_relpath] = filepath
        src_zip_relpaths = zip_relpaths.copy()
        ignore_patterns = self.get_ignore_patterns(home)
        for ignore_pattern in ignore_patterns:
            if ignore_pattern.startswith('!'):
                ignore_pattern = ignore_pattern[1:]
                zip_relpaths.update(
                    fnmatch.filter(src_zip_relpaths, ignore_pattern))
                continue
            zip_relpaths -= set(
                fnmatch.filter(zip_relpaths, ignore_pattern))
        minify_relpaths = set()
        minify_patterns = self.get_minify_patterns(home)
        for minify_pattern in minify_patterns:
            if minify_pattern.startswith('!'):
                minify_pattern = minify_pattern[1:]
                minify_relpaths -= set(
                    fnmatch.filter(minify_relpaths, minify_pattern))
                continue
            minify_relpaths.update(
                fnmatch.filter(src_zip_relpaths, minify_pattern))
        # 仅支持混淆 .py 文件
        minify_relpaths = fnmatch.filter(minify_relpaths, '*.py')
        with console.status('正在打包模型源码...', spinner='dots'):
            for zip_relpath in sorted(zip_relpaths):
                filepath = total_files[zip_relpath]
                if zip_relpath in minify_relpaths:
                    continue
                zipinfo = zipfile.ZipInfo(zip_relpath)
                zipinfo.external_attr = 0o755 << 16
                zipinfo.compress_type = ZIP_COMPRESSION
                with open(filepath, 'rb') as f:
                    ziph.writestr(zipinfo, f.read())
                output('\t{}'.format(zip_relpath))
            for zip_relpath in sorted(minify_relpaths):
                filepath = total_files[zip_relpath]
                with open(filepath, 'r') as fp:
                    content = fp.read()
                content = python_minifier.minify(content)
                zipinfo = zipfile.ZipInfo(zip_relpath)
                zipinfo.external_attr = 0o755 << 16
                zipinfo.compress_type = ZIP_COMPRESSION
                ziph.writestr(zipinfo, content)
                output('\t{} [green]MINIFIED[/green]'.format(zip_relpath))

    def get_ignore_patterns(self, home):
        patterns = []
        home = home.rstrip('/')
        path = join(home, BGE_IGNORE_FILE)
        with open(path) as fp:
            for _ in fp.readlines():
                _ = _.strip()
                while _.startswith('/'):
                    _ = _[1:]
                if _.startswith('#') or not _:
                    continue
                patterns.append(_)
        return patterns

    def get_minify_patterns(self, home):
        patterns = []
        home = home.rstrip('/')
        path = join(home, BGE_MINIFY_FILE)
        with open(path) as fp:
            for _ in fp.readlines():
                _ = _.strip()
                while _.startswith('/'):
                    _ = _[1:]
                if _.startswith('#') or not _:
                    continue
                patterns.append(_)
        return patterns

    def publish_model(self, args):
        """发布模型到稳定版"""
        message = args.message
        with_mirrors = args.with_mirrors
        project = get_active_project()
        config_path = self.get_model_config_path()
        config = get_config_parser(config_path)
        section_name = DEFAULT_MODEL_SECTION
        model_id = config_get(config.get, section_name, 'model_id')
        mirror_models = config_get(config.get, section_name, 'mirror_models')
        oauth2_section = DEFAULT_OAUTH2_SECTION
        token_section = DEFAULT_TOKEN_SECTION
        config = read_config(project)
        access_token = config_get(config.get, token_section, 'access_token')
        endpoint = config_get(config.get, oauth2_section, 'endpoint')
        api = API(
            access_token, endpoint=endpoint, timeout=DEFAULT_MODEL_TIMEOUT)
        try:
            self._publish_model(api, model_id, message)
        except Exception as e:
            output(f'[red] 发布模型 {model_id} 失败...[/red]')
            output_syntax(str(e))
        if not with_mirrors or not mirror_models:
            return
        if not Confirm.ask(f'是否同时发布镜像模型 {mirror_models} ？'):
            output('[yellow]已取消...[/yellow]')
            return
        output('\n\n')
        for idx, model_id in enumerate(mirror_models.split(','), start=1):
            output(f'[{idx}] 开始发布镜像模型 {model_id}...')
            try:
                self._publish_model(api, model_id, message)
            except Exception as e:
                output(f'[red] 发布模型 {model_id} 失败...[/red]')
                output_syntax(str(e))
            output('\n\n')

    def _publish_model(self, api, model_id, message):
        try:
            result = api.publish_model(model_id, message)
        except APIError as e:
            output('[red]模型发布失败：[/red]')
            output_json(e.result)
        else:
            output('[green]模型 {} 稳定版已成功发布。\n版本号：{}。[/green]'.format(
                model_id, result['version']))

    def rollback_model(self, args):
        version = args.version
        model_id = args.model_id
        home = get_home()
        project = get_active_project()
        config_path = self.get_model_config_path()
        config = get_config_parser(config_path)
        section_name = DEFAULT_MODEL_SECTION
        if not model_id:
            model_id = config_get(config.get, section_name, 'model_id')
        oauth2_section = DEFAULT_OAUTH2_SECTION
        token_section = DEFAULT_TOKEN_SECTION
        config = read_config(project)
        access_token = config_get(config.get, token_section, 'access_token')
        endpoint = config_get(config.get, oauth2_section, 'endpoint')
        api = API(
            access_token, endpoint=endpoint, timeout=DEFAULT_MODEL_TIMEOUT)
        try:
            result = api.rollback_model(model_id, version)
        except APIError as e:
            output('[red]模型回滚失败：[/red]')
            output_json(e.result)
            sys.exit(1)
        task_id = result.task_id
        output('模型回滚任务：{}'.format(task_id))
        task_path = join(home, '.bge', 'task_id')
        with open(task_path, 'w') as f:
            f.write(task_id)
        progress = self._wait_model_task(api, task_id, task_path)
        if 'SUCCESS' == progress:
            output('[green]模型 {} 灰度版已成功回滚至版本 {}。[/green]'.format(
                model_id, version
            ))
        elif 'FAILURE' == progress:
            output('[red]模型 {} 灰度回滚至版本 {} 失败。任务结果：{}[/red]'.format(
                model_id, version, result
            ))
        elif 'REVOKED' == progress:
            output(
                '[white]模型 {} 灰度回滚至版本 {} 任务已被撤销失败。[/white]'.format(
                    model_id, version
                )
            )

    def model_versions(self, args):
        limit = args.limit
        model_id = args.model_id
        next_page = args.next_page
        project = get_active_project()
        config_path = self.get_model_config_path()
        config = get_config_parser(config_path)
        section_name = DEFAULT_MODEL_SECTION
        if not model_id:
            model_id = config_get(config.get, section_name, 'model_id')
        oauth2_section = DEFAULT_OAUTH2_SECTION
        token_section = DEFAULT_TOKEN_SECTION
        config = read_config(project)
        access_token = config_get(config.get, token_section, 'access_token')
        endpoint = config_get(config.get, oauth2_section, 'endpoint')
        api = API(
            access_token, endpoint=endpoint, timeout=DEFAULT_MODEL_TIMEOUT)
        try:
            result = api.model_versions(
                model_id, limit=limit, next_page=next_page)
        except APIError as e:
            output('[red]获取模型版本列表失败：[/red]')
            output_json(e.result)
            sys.exit(1)
        output('第 {} 页，模型 {} 已发布版本：'.format(next_page or 1, model_id))
        output('...')
        length = None
        items = result['result']
        for item in items:
            version = item['version']
            message = item['message']
            create_time = datetime.fromtimestamp(item['create_time'])
            if length is None:
                length = len(str(version))
            output('发布时间：{}，版本号：{}，发布记录：{}'.format(
                create_time, str(version).rjust(length), message))
        output('...')
        size = len(items)
        if size == 0 or size < limit or next_page == result['next_page']:
            output('下一页：无')
        else:
            output('下一页：{}'.format(result['next_page']))

    def new_model_license(self, args):
        """获取模型离线运行运行许可证

        每个许可证在过期前不限制模型调用次数；
        """
        expires = args.expires
        project = get_active_project()
        if args.model_id:
            model_id = args.model_id
        else:
            config_path = self.get_model_config_path()
            config = get_config_parser(config_path)
            section_name = DEFAULT_MODEL_SECTION
            model_id = config_get(config.get, section_name, 'model_id')
        oauth2_section = DEFAULT_OAUTH2_SECTION
        token_section = DEFAULT_TOKEN_SECTION
        config = read_config(project)
        access_token = config_get(config.get, token_section, 'access_token')
        endpoint = config_get(config.get, oauth2_section, 'endpoint')
        api = API(
            access_token,
            endpoint=endpoint,
            timeout=DEFAULT_MODEL_TIMEOUT
        )
        csv_file = args.csv
        if isdir(csv_file):
            csv_file = join(csv_file, 'new_license.csv')
        if exists(csv_file):
            csv_file = generate_next_path('{}%s'.format(csv_file))
        with open(csv_file, 'w') as csv_fp:
            csv_writer = csv.DictWriter(
                csv_fp,
                fieldnames=(
                    'line_number',
                    'model_id',
                    'expires',
                    'params',
                    'license_key',
                    'expiration_time',
                    'expiration_utc_ts'
                )
            )
            csv_writer.writeheader()
            if args.file:
                for num, params in enumerate(
                        self._iter_model_params(args.file),
                        start=1):
                    console.rule()
                    output(
                        '处理第 [green]{}[/green] 行参数：{!r}'.format(
                            num,
                            params
                        )
                    )
                    try:
                        params_val = json.loads(params)
                    except Exception:
                        output(format_exc())
                        continue
                    try:
                        r = self._get_model_license(
                            api,
                            model_id,
                            expires,
                            params_val
                        )
                    except Exception:
                        output(format_exc())
                        continue
                    license_key = r['license_key']
                    expiration_time = r['expiration_time']
                    expiration_utc_ts = r['expiration_utc_ts']
                    csv_writer.writerow({
                        'line_number': num,
                        'model_id': model_id,
                        'expires': expires,
                        'params': params,
                        'license_key': license_key,
                        'expiration_time': expiration_time,
                        'expiration_utc_ts': expiration_utc_ts
                    })
                console.rule()
            else:
                params = {}
                if args.args:
                    params = dict(args.args)
                try:
                    r = self._get_model_license(
                        api,
                        model_id,
                        expires,
                        params
                    )
                except Exception:
                    output(format_exc())
                    return
                license_key = r['license_key']
                expiration_time = r['expiration_time']
                expiration_utc_ts = r['expiration_utc_ts']
                csv_writer.writerow({
                    'line_number': 1,
                    'model_id': model_id,
                    'expires': expires,
                    'params': json.dumps(params, sort_keys=True),
                    'license_key': license_key,
                    'expiration_time': expiration_time,
                    'expiration_utc_ts': expiration_utc_ts
                })
            output('处理完成，数据已导出至 {}'.format(csv_file))

    def run_license(self, args):
        """在本地启动的模型服务器上使用许可证方式调用模型"""
        license_file = args.license_file
        port = args.port
        params = {}
        project = get_active_project()
        config_path = self.get_model_config_path()
        config = get_config_parser(config_path)
        section_name = DEFAULT_MODEL_SECTION
        model_id = config_get(config.get, section_name, 'model_id')
        oauth2_section = DEFAULT_OAUTH2_SECTION
        token_section = DEFAULT_TOKEN_SECTION
        config = read_config(project)
        access_token = config_get(config.get, token_section, 'access_token')
        endpoint = config_get(config.get, oauth2_section, 'endpoint')
        api = API(
            access_token,
            endpoint='{}:{}'.format(TEST_SERVER_ENDPOINT, port),
            timeout=DEFAULT_MODEL_TIMEOUT
        )
        csv_file = args.csv
        if isdir(csv_file):
            csv_file = join(csv_file, 'run_license.csv')
        if exists(csv_file):
            csv_file = generate_next_path('{}%s'.format(csv_file))
        with open(csv_file, 'w') as csv_wfp:
            writer = csv.DictWriter(csv_wfp, fieldnames=(
                'model_id',
                'params',
                'result',
                'error'
            ))
            writer.writeheader()
            with open(license_file) as fp:
                license_reader = csv.DictReader(fp)
                for r in license_reader:
                    console.rule()
                    output('开始处理：{!r}'.format(r))
                    if model_id != r['model_id']:
                        output(
                            '[red]文件 {} 包含与项目不一致的 model_id：{}'.format(
                                license_file,
                                r['model_id']
                            )
                        )
                        continue
                    dumps_params = r['params']
                    params = json.loads(dumps_params)
                    license_key = r['license_key']
                    # 只有测试服务器支持许可证模式运行模型
                    headers = None
                    if license_key:
                        headers = {
                            'BGE_LICENSE_KEY': license_key
                        }
                    try:
                        result = api.invoke_model(
                            model_id,
                            headers=headers,
                            **params
                        )
                    except APIError as e:
                        output(
                            '[red]失败！[/red]模型运行失败：{}'.format(e.result)
                        )
                        writer.writerow({
                            'model_id': model_id,
                            'params': dumps_params,
                            'result': json.dumps(e.result, sort_keys=True),
                            'error': True
                        })
                    except Exception:
                        error = format_exc()
                        output(
                            '[red]失败！[/red]模型运行失败：{}'.format(error)
                        )
                        writer.writerow({
                            'model_id': model_id,
                            'params': dumps_params,
                            'result': error,
                            'error': True
                        })
                        sys.exit(1)
                    output('[green]成功！[/green]模型调用完成')
                    writer.writerow({
                        'model_id': model_id,
                        'params': dumps_params,
                        'result': result.dumps(sort_keys=True),
                        'error': False
                    })
        console.rule()
        output('[green]运行结果已保存至[/green] {}'.format(csv_file))

    def run_model(self, args):
        params = {}
        if args.file:
            filepath = args.file
            if not exists(filepath):
                output('文件不存在：{}'.format(filepath))
                sys.exit(1)
            if isdir(filepath):
                output('存在文件夹：{}'.format(filepath))
                sys.exit(1)
            with open(filepath, 'r') as fp:
                params = json.load(fp)
        elif args.args:
            params = dict(args.args)
        model_id = args.model_id
        draft = args.draft
        test = args.test
        no_pretty = args.no_pretty
        output_path = args.output
        project = get_active_project()
        config_path = self.get_model_config_path()
        config = get_config_parser(config_path)
        section_name = DEFAULT_MODEL_SECTION
        if not model_id:
            model_id = config_get(config.get, section_name, 'model_id')
        oauth2_section = DEFAULT_OAUTH2_SECTION
        token_section = DEFAULT_TOKEN_SECTION
        config = read_config(project)
        access_token = config_get(config.get, token_section, 'access_token')
        endpoint = config_get(config.get, oauth2_section, 'endpoint')
        api = API(
            access_token, endpoint=endpoint, timeout=DEFAULT_MODEL_TIMEOUT)
        try:
            if draft is True:
                result = api.invoke_draft_model(model_id, **params)
            elif test is True:
                port = args.port
                license_key = args.license_key
                api = API(
                    access_token,
                    endpoint='{}:{}'.format(TEST_SERVER_ENDPOINT, port),
                    timeout=DEFAULT_MODEL_TIMEOUT
                )
                # 只有测试服务器支持许可证模式运行模型
                headers = None
                if license_key:
                    headers = {
                        'BGE_LICENSE_KEY': license_key
                    }
                result = api.invoke_model(
                    model_id,
                    headers=headers,
                    **params
                )
            else:
                result = api.invoke_model(model_id, **params)
        except APIError as e:
            output('[red]模型运行失败：[/red]')
            if no_pretty:
                output_json(e.result, indent=None)
            else:
                output_json(e.result)
            sys.exit(1)
        output('[green]模型返回值：[/green]')
        if no_pretty:
            output_json(result.json(), indent=None)
        else:
            output_json(result.json())
        if output_path:
            output_path = abspath(output_path)
            with open(output_path, 'w') as fp:
                fp.write(json.dumps(
                    result.json(),
                    indent=4,
                    sort_keys=True,
                    ensure_ascii=False,
                ))
            output(f'[green]模型返回值已输出至：{output_path}[/green]')

    def get_model_config_path(self, home=None):
        if home is None:
            home = get_home()
        config_dir = join(home, '.bge')
        model_config_path = join(home, 'model.ini')
        if not exists(config_dir) and Confirm.ask(
                '是否创建模型 .bge 目录？'):
            os.mkdir(config_dir)
        if not exists(model_config_path):
            output('[red]model.ini 文件不存在，请确认当前是否为模型项目根目录。[/red]')
            sys.exit(1)
        return model_config_path

    def _read_model_project(self, args):
        config_path = self.get_model_config_path()
        output('配置文件：{}'.format(config_path))
        output('配置详情：')
        output('')
        with open(config_path, 'r') as config_file:
            output(config_file.read())

    def install_deps(self, args):
        package_name = args.package_name
        requirements = args.requirements
        upgrade = args.upgrade
        no_deps = args.no_deps
        force_reinstall = args.force_reinstall
        pkgs = ' '.join(package_name)
        config_path = self.get_model_config_path()
        config = get_config_parser(config_path)
        section_name = DEFAULT_MODEL_SECTION
        model_id = config_get(config.get, section_name, 'model_id')
        runtime = config_get(config.get, section_name, 'runtime')
        client = self._get_docker_client()
        command = ['pip install', '--cache-dir', '/tmp/.cache/']
        if upgrade:
            command.append('--upgrade')
        if no_deps:
            command.append('--no-deps')
        if force_reinstall:
            command.append('--force-reinstall')
        deps = []
        if pkgs:
            deps.append(pkgs)
        if requirements:
            deps.append('-r {}'.format(requirements))
        command.append('-t /code/lib {}'.format(' '.join(deps)))
        command = ' '.join(command)
        image_name = RUNTIMES[runtime]
        self._get_or_pull_image(client, image_name)
        with console.status('开始安装模型依赖包...', spinner='earth'):
            command = ('sh -c "{}"').format(command)
            container_name = generate_container_name(model_id)
            self._force_remove_container(client, container_name)
            self._run_by_container(client, image_name, command, container_name)
            output('[green]安装完成[/green]')

    def uninstall_deps(self, args):
        package_name = args.package_name
        requirements = args.requirements
        pkgs = ' '.join(package_name)
        config_path = self.get_model_config_path()
        config = get_config_parser(config_path)
        section_name = DEFAULT_MODEL_SECTION
        model_id = config_get(config.get, section_name, 'model_id')
        runtime = config_get(config.get, section_name, 'runtime')
        client = self._get_docker_client()
        command = ['pip uninstall', '--cache-dir', '/tmp/.cache/']
        deps = []
        if pkgs:
            deps.append(pkgs)
        if requirements:
            deps.append('-r {}'.format(requirements))
        command.append('-t /code/lib {}'.format(' '.join(deps)))
        command = ' '.join(command)
        image_name = RUNTIMES[runtime]
        self._get_or_pull_image(client, image_name)
        with console.status('开始卸载模型依赖包...', spinner='earth'):
            command = ('sh -c "{}"').format(command)
            container_name = generate_container_name(model_id)
            self._force_remove_container(client, container_name)
            self._run_by_container(client, image_name, command, container_name)
            output('[green]卸载完成[/green]')

    def start_model(self, args):
        port = args.port
        update_docker = args.update_docker
        home = get_home()
        config_path = self.get_model_config_path()
        config = get_config_parser(config_path)
        section_name = DEFAULT_MODEL_SECTION
        model_id = config_get(config.get, section_name, 'model_id')
        runtime = config_get(config.get, section_name, 'runtime')
        client = self._get_docker_client()
        image_name = RUNTIMES[runtime]
        if update_docker:
            self._get_or_pull_image(client, image_name)
        command = 'python -u /server/app.py'
        user = get_sys_user()
        container_name = generate_container_name(model_id)
        self._force_remove_container(client, container_name)
        container = client.containers.run(
            image_name,
            command=command,
            name=container_name,
            volumes={home: { 'bind': WORKDIR, 'mode': 'rw' }},
            stop_signal='SIGINT',
            ports={TEST_SERVER_PORT: port},
            user=user,
            detach=True,
            stream=True,
            auto_remove=True)
        output('Model debug server is starting at {}...'.format(port))
        output('Model {} was registered'.format(model_id))
        output('\n\tURL: {}:{}/model/{}'.format(
            TEST_SERVER_ENDPOINT, port, model_id
        ))
        output('\tMethod: GET\n')
        try:
            logs = container.logs(stream=True, follow=True)
            for log in logs:
                output(log.decode('utf-8').rstrip('\n'))
        finally:
            if container.status != 'exited':
                try:
                    container.remove(force=True)
                except Exception:
                    pass

    def clear_model(self, args):
        home = get_home()
        zip_tmpdir = join(home, '.bge', 'tmp')
        if confirm('是否清空目录 {} 下打包模型生成的临时文件？'.format(zip_tmpdir)):
            shutil.rmtree(zip_tmpdir, ignore_errors=True)
            os.mkdir(zip_tmpdir)
            output('[green]成功删除[/green]')
        else:
            output('[white]已取消[/white]')

    def _get_docker_client(self):
        command = WHEREIS_DOCKER if SYS_STR == 'windows' else WHICH_DOCKER
        with os.popen(command) as f:
            docker_path = f.read()
        if not docker_path:
            output(INSTALL_DOCKER_MESSAGE)
            sys.exit(1)
        try:
            client = docker.from_env()
        except docker.errors.DockerException:
            output('[red]请确认 docker 服务是否已开启。[/red]')
            output('[red]启动命令：/etc/init.d/docker start[/red]')
            sys.exit(1)
        return client

    def _get_or_pull_image(self, client, image_name):
        try:
            client.images.get(image_name)
        except docker.errors.NotFound:
            output(
                '[cyan]本地 docker 镜像 {} 不存在，开始拉取...[/cyan]'.format(
                    image_name
                )
            )
            with console.status(f'拉取镜像 {image_name} 中...',
                                spinner='earth'):
                return_code = os.system('docker pull {}'.format(image_name))
                if return_code != 0:
                    output(
                        '[red]拉取镜像 {} 失败，请重试[/red]'.format(image_name)
                    )
                    sys.exit(1)
                output('[green]拉取镜像 {} 成功[/green]'.format(image_name))
        else:
            with console.status(f'更新镜像 {image_name} 中...',
                                spinner='earth'):
                repository, tag = image_name.split(':')
                try:
                    client.images.pull(repository, tag)
                except docker.errors.APIError:
                    output(
                        '[yellow]更新镜像 {} 失败，请重试[/yellow]'.format(image_name)
                    )
                else:
                    output('[green]更新镜像 {} 成功[/green]'.format(image_name))

    def _force_remove_container(self, client, container_name):
        try:
            container = client.containers.get(container_name)
            if container.status != 'exited':
                try:
                    container.remove(force=True)
                except Exception:
                    pass
        except docker.errors.NotFound:
            pass

    def _run_by_container(self, client, image_name, command, container_name):
        home = get_home()
        user = get_sys_user()
        container = client.containers.run(
            image_name,
            command=command,
            name=container_name,
            volumes={home: { 'bind': WORKDIR, 'mode': 'rw' }},
            stop_signal='SIGINT',
            user=user,
            detach=True,
            auto_remove=True)
        try:
            logs = container.logs(stream=True)
            for log in logs:
                output_syntax(
                    log.decode('utf-8').rstrip('\n'),
                    line_numbers=False
                )
        finally:
            if container.status != 'exited':
                try:
                    container.remove(force=True)
                except Exception:
                    pass

    def _iter_model_params(self, path):
        with open(path) as fp:
            while True:
                line = fp.readline()
                if not line:
                    break
                yield line.strip()

    def _get_model_license(self, api, model_id, expires, params):
        result = api.model_license(
            model_id,
            expires=expires,
            params=params
        )
        return result.json()
