#!/bin/python2.7
# -*- coding: utf-8 -*-

"""
Lucas Ou-Yang 2014 -- http://codelucas.com

Setup guide: http://guide.python-distribute.org/creation.html
python setup.py sdist bdist_wininst upload
"""
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

packages = [
    'newspaper',
    'newspaper.data',
]

requires = [
    'lxml',         # 3.2.4 tested
    'requests',
    'nltk',
    'Pillow',       # <- PIL
    'cssselect',
    'BeautifulSoup'
]

readme = ''
history = ''
_license = ''

try:
    with open('README.rst') as f:
        readme = f.read()
    with open('LICENSE') as f:
        _license = f.read()
    with open('HISTORY.md') as f:
        history = f.read()
except:
    print('')

setup(
    name='newspaper',
    version='0.0.6',
    description='Simplified python article discovery & extraction.',
    # long_description=readme+'\r\n'+history,
    author='Lucas Ou-Yang',
    author_email='lucasyangpersonal@gmail.com',
    url='https://github.com/codelucas/newspaper/',
    packages=packages,

    # TODO: Uhh, what do the following two lines mean?
    # package_data={'': ['LICENSE'], 'newspaper': []},
    # package_dir={'newspaper': 'newspaper'},

    include_package_data=True,
    install_requires=requires,
    license=_license,
    zip_safe=False,
)

