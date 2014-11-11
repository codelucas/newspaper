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
]

# The following libs are bundled in
# ---------------------------------
# 'feedparser'
# 'tldextract==1.2.2'
# 'jieba'

requires = [
    'lxml',
    'requests',
    'nltk',
    'Pillow',
    'cssselect',
    'BeautifulSoup'
]

setup(
    name='newspaper',
    version='0.0.8',
    description='Simplified python article discovery & extraction.',
    author='Lucas Ou-Yang',
    author_email='lucasyangpersonal@gmail.com',
    url='https://github.com/codelucas/newspaper/',
    packages=packages,
    include_package_data=True,
    install_requires=requires,
    license='',
    zip_safe=False,
)
