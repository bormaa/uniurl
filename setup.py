from setuptools import setup, find_packages
import os
import re

# Read version from __version__.py
with open(os.path.join("uniurl", "__version__.py"), "r", encoding="utf-8") as f:
    content = f.read()
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", content, re.M)
    author_match = re.search(r"^__author__ = ['\"]([^'\"]*)['\"]", content, re.M)
    email_match = re.search(r"^__author_email__ = ['\"]([^'\"]*)['\"]", content, re.M)
    
    if not version_match:
        raise RuntimeError("Unable to find version string.")
    if not author_match:
        raise RuntimeError("Unable to find author string.")
    if not email_match:
        raise RuntimeError("Unable to find author email string.")

version = version_match.group(1)
author = author_match.group(1)
author_email = email_match.group(1)

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="uniurl",
    version=version,
    author=author,
    author_email=author_email,
    description="This package takes input from dirsearch tool to remove unused and unworking links",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/bormaa/uniurl",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    install_requires=[
        "requests>=2.25.0",
        "fake-useragent>=1.4.0"
    ],
    entry_points={
        'console_scripts': [
            'uniurl=uniurl.cli:main',
        ],
    },
) 