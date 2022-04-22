from bgesdk.management.command import BaseCommand
from bgesdk.management.commands.config import list_projects
from bgesdk.management.utils import (
    get_config_path,
    get_active_path,
    output
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
            return list_projects()
        else:
            project = project.lower()
            return self.workon_project(project)

    def workon_project(self, project):
        config_path = get_config_path(project)
        output('配置文件位置：{}'.format(config_path))
        active_path = get_active_path()
        with open(active_path, 'w') as fp:
            fp.write(project)
        output('[green]已激活 {} 的项目配置'.format(project))
