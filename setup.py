#!/bin/python2.7

"""
Lucas Ou-Yang 2014 -- http://codelucas.com

Setup guide: http://guide.python-distribute.org/creation.html

"""
import os
import sys

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

packages = [
    'newspaper',
    'newspaper.data',
    'newspaper.packages',
    'newspaper.packages.tldextract',
    # 'newspaper.packages.tldextract.tests',
    'newspaper.packages.feedparser',
    # 'newspaper.packages.feedparser.tests'
    'newspaper.packages.goose',
    'newspaper.packages.goose.utils',
    'newspaper.packages.goose.videos',
    'newspaper.packages.goose.images',
    # 'newspaper.packages.python-goose-documents',
    'newspaper.packages.jieba',
    'newspaper.packages.jieba.posseg',
    'newspaper.packages.jieba.finalseg',
    'newspaper.packages.jieba.analyse'
]

requires = [
    'lxml==3.2.4',            # version for lxml is important
    'requests',
    'nltk',
    'Pillow',
    'cssselect',
    'BeautifulSoup'
]

# 'feedparser',
# 'tldextract==1.2.2',
# 'pil',
# 'nltk',
# 'requests==2.0.1',

try:
    with open('README.rst') as f:
        readme = f.read()
except: readme = u''

try:
    with open('LICENSE') as f:
        license = f.read()
except: license = u''

try:
    with open('HISTORY.md') as f:
        history = f.read()
except: history = u''

setup(
    name='newspaper',
    version='0.0.3',
    description='Simplified python article discovery & extraction.',
    long_description=readme + '\r\n' + history,
    author='Lucas Ou-Yang',
    author_email='lucasyangpersonal@gmail.com',
    url='https://github.com/codelucas/newspaper/', #tarball/0.0.2',
    packages=packages,
    # package_data={'': ['LICENSE'], 'newspaper': []},
    # package_dir={'newspaper': 'newspaper'},
    include_package_data=True,
    install_requires=requires,
    license=license,
    zip_safe=False,
)

