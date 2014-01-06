Newspaper: Article scraping & curation
======================================

.. image:: https://badge.fury.io/py/newspaper.png
    :target: http://badge.fury.io/py/newspaper
        :alt: Latest version

Inspired by `requests`_ for its **simplicity** and powered by `lxml`_ for its **speed**; *newspaper*
is a Python 2 library for extracting & curating articles from the web.

Newspaper wants to change the way people handle article extraction with a new, more precise
layer of abstraction. Newspaper caches whatever it can for speed. *Also, everything is in unicode*.

Please refer to `The Documentation`_ for a quickstart tutorial!

A Glance:
---------

.. code-block:: pycon

    >>> import newspaper

    >>> cnn_paper = newspaper.build('http://cnn.com')

    >>> for article in cnn_paper.articles:
    >>>     print article.url
    u'http://www.cnn.com/2013/11/27/justice/tucson-arizona-captive-girls/'
    u'http://www.cnn.com/2013/12/11/us/texas-teen-dwi-wreck/index.html'
    ...

    >>> for category in cnn_paper.category_urls():
    >>>     print category

    u'http://lifestyle.cnn.com'
    u'http://cnn.com/world'
    u'http://tech.cnn.com'
    ...

.. code-block:: pycon

    >>> article = cnn_paper.articles[0]

.. code-block:: pycon

    >>> article.download()

    >>> article.html
    u'<!DOCTYPE HTML><html itemscope itemtype="http://...'

.. code-block:: pycon

    >>> article.parse()

    >>> article.authors
    [u'Leigh Ann Caldwell', 'John Honway']

    >>> article.text
    u'Washington (CNN) -- Not everyone subscribes to a New Year's resolution...'

.. code-block:: pycon

    >>> article.nlp()

    >>> article.keywords
    ['New Years', 'resolution', ...]

    >>> article.summary
    u'The study shows that 93% of people ...'

Documentation
-------------

Check out `The Documentation`_ for full and detailed guides using newspaper.

Features
--------

- News url identification
- Text extraction from html
- Keyword extraction from text
- Summary extraction from text
- Author extraction from text
- Top image extraction from html
- All image extraction from html
- Multi-threaded article download framework
- Google trending terms extraction

Get it now
----------

Installing newspaper is simple with `pip <http://www.pip-installer.org/>`_
However, you will run into (fixable) issues if you are trying to install in a virtualenv on ubuntu or any other debian system.

If you are not using ubuntu or debian, install with the following:

::

    $ pip install newspaper

    $ curl https://raw.github.com/codelucas/newspaper/master/download_corpora.py | python2.7


If you are, install using the following:

::

    $ apt-get install libxml2-dev libxslt-dev

    $ easy_install lxml  # NOT PIP
    
    $ pip install newspaper 

    $ curl https://raw.github.com/codelucas/newspaper/master/download_corpora.py | python2.7


It is also important to note that the line ``$ curl https://raw.github.com/codelucas/newspaper/master/download_corpora.py | python2.7`` is not needed unless you need the natural language, ``nlp()`` features like keywords and summarization.

If you are using ubuntu and are still running into gcc compile errors when installing lxml, try installing
``libxslt1-dev`` instead of ``libxslt-dev``.

Todo List
---------

- Add a "follow_robots.txt" option in the config object.
- Bake in the CSSSelect and BeautifulSoup dependencies

.. _`Quickstart guide`: https://newspaper.readthedocs.org/en/latest/
.. _`The Documentation`: http://newspaper.readthedocs.org
.. _`lxml`: http://lxml.de/
.. _`requests`: http://docs.python-requests.org/en/latest/
