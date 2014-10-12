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

::

    # Python development version, needed for Python.h
    $ apt-get install python-dev

    # lxml requirements
    $ apt-get install libxml2-dev libxslt-dev

    # For PIL to recognize .jpg images
    $ sudo apt-get install libjpeg-dev zlib1g-dev libpng12-dev  

    $ pip install newspaper 

    $ curl https://raw.githubusercontent.com/codelucas/newspaper/master/download_corpora.py | python2.7


**If you are on OSX**, install using the following, you may use both homebrew or macports:

::

    # lxml requirements
    $ brew install libxml2 libxslt

    # For PIL to recognize .jpg images
    $ brew install libtiff libjpeg webp little-cms2

    $ pip install newspaper 

    $ curl https://raw.githubusercontent.com/codelucas/newspaper/master/download_corpora.py | python2.7


**Otherwise**, install with the following:

::

    # You will most likely need to install the following libraries via your
    # package manager
    #
    # PIL: libjpeg-dev zlib1g-dev libpng12-dev  
    # lxml: libxml2-dev libxslt-dev
    # Python Development version: python-dev

    $ pip install newspaper

    $ curl https://raw.githubusercontent.com/codelucas/newspaper/master/download_corpora.py | python2.7


It is also important to note that the line 

::

    $ curl https://raw.githubusercontent.com/codelucas/newspaper/master/download_corpora.py | python2.7


is not needed unless you need the natural language, ``nlp()``, features like keywords 
extraction and summarization.


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
