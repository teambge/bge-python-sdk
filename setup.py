import sys

if sys.version_info.major <= 2:
    reload(sys)
    sys.setdefaultencoding("UTF-8")

import setuptools

with open('requirements.txt') as f:
    install_requires = [line.strip() for line in f]

setuptools.setup(
    install_requires=install_requires
)
