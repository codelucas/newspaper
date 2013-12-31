.. _install:

Installation
============

This part of the documentation covers the installation of newspaper.
The first step to using any software package is getting it properly installed.

Distribute & Pip
----------------

Installing newspaper is simple with `pip <http://www.pip-installer.org/>`_::


    $ pip install newspaper

    IMPORTANT
    If you know for sure that you'll use the natural language features,
    nlp(), you must download some separate nltk corpora below.
    You must download everything in python 2.6 - 2.7!

    $ curl https://raw.github.com/codelucas/newspaper/master/download_corpora.py | python2.7


Get the Code
------------

newspaper is actively developed on GitHub, where the code is
`always available <https://github.com/codelucas/newspaper>`_.

You can clone the public repository::

    git clone git://github.com/codelucas/newspaper.git

Once you have a copy of the source, you can embed it in your Python package,
or install it into your site-packages easily::

    $ python setup.py install

