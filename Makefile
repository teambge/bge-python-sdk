# BGE 开放平台 Makefile 工具

PYTHON=`which python`

install:
	$(PYTHON) setup.py install

# 构建源码包
build: test
	$(PYTHON) setup.py build sdist

# 构建 wheel 包
wheel: test
	$(PYTHON) setup.py bdist_wheel

# 单元测试
test:
	pytest

# 初始化文档目录
initdoc:
	mkdir docs; \
	cd docs/; \
	sphinx-quickstart --ext-autodoc --ext-viewcode --ext-ifconfig

# 生成 api 文档
apidoc:
	sphinx-apidoc -f -o ./docs/api/ ./bgesdk/; \
	cd docs/; \
	make html

clean:
	rm -rf build dist *.egg-info docs/_build __pycache__ \
		   bgesdk/__pycache__ bgesdk/*.pyc \
		   tests/__pycache__ tests/*.pyc

.PHONY: test initdoc apidoc build wheel install clean