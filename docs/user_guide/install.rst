.. _install:

Installation
============

This part of the documentation covers the installation of newspaper.
The first step to using any software package is getting it properly installed.

Distribute & Pip
----------------
Installing newspaper is simple with `pip <http://www.pip-installer.org/>`_.
However, you will run into fixable issues if you are trying to install on ubuntu.

**If you are on Debian / Ubuntu**, install using the following:

- Python development version, needed for Python.h::

    $ sudo apt-get install python-dev

- lxml requirements::

    $ sudo apt-get install libxml2-dev libxslt-dev

- For PIL to recognize .jpg images::

    $ sudo apt-get install libjpeg-dev zlib1g-dev libpng12-dev  

- Install the distribution via pip::

    $ pip install newspaper 

- Download NLP related corpora::

    $ curl https://raw.githubusercontent.com/codelucas/newspaper/master/download_corpora.py | python2.7

**If you are on CentOS** and use Japanese language support, install using the following:

- Install ``mecab`` - Japanese morphological analyzer::

    $ rpm -ivh http://packages.groonga.org/centos/groonga-release-1.1.0-1.noarch.rpm

    $ yum install mecab mecab-devel mecab-ipadic

    $ pip install mecab-python3

- Install ``mecab-ipadic-NEologd`` - Neologism dictionary for MeCab (Optional)::

    $ mkdir ~/src && cd ~/src && git clone --depth 1 https://github.com/neologd/mecab-ipadic-neologd.git

    $ cd ~/src/mecab-ipadic-neologd && ./bin/install-mecab-ipadic-neologd -n

    $ curl https://raw.githubusercontent.com/codelucas/newspaper/master/download_corpora.py | python3

**If you are on OSX**, install using the following, you may use both homebrew or macports:

::

    $ brew install libxml2 libxslt

    $ brew install libtiff libjpeg webp little-cms2

    $ pip install newspaper 

    $ curl https://raw.githubusercontent.com/codelucas/newspaper/master/download_corpora.py | python2.7


**Otherwise**, install with the following:

NOTE: You will still most likely need to install the following libraries via your package manager

- PIL: ``libjpeg-dev`` ``zlib1g-dev`` ``libpng12-dev``
- lxml: ``libxml2-dev`` ``libxslt-dev``
- Python Development version: ``python-dev``

Note that the Python3 package name is ``newspaper3k`` while our Python2
package name is ``newspaper``.

::

    $ pip install newspaper3k

    $ curl https://raw.githubusercontent.com/codelucas/newspaper/master/download_corpora.py | python2.7

Get the Code
------------

Newspaper is actively developed on GitHub, where the code is
`always available <https://github.com/codelucas/newspaper>`_.

You can clone the public repository::

    git clone git://github.com/codelucas/newspaper.git

Once you have a copy of the source, you can embed it in your Python package,
or install it into your site-packages easily::

    $ pip install -r requirements.txt
    $ python setup.py install

Feel free to give our testing suite a shot::

    $ python tests/unit_tests.py
