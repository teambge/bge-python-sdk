# BGE 开放平台 Makefile 工具

PYTHON=`which python`

install:
	$(PYTHON) setup.py install

# 构建源码包
build: wheel
	$(PYTHON) setup.py build sdist

# 构建 wheel 包
wheel:
	$(PYTHON) setup.py bdist_wheel

# 单元测试
test:
	chmod +x ./test_env.sh; \
	./test_env.sh

upload-test:
	pip install twine; \
	twine upload --repository-url https://test.pypi.org/legacy/ dist/*

upload:
	pip install twine; \
	twine upload dist/*

clean:
	rm -rf build dist *.egg-info __pycache__ \
		   bgesdk/__pycache__ bgesdk/*.pyc bgesdk/management/*.pyc \
		   bgesdk/commands/*.pyc tests/__pycache__ tests/*.pyc

.PHONY: test upload upload-test build wheel install clean
