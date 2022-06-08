import argparse
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
from posixpath import join, exists, isdir, relpath
from rich.prompt import Prompt
from time import sleep
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
import bgesdk
import logging

def handler(event, context):
    logging.debug(event)
    event = json.loads(event)
    access_token = event['access_token']
    params = event['params']
    return json.dumps({
        "model_code": 0,
        "model_msg": "success",
        "model_data": {
            'params': params,
            'sdk': {
                'version': bgesdk.__version__
            }
        }
    })
'''

MODEL_CONFIG_TEMPLATE = '''\
[Model]
model_id =
memory_size = 128
timeout = 900
runtime = python3
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
    'python2.7': 'teambge/model-python2.7:latest',
    'python3': 'teambge/model-python3.6:latest'
}
WORKDIR = '/code'

RUNTIME_CHOICES = ['python3', 'python2.7']
MEMORY_SIZE_CHOICES = list(range(128, 2049, 64))
MIN_TIMEOUT = 1
MAX_TIMEOUT = 900

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

CREATE_MESSAGE = '创建 {} ... '
INSTALL_DOCKER_MESSAGE = '\
请先安装 docker，参考 https://docs.docker.com/engine/install/'
WAIT_MESSAGE = '已等待 {}s，{}'
TASK_ERROR_MESSAGE = '已等待 {}s，任务状态异常：{}'

WHICH_DOCKER = 'which docker'
WHEREIS_DOCKER = 'whereis docker'

ZIP_COMPRESSION = zipfile.ZIP_DEFLATED


