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

# 初始化文档目录
initdoc:
	mkdir docs; \
	cd docs/; \
	sphinx-quickstart --ext-autodoc --ext-viewcode --ext-ifconfig

# 生成 api 文档
apidoc:
	pip install sphinx sphinx_rtd_theme; \
	sphinx-apidoc -f -o ./docs/api/ ./bgesdk/; \
	cd docs/; \
	make html

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