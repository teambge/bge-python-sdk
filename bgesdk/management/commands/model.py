import argparse
import docker
import json
import os
import pkgutil
import pwd
import re
import shutil
import six
import stat
import sys
import tempfile
import zipfile

from datetime import datetime
from pimento import menu
from posixpath import join, exists, abspath, isdir, relpath, dirname, split
from six.moves import input
from time import sleep
from uuid import uuid4

from bgesdk.client import OAuth2, API
from bgesdk.error import APIError
from bgesdk.management import constants
from bgesdk.management.utils import get_active_project, config_get, \
                                    secure_str, get_home, read_config, \
                                    generate_container_name, \
                                    get_config_parser, confirm
from bgesdk.version import __version__


DEFAULT_OAUTH2_SECTION = constants.DEFAULT_OAUTH2_SECTION
DEFAULT_TOKEN_SECTION = constants.DEFAULT_TOKEN_SECTION
DEFAULT_MODEL_SECTION = constants.DEFAULT_MODEL_SECTION
DEFAULT_MODEL_TIMEOUT = constants.DEFAULT_MODEL_TIMEOUT
TEST_SERVER_ENDPOINT = constants.TEST_SERVER_ENDPOINT
TEST_SERVER_PORT = constants.TEST_SERVER_PORT

model_match = re.compile(r'^[a-zA-Z0-9]{15}$').match

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

model_config_template = '''\
[Model]
model_id =
memory_size = 128
timeout = 900
runtime = python3
'''

RUNTIMES = {
    'python2.7': 'teambge/model-python2.7:{}'.format(__version__),
    'python3': 'teambge/model-python3.6:{}'.format(__version__)
}
WORKDIR = '/code'

RUNTIME_CHOICES = ['python3', 'python2.7']
MEMORY_SIZE_CHOICES = [
    128, 192, 256, 320, 384, 448, 512, 576, 640, 704, 768, 832,
    896, 960, 1024, 1088, 1152, 1216, 1280, 1344, 1408, 1472, 1536,
    1600, 1664, 1728, 1792, 1856, 1920, 1984, 2048
]
MIN_TIMEOUT = 1
MAX_TIMEOUT = 900

TOTAL_PROGRESS = {
    'FAILURE': '任务执行失败',
    'PENDING': '任务等待中',
    'RECEIVED': '任务已接收',
    'RETRY': '任务将被重试',
    'REVOKED': '任务取消',
    'STARTED': '任务已开始',
    'SUCCESS': '任务执行成功'
}


