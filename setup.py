# -*- coding: utf-8 -*-
"""
Lucas Ou 2014 -- http://lucasou.com

Setup guide: http://guide.python-distribute.org/creation.html
python setup.py sdist bdist_wininst upload
"""
import sys
import os


# This *must* run early. Please see this API limitation on our users:
# https://github.com/codelucas/newspaper/issues/155
if sys.version_info[0] == 3:
    sys.exit('WARNING! You are attempting to install newspaper\'s '
             'python2 repository on python3. PLEASE RUN '
             '`$ pip3 install newspaper3k` for python3 or '
             '`$ pip install newspaper` for python2')


try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


if sys.argv[-1] == 'publish':
    os.system('python setup.py sdist upload')  # bdist_wininst
    sys.exit()


packages = [
    'newspaper',
]


with open('requirements.txt') as f:
    required = f.read().splitlines()


setup(
    name='newspaper',
    version='0.0.9.9',
    description='Simplified python article discovery & extraction.',
    author='Lucas Ou-Yang',
    author_email='lucasyangpersonal@gmail.com',
    url='https://github.com/codelucas/newspaper/',
    packages=packages,
    include_package_data=True,
    install_requires=required,
    license='MIT',
    zip_safe=False,
)