class TestServerPortAction(argparse.Action):

    def __call__(self, parser, namespace, values, option_string=None):
        print(namespace)
        if not namespace.test and values:
            parser.error(
                'argument -p/--port: only allowed with argument -t/--test'
            )
        else:
            namespace.port = values


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
            help='部署灰度版本模型。（开发中，仅支持 python2.7/3.6 的 docker 环境）'
        )
        install_p.add_argument(
            'package_name',
            nargs="+",
            type=str,
            help='要安装的 Python 软件包，如 numpy 或 numpy==v1.19.5'
        )
        install_p.add_argument(
            '-r',
            '--requirements',
            nargs=1,
            type=str,
            help='要安装的 Python 软件包依赖文件'
        )
        install_p.add_argument(
            '-U',
            '--upgrade',
            default=False,
            action='store_true',
            help='是否升级依赖包，同 pip install -U'
        )
        install_p.add_argument(
            '--force-reinstall',
            default=False,
            action='store_true',
            help='是否强制重新安装依赖包，同 pip install --force-reinstall'
        )
        install_p.set_defaults(method=self.install_deps, parser=install_p)

        start_p = model_subparsers.add_parser(
            'start',
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            help='启动本地 HTTP 测试服务器'
        )
        start_p.add_argument(
            '-p',
            '--port',
            default=TEST_SERVER_PORT,
            type=int,
            choices=range(1,65536),
            metavar="[1-65535]",
            help='服务器监听端口'
        )
        start_p.set_defaults(method=self.start_model, parser=start_p)

        expfs_p = model_subparsers.add_parser(
            'expfs',
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            help='扩展模型文件集'
        )
        expfs_p.set_defaults(method=self.upload_model_expfs, parser=expfs_p)

        # 部署子命令
        deploy_p = model_subparsers.add_parser(
            'deploy',
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            help='部署灰度版本模型。'
        )
        deploy_p.add_argument(
            '-i',
            '--ignore-source',
            default=False,
            action="store_true",
            help='部署时不包含模型源代码'
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
        group_2 = run_p.add_mutually_exclusive_group()
        group_2.add_argument(
            '-p',
            '--port',
            default=TEST_SERVER_PORT,
            type=int,
            action=TestServerPortAction,
            choices=range(1,65536),
            metavar="[1-65535]",
            help='服务器监听端口'
        )
        group_2._group_actions.append(draft_a)  # 禁止 -p 与 -d 参数同时提供
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
        run_p.set_defaults(method=self.run_model, parser=run_p)

        # 回滚子命令
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
        rollback_p.set_defaults(method=self.rollback_model, parser=rollback_p)

        # 回滚版本列表子命令
        versions_p = model_subparsers.add_parser(
            'versions',
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            help='模型发布版本列表。（开发中）'
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
            help='清空部署模型时生成的打包临时文件'
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
        model_id, runtime, memory_size, timeout = self._config_model()
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
            model_id, runtime, memory_size, timeout, home=scaffold_dir)
        if confirm('是否安装 bge-python-sdk？'):
            os.chdir(scaffold_dir)
            self._install_sdk()
        output('[green]成功创建模型项目脚手架[/green]')

    def config_model(self, args):
        if args.show:
            return self._read_model_project(args)
        config_path = self.get_model_config_path()
        config_parser = get_config_parser(config_path)
        model_id, runtime, memory_size, timeout \
            = self._config_model(config_parser)
        self._save_model_config(model_id, runtime, memory_size, timeout)

    def _config_model(self, config=None):
        output('开始配置解读模型...')
        default_model_id = ''
        default_runtime = 'python3'
        default_memory_size = 128
        default_timeout = 900
        if config is not None:
            section_name = DEFAULT_MODEL_SECTION
            default_model_id = config_get(config.get, section_name, 'model_id')
            default_runtime = config_get(config.get, section_name, 'runtime')
            default_memory_size = config_get(
                config.getint, section_name, 'memory_size')
            default_timeout = config_get(
                config.getint, section_name, 'timeout')
        model_id = self._input_model_id(default=default_model_id)
        try:
            index = RUNTIME_CHOICES.index(default_runtime)
        except IndexError:
            index = 0
        prompt = '请选择运行环境 [{}]'.format(default_runtime)
        input_prompt = "请选择"
        runtime = qprompt.enum_menu(RUNTIME_CHOICES).show(
            header=prompt,
            dft=index + 1,
            returns="desc",
            msg=input_prompt
        )
        try:
            index = MEMORY_SIZE_CHOICES.index(default_memory_size)
        except IndexError:
            index = 0
        prompt = '请选择内存占用（MB） [{}]'.format(default_memory_size)
        input_prompt = "请选择"
        memory_size = qprompt.enum_menu(MEMORY_SIZE_CHOICES).show(
            header=prompt,
            dft=index + 1,
            returns="desc",
            msg=input_prompt
        )
        prompt = '请输入模型运行超时时间，类型为整数'
        while True:
            timeout = qprompt.ask_int(msg=prompt, dft=default_timeout)
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
            timeout = default_timeout
        return model_id, runtime, memory_size, timeout

    def _input_model_id(self, default=''):
        prompt = '[?] 请输入解读模型编号'
        while True:
            model_id = Prompt.ask(prompt, default=default)
            if not model_id:
                if default:
                    model_id = default
                    break
                output('[red]必须提供模型编号[/red]')
            else:
                if model_id_match(model_id):
                    break
                output('[red]模型编号只能包含数字、大小写字母[/red]')
        return model_id

    def _save_model_config(self, model_id, runtime, memory_size, timeout, home=None):
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
        config.set(section_name, 'memory_size', str(memory_size))
        config.set(section_name, 'timeout', str(timeout))
        with open(config_path, 'w') as config_file:
            config.write(config_file)
        output('')
        output('[green]解读模型配置已保存至[/green] {}'.format(config_path))

    def _install_sdk(self):
        with console.status("正在安装 bge-python-sdk", spinner="earth"):
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

    def deploy_model(self, args):
        """部署模型"""
        ignore_source = args.ignore_source
        home = get_home()
        project = get_active_project()
        config_path = self.get_model_config_path()
        config = get_config_parser(config_path)
        section_name = DEFAULT_MODEL_SECTION
        model_id = config_get(config.get, section_name, 'model_id')
        timestr = datetime.now().strftime('%Y%m%d%H%M%S%f')
        randstr = uuid4().hex
        zip_filename = '{}.{}.{}.zip'.format(model_id, timestr, randstr)
        params = {}
        params['runtime'] = config_get(config.get, section_name, 'runtime')
        params['memory_size'] = config_get(
            config.getint, section_name, 'memory_size')
        params['timeout'] = config_get(config.getint, section_name, 'timeout')
        oauth2_section = DEFAULT_OAUTH2_SECTION
        token_section = DEFAULT_TOKEN_SECTION
        config = read_config(project)
        access_token = config_get(config.get, token_section, 'access_token')
        endpoint = config_get(config.get, oauth2_section, 'endpoint')
        api = API(
            access_token, endpoint=endpoint, timeout=DEFAULT_MODEL_TIMEOUT)
        object_name = None
        if not ignore_source:
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
                if size > 100 * 1024 * 1024:
                    output(
                        '打包后 zip 文件大小为 {}，最大限制 100MB'.format(
                            human_size
                        )
                    )
                    exit(1)
                output('打包成功：{}'.format(tmp.name))
                output('文件大小：{}'.format(human_size))
                output('开始上传模型源码...')
                try:
                    object_name = api.upload(zip_filename, tmp)
                except APIError as e:
                    output('[red]上传模型源码失败：[/red]')
                    output_json(e.result)
                    sys.exit(1)
                output('[green]上传成功[green]')
        with console.status('模型部署中...', spinner='earth'):
            try:
                result = api.deploy_model(
                    model_id, object_name=object_name, **params)
            except APIError as e:
                output('[red]部署模型失败：[/red]')
                output_json(e.result)
                sys.exit(1)
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
                ziph.write(filepath, zip_relpath)
                output('\t{}'.format(zip_relpath))
            for zip_relpath in sorted(minify_relpaths):
                filepath = total_files[zip_relpath]
                with open(filepath, 'r') as fp:
                    content = fp.read()
                with tempfile.NamedTemporaryFile(mode='w') as temp_fp:
                    content = python_minifier.minify(content)
                    temp_fp.write(content)
                    temp_fp.flush()
                    temp_fp.seek(0)
                    ziph.write(temp_fp.name, zip_relpath)
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
            result = api.publish_model(model_id, message)
        except APIError as e:
            output('[red]模型发布失败：[/red]')
            output_json(e.result)
            sys.exit(1)
        output('[green]模型 {} 稳定版已成功发布。\n版本号：{}。[/green]'.format(
            model_id, result['version']))

    def rollback_model(self, args):
        version = args.version
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
        next_page = args.next_page
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
        draft = args.draft
        test = args.test
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
            if draft is True:
                result = api.invoke_draft_model(model_id, **params)
            elif test is True:
                port = args.port
                api = API(
                    access_token,
                    endpoint='{}:{}'.format(TEST_SERVER_ENDPOINT, port),
                    timeout=DEFAULT_MODEL_TIMEOUT
                )
                result = api.invoke_model(model_id, **params)
            else:
                result = api.invoke_model(model_id, **params)
        except APIError as e:
            output('[red]模型运行失败：[/red]')
            output_json(e.result)
            sys.exit(1)
        output('[green]模型返回值：[/green]')
        output_json(result.json())

    def get_model_config_path(self, home=None):
        if home is None:
            home = get_home()
        config_dir = join(home, '.bge')
        model_config_path = join(home, 'model.ini')
        if not exists(model_config_path) or not exists(config_dir):
            output('[red]请确认当前是否为模型项目根目录。[/red]')
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

    def start_model(self, args):
        port = args.port
        home = get_home()
        config_path = self.get_model_config_path()
        config = get_config_parser(config_path)
        section_name = DEFAULT_MODEL_SECTION
        model_id = config_get(config.get, section_name, 'model_id')
        runtime = config_get(config.get, section_name, 'runtime')
        client = self._get_docker_client()
        image_name = RUNTIMES[runtime]
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
                output(log.strip().decode('utf-8'))
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
            with console.status('拉取 docker 镜像中...', spinner='earth'):
                return_code = os.system('docker pull {}'.format(image_name))
                if return_code != 0:
                    output(
                        '[red]拉取镜像 {} 失败，请重试[/red]'.format(image_name)
                    )
                    sys.exit(1)
                output('[green]拉取镜像 {} 成功[/green]'.format(image_name))
        else:
            with console.status('更新 docker 镜像中...', spinner='earth'):
                repository, tag = image_name.split(':')
                try:
                    client.images.pull(repository, tag)
                except docker.errors.APIError:
                    output(
                        '[red]更新镜像 {} 失败，请重试[/red]'.format(image_name)
                    )
                    sys.exit(1)
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
                output_syntax(log.strip().decode('utf-8'), line_numbers=False)
        finally:
            if container.status != 'exited':
                try:
                    container.remove(force=True)
                except Exception:
                    pass
