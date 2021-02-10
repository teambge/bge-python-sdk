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
	chmod +x ./test_env.sh; \
	./test_env.sh

# 启动 HTTP 服务器查看文档
py3server:
	cd docs; \
	python3 -m http.server 4000

# 启动 HTTP 服务器查看文档
py2server:
	cd docs; \
	python -m SimpleHTTPServer 4000

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

.PHONY: test py3server py2server upload upload-test build wheel install clean
