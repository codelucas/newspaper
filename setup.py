#!/bin/python2.7
# -*- coding: utf-8 -*-
"""
Lucas Ou-Yang 2014 -- http://codelucas.com
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
    # PYPI now uses twine for package management.
    # For this to work you must first `$ pip3 install twine`
    os.system('python3 setup.py sdist bdist_wheel')
    os.system('twine upload dist/*')
    sys.exit()


# This *must* run early. Please see this API limitation on our users:
# https://github.com/codelucas/newspaper/issues/155
if sys.version_info[0] == 2 and sys.argv[-1] not in ['publish', 'upload']:
    sys.exit('WARNING! You are attempting to install newspaper3k\'s '
             'python3 repository on python2. PLEASE RUN '
             '`$ pip3 install newspaper3k` for python3 or '
             '`$ pip install newspaper` for python2')


with open('requirements.txt') as f:
    required = f.read().splitlines()


with codecs.open('README.rst', 'r', 'utf-8') as f:
    readme = f.read()


setup(
    name='newspaper3k',
    version='0.2.8',
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
    classifiers=[
        'Programming Language :: Python :: 3',
        'Natural Language :: English',
        'Intended Audience :: Developers',
    ],
)
