.. _install:

Installation
============

This part of the documentation covers the installation of newspaper.
The first step to using any software package is getting it properly installed.

Distribute & Pip
----------------

Installing newspaper is simple with `pip <http://www.pip-installer.org/>`_.
However, you will run into fixable issues if you are trying to install on ubuntu.


**If you are on ubuntu**, install using the following:

::

    # Pre-req's for lxml
    $ apt-get install libxml2-dev libxslt-dev

    # For PIL to recognize .jpg
    $ sudo apt-get install libjpeg-dev zlib1g-dev libpng12-dev  

    $ easy_install lxml # NOT PIP

    $ pip install newspaper 

    $ curl https://raw.github.com/codelucas/newspaper/master/download_corpora.py | python2.7


**If you are on OSX**, install using the following:

::

    # Pre-req's for lxml
    $ brew install libxml2 libxslt # or the equiv command in macports

    $ pip install lxml

    # For PIL to recognize .jpg
    $ brew install libtiff libjpeg webp little-cms2 # or the equiv with macports

    $ pip install newspaper 

    $ curl https://raw.github.com/codelucas/newspaper/master/download_corpora.py | python2.7


**If you are neither using ubuntu nor mac**, install with the following:

::

    # You will most likely need to install the following libraries via your
    # package manager
    # for lxml: libxml2-dev libxslt-dev
    # for PIL: libjpeg-dev zlib1g-dev libpng12-dev  

    $ pip install newspaper

    $ curl https://raw.github.com/codelucas/newspaper/master/download_corpora.py | python2.7


It is also important to note that the line

::

    $ curl https://raw.github.com/codelucas/newspaper/master/download_corpora.py | python2.7


is not needed unless you need the natural language, ``nlp()`` features like keywords extraction and summarization.

If you are using ubuntu and are still running into gcc compile errors when installing lxml, try installing
``libxslt1-dev`` instead of ``libxslt-dev``.

Get the Code
------------

Newspaper is actively developed on GitHub, where the code is
`always available <https://github.com/codelucas/newspaper>`_.

You can clone the public repository::

    git clone git://github.com/codelucas/newspaper.git

Once you have a copy of the source, you can embed it in your Python package,
or install it into your site-packages easily::

    $ python setup.py install

