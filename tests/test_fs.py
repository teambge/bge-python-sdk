#-*- coding: utf-8 -*-

from bgesdk.fs import FileItem

import pytest


class TestFS:

    def test_file_item(self):
        inst = FileItem('hello.txt', 'Hello world')
        assert isinstance(inst, FileItem)