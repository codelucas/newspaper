#!/bin/python2.7

import os
import sys

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

packages = [
    'newspaper'
]

requires = []

with open('README.rst') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

setup(
    name='newspaper',
    version='0.0.1',
    description='Python HTTP for Humans.',
    long_description=readme + '\r\n',
    author='Lucas Ou-Yang',
    author_email='lucasyangpersonal@gmail.com',
    url='http://codelucas.com',
    packages=packages,
    package_data={'': ['LICENSE', 'NOTICE'], 'newspaper': []},
    package_dir={'newspaper': 'newspaper'},
    include_package_data=True,
    install_requires=requires,
    license=license,
    zip_safe=False,
    # classifiers=(
    #    'Development Status :: 5 - Production/Stable',
    #    'Intended Audience :: Developers',
    #    'Natural Language :: English',
    #    'License :: OSI Approved :: Apache Software License',
    #    'Programming Language :: Python',
    #    'Programming Language :: Python :: 2.6',
    #    'Programming Language :: Python :: 2.7',
    #    'Programming Language :: Python :: 3',
    #    'Programming Language :: Python :: 3.3',

    # ),
)