def init_parser(subparsers):
    home = get_home()
    model_p = subparsers.add_parser(
        'model',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        help='模型初始化脚手架、配置、部署等相关命令。'
    )
    model_p.set_defaults(method=print_subparser_help, parser=model_p)
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
        '--home',
        type=str,
        default=home,
        help='脚手架项目生成的父级目录，默认为当前目录。'
    )
    init_p.set_defaults(method=init_scaffold, parser=init_p)

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
    config_p.set_defaults(method=config_model, parser=config_p)

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
    install_p.set_defaults(method=install_deps, parser=install_p)

    start_p = model_subparsers.add_parser(
        'start',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        help='启动本地 HTTP 测试服务器'
    )
    start_p.set_defaults(method=start_model, parser=start_p)

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
    deploy_p.set_defaults(method=deploy_model, parser=deploy_p)
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
    publish_p.set_defaults(method=publish_model, parser=publish_p)

    # 运行模型子命令
    run_p = model_subparsers.add_parser(
        'run',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        help='调用线上稳定版模型。'
    )
    group = run_p.add_mutually_exclusive_group()
    group.add_argument(
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
    run_p.set_defaults(method=run_model, parser=run_p)

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
    rollback_p.set_defaults(method=rollback_model, parser=rollback_p)

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
    versions_p.set_defaults(method=model_versions, parser=versions_p)


def print_subparser_help(args):
    """打印 subparser 帮助信息"""
    parser = args.parser
    parser.print_help(sys.stderr)


def init_scaffold(args):
    scaffold_name = args.scaffold_name
    home = args.home
    if home is None:
        home = get_home()
    scaffold_dir = join(home, scaffold_name)
    if exists(scaffold_dir):
        print('错误！{} 已存在 '.format(scaffold_dir))
        sys.exit(1)
    if not exists(home):
        print('错误！无法找到 home 目录 {}。'.format(home))
        sys.exit(1)
    model_id, runtime, memory_size, timeout = _config_model()
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
            sys.exit(1)
        else:
            print('已存在')
    model_config_path = join(scaffold_dir, 'model.ini')
    if not exists(model_config_path):
        open(model_config_path, 'w').write(model_config_template)
    script_name = 'main.py'
    script_path = join(scaffold_dir, script_name)
    with open(script_path, 'wb') as file_out:
        file_out.write(main_py.encode())
    st = os.stat(script_path)
    os.chmod(script_path, st.st_mode | stat.S_IEXEC)
    _save_model_config(
        model_id, runtime, memory_size, timeout, home=scaffold_dir)
    if confirm('是否安装 bge-python-sdk？'):
        os.chdir(scaffold_dir)
        _install_sdk()
    print('成功创建模型项目脚手架')


def config_model(args):
    if args.show:
        return _read_model_project(args)
    config_path = get_model_config_path()
    config_parser = get_config_parser(config_path)
    model_id, runtime, memory_size, timeout = _config_model(config_parser)
    _save_model_config(model_id, runtime, memory_size, timeout)


def _config_model(config=None):
    print('开始配置解读模型...')
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
    # model_id
    prompt = '？请输入解读模型编号 [{}]：'.format(default_model_id)
    while True:
        model_id = input(prompt)
        if model_id:
            break
        if not default_model_id:
            print('模型编号未设置...')
            continue
        model_id = default_model_id
        break
    # runtime
    try:
        index = RUNTIME_CHOICES.index(default_runtime)
    except IndexError:
        index = 0
    prompt = '？请选择运行环境 [{}]'.format(default_runtime)
    input_prompt = "请选择: "
    runtime = menu(
        RUNTIME_CHOICES, prompt, input_prompt, default_index=index,
        indexed=True)
    # memory_size
    try:
        index = MEMORY_SIZE_CHOICES.index(default_memory_size)
    except IndexError:
        index = 0
    prompt = '？请选择内存占用（MB） [{}]'.format(default_memory_size)
    input_prompt = "请选择: "
    memory_size = menu(
        MEMORY_SIZE_CHOICES, prompt, input_prompt, default_index=index,
        indexed=True)
    # timeout
    prompt = '？请输入模型运行超时时间 [{}]：'.format(default_timeout)
    while True:
        timeout = input(prompt)
        if not timeout:
            if not default_timeout:
                print('模型运行时间未设置...')
                continue
            timeout = default_timeout
        else:
            try:
                timeout = int(timeout)
            except ValueError:
                print('请输入整数...')
                continue
        if (MIN_TIMEOUT and timeout < MIN_TIMEOUT) \
                or (MAX_TIMEOUT and timeout > MAX_TIMEOUT):
            print('超出范围 [{},{}]，请重新输入'.format(
                MIN_TIMEOUT or '', MAX_TIMEOUT or ''))
            continue
        break
    if not timeout:
        timeout = default_timeout
    return model_id, runtime, memory_size, timeout


def _save_model_config(model_id, runtime, memory_size, timeout, home=None):
    # save
    config_path = get_model_config_path(home=home)
    config = get_config_parser(config_path)
    section_name = DEFAULT_MODEL_SECTION
    if section_name not in config.sections():
        config.add_section(section_name)
    print('开始保存解读模型配置...')
    print('配置文件 {}'.format(config_path))
    config.set(section_name, 'model_id', model_id)
    config.set(section_name, 'runtime', runtime)
    config.set(section_name, 'memory_size', str(memory_size))
    config.set(section_name, 'timeout', str(timeout))
    with open(config_path, 'w') as config_file:
        config.write(config_file)
    print('')
    print('解读模型配置已保存至：{}'.format(config_path))
    

def _install_sdk():
    home = get_home()
    config_path = get_model_config_path()
    config = get_config_parser(config_path)
    section_name = DEFAULT_MODEL_SECTION
    model_id = config_get(config.get, section_name, 'model_id')
    runtime = config_get(config.get, section_name, 'runtime')
    image_name = RUNTIMES[runtime]
    container_name = generate_container_name(model_id)
    deps = []
    docker_path = os.popen('which docker')
    if not docker_path:
        print('请先安装 docker，参考 https://docs.docker.com/engine/install/')
        sys.exit(1)
    client = docker.from_env()
    command = 'pip install --no-deps bge-python-sdk pimento -t /code/lib'
    try:
        client.images.get(image_name)
    except docker.errors.NotFound:
        print('本地 docker 镜像 {} 不存在，开始拉取...'.format(image_name))
        return_code = os.system('docker pull {}'.format(image_name))
        if return_code != 0:
            print('镜像拉取失败，请重试')
            sys.exit(1)
        print('镜像拉取成功')
    print('开始安装模型依赖包...')
    command = ('sh -c "{}"').format(command)
    pwd_info = pwd.getpwuid(os.getuid())
    uid = pwd_info.pw_uid
    gid = pwd_info.pw_gid
    try:
        container = client.containers.get(container_name)
        if container.status != 'exited':
            try:
                container.remove(force=True)
            except:
                pass
    except docker.errors.NotFound:
        pass
    container = client.containers.run(
        image_name,
        command=command,
        name=container_name,
        volumes={home: { 'bind': WORKDIR, 'mode': 'rw' }},
        stop_signal='SIGINT',
        user='{}:{}'.format(uid, gid),
        detach=True,
        auto_remove=True)
    try:
        logs = container.logs(stream=True)
        for log in logs:
            sys.stdout.write(log.decode('utf-8'))
            sys.stdout.flush()
    finally:
        if container.status != 'exited':
            try:
                container.remove(force=True)
            except:
                pass
    print('安装完成')


def deploy_model(args):
    """部署模型"""
    ignore_source = args.ignore_source
    home = get_home()
    project = get_active_project()
    config_path = get_model_config_path()
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
        print('开始打包模型源码...')
        with tempfile.NamedTemporaryFile(suffix='.zip') as tmp:
            with zipfile.ZipFile(tmp.name, 'w', zipfile.ZIP_DEFLATED) as zf:
                _zip_codedir(home, zf)
            tmp.flush()
            tmp.seek(0, 2)
            size = tmp.tell()
            tmp.seek(0)
            print('打包成功')
            size_mb = '%.2f' % (size / 1024.0 / 1024.0)
            if size > 100 * 1024 * 1024:
                print('打包后 zip 文件大小 {}，最大限制 100MB'.format(size_mb))
                exit(1)
            print('打包 zip 文件大小为：{}MB'.format(size_mb))
            print('开始上传模型源码...')
            try:
                object_name = api.upload(zip_filename, tmp)
            except APIError as e:
                print('上传模型源码失败：{}'.format(e))
                sys.exit(1)
            print('上传成功')
    print('模型部署中...')
    try:
        result = api.deploy_model(
            model_id, object_name=object_name, **params)
    except APIError as e:
        print('模型部署失败：{}'.format(e))
        sys.exit(1)
    task_id = result.task_id
    print('模型部署任务：{}'.format(task_id))
    task_path = join(home, '.bge', 'task_id')
    with open(task_path, 'w') as f:
        f.write(task_id)
    print('模型部署任务返回结果：')
    seconds = 0
    while True:
        result = api.task(task_id)
        progress = result.progress
        if progress not in TOTAL_PROGRESS:
            print('已等待 {}s，任务状态异常：{}'.format(seconds, progress))
            try:
                os.unlink(task_path)
            except (IOError, OSError):
                pass
            sys.exit(1)
        print('已等待 {}s，{}'.format(seconds, TOTAL_PROGRESS[progress]))
        if progress in ('SUCCESS', 'FAILURE', 'REVOKED'):
            break
        sleep(1)
        seconds += 1
    try:
        os.unlink(task_path)
    except (IOError, OSError):
        pass
    print('模型 {} 灰度部署成功。'.format(model_id))


def _zip_codedir(path, ziph):
    for root, dirs, files in os.walk(path):
        # 项目目录 .bge/build 不打包入 zip 文件
        bgedir = join(path.rstrip('/'), '.bge', 'build')
        if root == bgedir or root.startswith(bgedir + '/'):
            continue
        for file in files:
            filepath = join(root, file)
            zip_relpath = relpath(filepath, path)
            ziph.write(filepath, zip_relpath)


def publish_model(args):
    """发布模型到稳定版"""
    message = args.message
    home = get_home()
    project = get_active_project()
    config_path = get_model_config_path()
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
        print('模型发布失败：{}'.format(e))
        sys.exit(1)
    print('模型 {} 稳定版已成功发布。\n版本号：{}。'.format(
        model_id, result['version']))


def rollback_model(args):
    version = args.version
    home = get_home()
    project = get_active_project()
    config_path = get_model_config_path()
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
        print('模型回滚失败：{}'.format(e))
        sys.exit(1)
    task_id = result.task_id
    print('模型回滚任务：{}'.format(task_id))
    task_path = join(home, '.bge', 'task_id')
    with open(task_path, 'w') as f:
        f.write(task_id)
    seconds = 0
    while True:
        result = api.task(task_id)
        progress = result.progress
        if progress not in TOTAL_PROGRESS:
            print('已等待 {}s，任务状态异常：{}'.format(seconds, progress))
            try:
                os.unlink(task_path)
            except (IOError, OSError):
                pass
            sys.exit(1)
        print('已等待 {}s，{}'.format(seconds, TOTAL_PROGRESS[progress]))
        if progress in ('SUCCESS', 'FAILURE', 'REVOKED'):
            break
        sleep(1)
        seconds += 1
    try:
        os.unlink(task_path)
    except (IOError, OSError):
        pass
    print('模型 {} 灰度版已成功回滚至版本 {}。'.format(model_id, version))


def model_versions(args):
    limit = args.limit
    next_page = args.next_page
    home = get_home()
    project = get_active_project()
    config_path = get_model_config_path()
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
        print('获取模型版本列表失败：{}'.format(e))
        sys.exit(1)
    print('第 {} 页，模型 {} 已发布版本：'.format(next_page or 1, model_id))
    print('...')
    length = None
    items = result['result']
    for item in items:
        version = item['version']
        message = item['message']
        create_time = datetime.fromtimestamp(item['create_time'])
        if length is None:
            length = len(str(version))
        print('发布时间：{}，版本号：{}，发布记录：{}'.format(
            create_time, str(version).rjust(length), message))
    print('...')
    size = len(items)
    if size == 0 or size < limit or next_page == result['next_page']:
        print('下一页：无')
    else:
        print('下一页：{}'.format(result['next_page']))


def run_model(args):
    params = {}
    if args.file:
        if not exists(args.file):
            print('文件不存在：{}'.format(args.file))
            sys.exit(1)
        if isdir(args.file):
            print('存在文件夹：{}'.format(args.file))
            sys.exit(1)
        with open(file, 'r') as fp:
            params = json.load(fp)
    elif args.args:
        params = dict(args.args)
    draft = args.draft
    test = args.test
    home = get_home()
    project = get_active_project()
    config_path = get_model_config_path()
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
            api = API(
                access_token, endpoint=TEST_SERVER_ENDPOINT,
                timeout=DEFAULT_MODEL_TIMEOUT)
            result = api.invoke_model(model_id, **params)
        else:
            result = api.invoke_model(model_id, **params)
    except APIError as e:
        print('模型运行失败：{}'.format(e))
        sys.exit(1)
    print('模型返回值：')
    print(json.dumps(result.json(), indent=4, ensure_ascii=False))


def get_model_config_path(home=None):
    if home is None:
        home = get_home()
    config_dir = join(home, '.bge')
    model_config_path = join(home, 'model.ini')
    if not exists(model_config_path) or not exists(config_dir):
        print('请确认当前目录是否为 BGE 开放平台解读模型脚手架项目的根目录。')
        sys.exit(1)
    return model_config_path


def _read_model_project(args):
    config_path = get_model_config_path()
    print('配置文件：{}'.format(config_path))
    print('配置详情：')
    print('')
    with open(config_path, 'r') as config_file:
        print(config_file.read())


def install_deps(args):
    package_name = args.package_name
    requirements = args.requirements
    upgrade = args.upgrade
    force_reinstall = args.force_reinstall
    pkgs = ' '.join(package_name)
    home = get_home()
    config_path = get_model_config_path()
    config = get_config_parser(config_path)
    section_name = DEFAULT_MODEL_SECTION
    model_id = config_get(config.get, section_name, 'model_id')
    runtime = config_get(config.get, section_name, 'runtime')
    image_name = RUNTIMES[runtime]
    container_name = generate_container_name(model_id)
    deps = []
    if pkgs:
        deps.append(pkgs)
    if requirements:
        deps.append('-r {}'.format(requirements))
    docker_path = os.popen('which docker')
    if not docker_path:
        print('请先安装 docker，参考 https://docs.docker.com/engine/install/')
        sys.exit(1)
    client = docker.from_env()
    command = ['pip install']
    if upgrade:
        command.append('--upgrade')
    if force_reinstall:
        command.append('--force-reinstall')
    command.append('-t /code/lib {}'.format(' '.join(deps)))
    command = ' '.join(command)
    try:
        client.images.get(image_name)
    except docker.errors.NotFound:
        print('本地 docker 镜像 {} 不存在，开始拉取...'.format(image_name))
        return_code = os.system('docker pull {}'.format(image_name))
        if return_code != 0:
            print('镜像拉取失败，请重试')
            sys.exit(1)
        print('镜像拉取成功')
    print('开始安装模型依赖包...')
    command = ('sh -c "{}"').format(command)
    pwd_info = pwd.getpwuid(os.getuid())
    uid = pwd_info.pw_uid
    gid = pwd_info.pw_gid
    try:
        container = client.containers.get(container_name)
        if container.status != 'exited':
            try:
                container.remove(force=True)
            except:
                pass
    except docker.errors.NotFound:
        pass
    container = client.containers.run(
        image_name,
        command=command,
        name=container_name,
        volumes={home: { 'bind': WORKDIR, 'mode': 'rw' }},
        stop_signal='SIGINT',
        user='{}:{}'.format(uid, gid),
        detach=True,
        auto_remove=True)
    try:
        logs = container.logs(stream=True)
        for log in logs:
            sys.stdout.write(log.decode('utf-8'))
            sys.stdout.flush()
    finally:
        if container.status != 'exited':
            try:
                container.remove(force=True)
            except:
                pass
    print('安装完成')


def start_model(args):
    print('Model debug server is starting ...')
    home = get_home()
    config_path = get_model_config_path()
    config = get_config_parser(config_path)
    section_name = DEFAULT_MODEL_SECTION
    model_id = config_get(config.get, section_name, 'model_id')
    runtime = config_get(config.get, section_name, 'runtime')
    image_name = RUNTIMES[runtime]
    container_name = generate_container_name(model_id)
    docker_path = os.popen('which docker')
    if not docker_path:
        print('请先安装 docker，参考 https://docs.docker.com/engine/install/')
        sys.exit(1)
    client = docker.from_env()
    try:
        client.images.get(image_name)
    except docker.errors.NotFound:
        print('本地 docker 镜像 {} 不存在，开始拉取...'.format(image_name))
        return_code = os.system('docker pull {}'.format(image_name))
        if return_code != 0:
            print('镜像拉取失败，请重试')
            sys.exit(1)
        print('镜像拉取成功')
    command = 'sh -c "python /server/app.py"'
    pwd_info = pwd.getpwuid(os.getuid())
    uid = pwd_info.pw_uid
    gid = pwd_info.pw_gid
    try:
        container = client.containers.get(container_name)
        if container.status != 'exited':
            try:
                container.remove(force=True)
            except:
                pass
    except docker.errors.NotFound:
        pass
    container = client.containers.run(
        image_name,
        command=command,
        name=container_name,
        volumes={home: { 'bind': WORKDIR, 'mode': 'rw' }},
        stop_signal='SIGINT',
        ports={TEST_SERVER_PORT: TEST_SERVER_PORT},
        user='{}:{}'.format(uid, gid),
        detach=True,
        stream=True,
        auto_remove=True)
    print('Model {} was registered'.format(model_id))
    print('\n\tURL: {}/model/{}'.format(TEST_SERVER_ENDPOINT, model_id))
    print('\tMethod: GET\n')
    try:
        logs = container.logs(stream=True, follow=True)
        for log in logs:
            sys.stdout.write(log.decode('utf-8'))
            sys.stdout.flush()
    finally:
        if container.status != 'exited':
            try:
                container.remove(force=True)
            except:
                pass
