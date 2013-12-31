Newspaper: Article scraping & curation
======================================

.. image:: https://badge.fury.io/py/newspaper.png
    :target: http://badge.fury.io/py/newspaper
        :alt: Latest version

Inspired by `requests`_ for its **simplicity** and powered by `lxml`_ for its **speed**; *newspaper*
is a Python 2 library for extracting & curating articles from the web.

Newspaper wants to change the way people handle article extraction with a new, more precise
layer of abstraction. Newspaper caches whatever it can for speed. *Also, everything is in unicode*

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

    >>> first = cnn_paper.articles[0]

.. code-block:: pycon

    >>> first.download()

    >>> first.html
    u'<!DOCTYPE HTML><html itemscope itemtype="http://...'

.. code-block:: pycon

    >>> first.parse()

    >>> first.authors
    [u'Leigh Ann Caldwell', 'John Honway']

    >>> first.text
    u'Washington (CNN) -- Not everyone subscribes to a New Year's resolution...'

.. code-block:: pycon

    >>> first.nlp()

    >>> first.keywords
    ['New Years', 'resolution', ...]

    >>> first.summary
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
::

    $ pip install newspaper

    IMPORTANT
    If you know for sure that you'll use the natural language features,
    nlp(), you must download some separate nltk corpora below.
    You must download everything in python 2.6 - 2.7!

    $ curl https://raw.github.com/codelucas/newspaper/master/download_corpora.py | python2.7

Todo List
---------

- Add a "follow_robots.txt" option in the config object.
- Bake in the CSSSelect and BeautifulSoup dependencies

.. _`Quickstart guide`: https://newspaper.readthedocs.org/en/latest/
.. _`The Documentation`: http://newspaper.readthedocs.org
.. _`lxml`: http://lxml.de/
.. _`requests`: http://docs.python-requests.org/en/latest/
