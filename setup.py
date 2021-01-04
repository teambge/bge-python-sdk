from setuptools import setup, find_packages

with open("README.md", "r") as f:
    long_description = f.read()

setup(
    name="bge-python-sdk",
    version="0.0.1",
    author="xiangji",
    author_email="xiangji@genomics.cn",
    description="BGE wpapi client",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://gitlab.genomics.cn/DTCLab/bge-platform/bge-python-sdk",
    packages=find_packages(),
)
