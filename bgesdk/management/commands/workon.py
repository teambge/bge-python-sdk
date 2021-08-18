import os

from posixpath import splitext

from bgesdk.management.command import BaseCommand
from bgesdk.management.utils import (
    get_config_dir, get_config_path, get_active_path, get_active_project
)


class Command(BaseCommand):

    order = 2
    help='激活某项目配置，其他命令均使用已激活的项目配置作为全局配置。'

    def add_arguments(self, parser):
        parser.add_argument(
            'project',
            nargs='?',
            help='自定义项目名称保存全局配置，其他命令默认读取正在生效的项目配置。'
        )

    def handler(self, args):
        """将配置写入项目文件"""
        project = args.project
        if not project:
            return self.list_projects()
        else:
            project = project.lower()
            return self.workon_project(project)

    def workon_project(self, project):
        config_path = get_config_path(project)
        print('配置文件位置：{}'.format(config_path))
        active_path = get_active_path()
        with open(active_path, 'w') as fp:
            fp.write(project)
        print('已激活 {} 的项目配置'.format(project))

    def list_projects(self):
        active_project = get_active_project()
        config_dir = get_config_dir()
        projects = []
        for filename in os.listdir(config_dir):
            name, ext = splitext(filename)
            if ext != '.ini':
                continue
            projects.append(name)
        print('通过 bge workon <NAME> 切换生效配置：\n')
        projects.sort()
        if active_project in projects:
            print(active_project, '- 已生效')
        for project in projects:
            if project == active_project:
                continue
            print(project)
