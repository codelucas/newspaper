#!/bin/python2.7

import os
import sys

from .newspaper import VERSION

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

packages = [
    'newspaper'
]

requires = [
    'goose-extractor==1.0.2',
    'requests==2.0.1',
    'lxml==3.2.4',
    'tldextract==1.2.2'
]

with open('README.md') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

with open('HISTORY.md') as f:
    history = f.read()

setup(
    name='newspaper',
    version=VERSION,
    description='Python article extraction for humans.',
    long_description=readme + '\r\n' + history,
    author='Lucas Ou-Yang',
    author_email='lucasyangpersonal@gmail.com',
    url='http://codelucas.com',
    packages=packages,
    package_data={'': ['LICENSE'], 'newspaper': []},
    package_dir={'newspaper': 'newspaper'},
    include_package_data=True,
    install_requires=requires,
    license=license,
    zip_safe=False,
)
