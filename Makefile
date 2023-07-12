# BGE 开放平台 Makefile 工具

PYTHON=`which python`
PIP = `which pip`

install:
	$(PYTHON) setup.py install

# 构建源码包
build:
	python -m build

# 单元测试
test:
	$(PIP) install pytest pytest-cov; \
	grep -v '^#' .env; \
	export $(grep -v '^#' .env | xargs); \
	pytest -s --cov-config=./.coveragerc --cov-report html --cov-report xml --cov=./

test-pro:
	$(PIP) install pytest pytest-cov; \
	grep -v '^#' .env-pro; \
	export $(grep -v '^#' .env-pro | xargs); \
	pytest -s --cov-config=./.coveragerc --cov-report html --cov-report xml --cov=./

upload-test:
	$(PIP) install twine; \
	twine upload --repository-url https://test.pypi.org/legacy/ dist/*

upload:
	$(PIP) install twine; \
	twine upload dist/*

changelog:
	npm run changelog

clean:
	rm -rf build \
		   dist \
		   *.egg-info __pycache__/ \
		   bgesdk/__pycache__/ \
		   bgesdk/*.pyc \
		   bgesdk/management/*.pyc \
		   bgesdk/management/__pycache__/ \
		   bgesdk/management/commands/*.pyc \
		   bgesdk/management/commands/__pycache__/ \
		   bgesdk/management/commands/api/*.pyc \
		   bgesdk/management/commands/api/__pycache__/ \
		   bgesdk/management/commands/api/commands/*.pyc \
		   bgesdk/management/commands/api/commands/__pycache__/ \
		   tests/*.pyc \
		   tests/__pycache__/ \
		   .bge/tmp/*

.PHONY: test test-pro upload upload-test build install changelog clean
