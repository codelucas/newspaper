#!/bin/python2.7
# -*- coding: utf-8 -*-
"""
Lucas Ou 2014 -- http://lucasou.com

Setup guide: http://guide.python-distribute.org/creation.html
python setup.py sdist bdist_wininst upload
"""
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

packages = [
    'newspaper',
    'newspaper.packages',
    'newspaper.packages.tldextract',
    'newspaper.packages.feedparser',
]

required = []
with open('requirements.txt') as f:
    required = f.read().splitlines()

"""
requires = [
    'lxml==3.3.5',
    'jieba==0.35',
    'requests==2.3.0',
    'nltk==2.0.4',
    'Pillow==2.5.1',
    'cssselect==0.9.1',
    'BeautifulSoup==3.2.1'
]
"""

setup(
    name='newspaper',
    version='0.0.9',
    description='Simplified python article discovery & extraction.',
    author='Lucas Ou-Yang',
    author_email='lucasyangpersonal@gmail.com',
    url='https://github.com/codelucas/newspaper/',
    packages=packages,
    include_package_data=True,
    install_requires=required,
    license='',
    zip_safe=False,
)
