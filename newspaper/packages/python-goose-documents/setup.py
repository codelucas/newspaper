# -*- coding: utf-8 -*-
"""\
This is a python port of "Goose" orignialy licensed to Gravity.com
under one or more contributor license agreements.  See the NOTICE file
distributed with this work for additional information
regarding copyright ownership.

Python port was written by Xavier Grangier for Recrutae

Gravity.com licenses this file
to you under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance
with the License.  You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import os
from setuptools import setup, find_packages
from imp import load_source

version = load_source("version", os.path.join("goose", "version.py"))

CLASSIFIERS = [
    'Development Status :: 4 - Beta',
    'Environment :: Other Environment',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: Apache Software License',
    'Operating System :: MacOS :: MacOS X',
    'Operating System :: POSIX',
    'Operating System :: Microsoft :: Windows',
    'Programming Language :: Python',
    'Programming Language :: Python',
    'Programming Language :: Python :: 2',
    'Programming Language :: Python :: 2.6',
    'Programming Language :: Python :: 2.7',
    'Topic :: Internet',
    'Topic :: Utilities',
    'Topic :: Software Development :: Libraries :: Python Modules']

description = "Html Content / Article Extractor, web scrapping"

# read long description
try:
    with open(os.path.join(os.path.dirname(__file__), 'README.rst')) as f:
        long_description = f.read()
except:
    long_description = description

setup(name='goose-extractor',
    version=version.__version__,
    description=description,
    long_description=long_description,
    keywords='scrapping, extractor, web scrapping',
    classifiers=CLASSIFIERS,
    author='Xavier Grangier',
    author_email='grangier@gmail.com',
    url='https://github.com/grangier/python-goose',
    license='Apache',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=['Pillow', 'lxml', 'cssselect', 'jieba', 'beautifulsoup', 'nltk'],
    test_suite="tests"
)
