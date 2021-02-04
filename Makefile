# BGE 开放平台 Makefile 工具

PYTHON=`which python`

install:
	$(PYTHON) setup.py install

# 构建源码包
build:
	$(PYTHON) setup.py build sdist

# 构建 wheel 包
wheel:
	$(PYTHON) setup.py bdist_wheel

# 单元测试
test:
	pytest

# 启动 HTTP 服务器查看文档
py3server:
	python3 -m http.server

# 启动 HTTP 服务器查看文档
py2server:
	python -m SimpleHTTPServer

upload-test:
	pip install twine; \
	twine upload --repository-url https://test.pypi.org/legacy/ dist/*

upload:
	pip install twine; \
	twine upload dist/*

clean:
	rm -rf build dist *.egg-info docs/_build __pycache__ \
		   bgesdk/__pycache__ bgesdk/*.pyc \
		   tests/__pycache__ tests/*.pyc

.PHONY: test initdoc apidoc build wheel install clean