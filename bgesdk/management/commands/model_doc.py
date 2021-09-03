import argparse
import json
import os
import sys

from datetime import datetime
from posixpath import join, exists

from bgesdk.client import API
from bgesdk.error import APIError
from bgesdk.management.command import BaseCommand
from bgesdk.management.constants import (
    TAB_CHOICES, TITLE_NAME, API_TABLE, DEFAULT_TOKEN_SECTION,
    DEFAULT_OAUTH2_SECTION, DEFAULT_MODEL_TIMEOUT
)
from bgesdk.management.utils import (
    config_get, get_active_project, read_config, get_home
)
from bgesdk.management.validate import validator_doc


class Command(BaseCommand):

    order = 6
    help = '对模型文档进行预览和发布，可访问 ' \
           'https://api.bge.genomics.cn/doc/scripts/model_doc.json 下载示例文件'

    def add_arguments(self, parser):
        home = get_home()
        doc_ps = parser.add_subparsers(help='对模型文档进行预览和发布')

        init_p = doc_ps.add_parser(
            'init',
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            help='初始化 docsify 项目。'
        )
        init_p.add_argument(
            'name',
            type=str,
            default='docs',
            help='docsify 项目名称'
        )
        init_p.add_argument(
            '--home',
            type=str,
            default=home,
            help='docsify 项目生成的父级目录，默认为当前目录'
        )
        init_p.set_defaults(method=self.init_docsify, parser=init_p)

        pre_p = doc_ps.add_parser(
            'preview',
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            help='对模型文档进行预览'
        )

        pre_p.add_argument(
            'path',
            type=str,
            help='模型文档的 json 文件路径。'
        )
        pre_p.add_argument(
            '--home',
            type=str,
            default=home,
            help='docsify 项目的根目录，默认为当前目录'
        )

        pre_p.set_defaults(method=self.preview, parser=pre_p)

        release_p = doc_ps.add_parser(
            'release',
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            help='发布模型文档'
        )
        release_p.set_defaults(method=self.release_doc, parser=release_p)

    def handler(self, args):
        """打印 subparser 帮助信息"""
        parser = args.parser
        parser.print_help(sys.stderr)

    def init_docsify(self, args):
        name = args.name
        home = args.home
        if home is None:
            home = get_home()
        docs_dir = join(home, name)
        if exists(docs_dir):
            print('错误！{} 已存在 '.format(docs_dir))
            sys.exit(1)
        if not exists(home):
            print('错误！无法找到 home 目录 {}。'.format(home))
            sys.exit(1)
        with os.popen('docsify init {}'.format(docs_dir)) as f:
            content = f.read()
        if content:
            print('docsify 项目已初始化，路径为：{}'.format(docs_dir))
            print('请跳转至项目目录下。')

    def get_docs_dir(self, home=None):
        if home is None:
            home = get_home()
        doc_path = join(home, 'index.html')
        if not exists(doc_path):
            print('请确认当前目录或者所输入的项目路径是否为 docsify 项目的根目录。')
            sys.exit(1)
        return home

    def preview(self, args):
        with os.popen('which docsify') as f:
            content = f.read()
        if not content:
            print('请先安装 docsify，参考 https://docsify.js.org/#/quickstart')
            sys.exit(1)
        path = args.path
        if not exists(path):
            print('文件路径：{} 有误，请检查。'.format(path))
            sys.exit(1)
        docs_dir = self.get_docs_dir(home=args.home)
        doc_data = json.load(open(path))
        result = validator_doc(doc_data)
        if result['valid'] is False:
            print('文件内容有误，错误内容：{}'.format(result['errors']))
            sys.exit(1)
        doc_tab = doc_data['doc_tab']
        model_id = doc_data['model_id']
        doc_content = doc_data['doc_content']
        sidebar_path = join(docs_dir, '_sidebar.md')
        file_dir = join(docs_dir, 'model_center')
        sidebar_lines = []
        req_path = 'model_center/{}.md'.format(model_id)
        for content in doc_content:
            language = content['language']
            doc_name = content['doc_name']
            if language == 'en':
                file_dir = join(
                    docs_dir, 'en', 'model_center')
                req_path = 'en/model_center/{}.md'.format(model_id)
            if not exists(file_dir):
                os.makedirs(file_dir)
            file_path = join(
                file_dir, '{}.md'.format(model_id))
            sidebar = '        * [{}]({})'.format(doc_name, req_path)
            sidebar_lines.append(sidebar)
            self._make_doc(content, file_path, model_id)

        self._write_to_sidebar(doc_tab, sidebar_path, sidebar_lines)
        self._write_index(docs_dir)
        os.system('docsify serve {} --port 3000'.format(docs_dir))

    def _make_doc(self, content, file_path, model_id):
        line_feed = '\n'
        lines = []
        divid_line = '--------'
        developer = 'Developer: {}'.format(content.get('developer', ''))
        content_title = '# {}'.format(content.get('content_title', ''))
        ctime = 'Ctime: {}'.format(
            datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S'))
        version_line = 'Version:'
        join_lines = [content_title, ctime, developer, version_line,
                      divid_line]
        for key, value in TITLE_NAME.items():
            title_line = '#### {}'.format(value)
            join_model_id = None
            science_detail_title = None
            if key == 'brief_intro':
                title_line = '### {}'.format(value)
                join_model_id = '**model_id**: `{}`'.format(model_id)
                science_detail_title = '### {}'.format('科学细节')
            handle_content = self._join_content(content.get(key, {}))
            join_lines.append(title_line)
            join_lines.extend(handle_content)
            join_lines.append(join_model_id)
            join_lines.append(science_detail_title)
        api_title = '### {}'.format('API调用')
        join_lines.append(api_title)

        for key, value in API_TABLE.items():

            params_line = '![{}](https://img.shields.io/badge/' \
                          '{}-{}-blue)'.format(key, value, key)
            params = dict()
            if key == 'QueryParams':
                pass
            elif key == 'Success':
                params = content.get('return_params', None)
            elif key == 'State':
                params = content.get('state_explain', None)
            params_table = self._join_table(params)
            join_lines.append(params_line)
            join_lines.append(params_table)

        example_result_line = '![Success](https://img.shields.io/badge/' \
                              '输出-Success-green)'
        json_str = '```json'
        example_result = content.get('example_result')
        example_result_json = ''
        if example_result:
            example_result_json = json.dumps(
                example_result, sort_keys=False, indent=4)
        last_json_str = '```'
        join_lines.append(example_result_line)
        join_lines.append(json_str)
        join_lines.append(example_result_json)
        join_lines.append(last_json_str)
        join_lines.append(divid_line)

        ref_line = '### {}'.format('参考文献')
        join_lines.append(ref_line)
        refs = content.get('ref', [])
        ref_lines = []
        if refs:
            for index, ref in enumerate(refs):
                ref_str = r'\[{}]: {}{}'.format(index + 1, ref, '<br>')
                ref_lines.append(ref_str)
        join_lines.append(ref_lines)
        for line in join_lines:
            if isinstance(line, list):
                for l in line:
                    lines.append(l + line_feed)
            elif isinstance(line, str):
                lines.append(line + line_feed)
            lines.append(line_feed)

        with open(file_path, 'w') as f:
            f.writelines(lines)

    def _join_content(self, content):
        line_feed = '\n'
        templates = content.get('templates', None)
        arguments = content.get('arguments', None)
        if templates:
            description_lines = []
            params = arguments.get('image', None)
            target_array = 0
            for tem in templates:
                tem = str(tem)
                word = '{%s}' % 'image'
                if word in tem:
                    word_count = tem.count(word)
                    for index in range(target_array,
                                       target_array + word_count):
                        try:
                            data = params[index]
                        except:
                            print(
                                'arguments中的关键词数组应大于'
                                '等于templates中的关键词数组')
                            sys.exit(1)
                        image_md = '''{}<br><center><img src="{}" 
                        width="386" height="386" /><div style="color: #999;
                        ">{}</div></center><br>{}'''.format(
                            line_feed, data['uri'], data['caption'],
                            line_feed)
                        tem = tem.replace(word, image_md, 1)
                    target_array += word_count
                description_lines.append(tem)
            return description_lines
        return ['未提及', 'Not mentioned']

    def _join_table(self, params):
        table_lines = []
        table_1 = '| {} | {} |'.format('数据名'.ljust(29), '描述'.ljust(29))
        table_2 = '| {} | {} |'.format('-' * 31, '-' * 31)
        table_lines.append(table_1)
        table_lines.append(table_2)
        for key, value in params.items():
            param_line = '| {} | {} |'.format(
                str(key).ljust(31), str(value))
            table_lines.append(param_line)
        return table_lines

    def _write_to_sidebar(self, doc_tab, sidebar_path, sidebar_lines):
        sidebar_title = '* :chart_with_upwards_trend: 模型中心'
        tab_choices = dict(TAB_CHOICES)
        tab = '    * {}'.format(tab_choices.get(doc_tab))
        lines = [sidebar_title, tab]
        lines.extend(sidebar_lines)
        with open(sidebar_path, 'w') as f:
            for line in lines:
                f.write(line)
                f.write('\n')

    def _write_index(self, docs_dir):
        index_path = join(docs_dir, 'index.html')
        if exists(index_path) is False:
            print('docs 目录下无 index.html')
            sys.exit(1)
        lines = []
        with open(index_path, 'r') as f:
            for line in f.readlines():
                lines.append(line)
                if line == '    window.$docsify = {\n':
                    lines.append('      loadSidebar: true,\n')
                elif line == '  </script>\n':
                    lines.append(
                        '  <script src="//cdn.jsdelivr.net/npm/prismjs/'
                        'components/prism-json.min.js"></script>\n')
                    lines.append(
                        '  <script src="//cdn.jsdelivr.net/npm/docsify-kate'
                        'x@latest/dist/docsify-katex.js"></script>\n')
                    lines.append(
                        '  <link rel="stylesheet" href="//cdn.jsdelivr.net/'
                        'npm/katex@latest/dist/katex.min.css"/>\n')
        with open(index_path, 'w') as f:
            f.writelines(lines)

    def release_doc(self, args):
        project = get_active_project()
        config = read_config(project)
        access_token = config_get(
            config.get, DEFAULT_TOKEN_SECTION, 'access_token')
        endpoint = config_get(config.get, DEFAULT_OAUTH2_SECTION, 'endpoint')
        api = API(
            access_token, endpoint=endpoint, timeout=DEFAULT_MODEL_TIMEOUT)
        input_value = input('？请输入需要发布的 json 文件路径：')
        if input_value:
            if not exists(input_value):
                print('文件路径：{} 有误，请检查。'.format(input_value))
                sys.exit(1)
            doc_data = json.load(open(input_value))
            doc_tab = doc_data['doc_tab']
            model_id = doc_data['model_id']
            doc_content = doc_data['doc_content']
            try:
                result = api.upload_model_doc(doc_tab, model_id, doc_content)
            except APIError as e:
                print('模型文档上传失败：{}'.format(e))
                sys.exit(1)
            print('模型文档上传结果：')
            print(json.dumps(result.json(), indent=4, ensure_ascii=False))

        else:
            print('请输入需要预览的文档路径')
            sys.exit(1)

