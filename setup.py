#!/bin/python2.7
# -*- coding: utf-8 -*-
"""
Lucas Ou 2014 -- http://lucasou.com

Setup guide: http://guide.python-distribute.org/creation.html
python setup.py sdist bdist_wininst upload
"""

import sys
import os
import codecs

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


packages = [
    'newspaper',
]


if sys.argv[-1] == 'publish':
    os.system('python setup.py sdist bdist_wininst upload')
    sys.exit()


with open('requirements.txt') as f:
    required = f.read().splitlines()


with codecs.open('README.rst', 'r', 'utf-8') as f:
    readme = f.read()


setup(
    name='newspaper3k',
    version='0.1.0',
    description='Simplified python article discovery & extraction.',
    long_description=readme,
    author='Lucas Ou-Yang',
    author_email='lucasyangpersonal@gmail.com',
    url='https://github.com/codelucas/newspaper/',
    packages=packages,
    include_package_data=True,
    install_requires=required,
    license='MIT',
    zip_safe=False,
)
