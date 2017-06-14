# -*- coding: utf-8 -*-
"""
Lucas Ou 2014 -- http://lucasou.com

Setup guide: http://guide.python-distribute.org/creation.html
python setup.py sdist bdist_wininst upload
"""
import sys
import os


def hilight(input_string):
    if sys.stdout.isatty():
        # only print escape sequences for TTL interfaces
        return input_string
    attr = []
    attr.append('31')  # red
    attr.append('1')   # bold
    return '\x1b[%sm%s\x1b[0m' % (';'.join(attr), input_string)


try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


if sys.argv[-1] == 'publish':
    os.system('python setup.py sdist upload')  # bdist_wininst
    sys.exit()


# This *must* run early. Please see this API limitation on our users:
# https://github.com/codelucas/newspaper/issues/155
# But, this can't run before the `os.system('python setup.py sdist upload')` publish
# command because publishing only works in python3 for my MANIFEST.in format
if sys.version_info[0] == 3 and sys.argv[-1] != 'upload':
    warning_string = hilight(
        'WARNING! You are attempting to install newspaper\'s '
        'python2 repository on python3. PLEASE RUN '
        '`$ pip3 install newspaper3k` for python3 or '
        '`$ pip install newspaper` for python2')
    sys.exit(warning_string)

packages = [
    'newspaper',
]


with open('requirements.txt') as f:
    required = f.read().splitlines()


setup(
    name='newspaper',
    version='0.1.0.7',
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
