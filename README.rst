Newspaper: Article scraping & curation
======================================

.. image:: https://badge.fury.io/py/textblob.png
    :target: http://badge.fury.io/py/textblob
        :alt: Latest version

.. image:: https://pypip.in/d/textblob/badge.png
    :target: https://crate.io/packages/textblob/
        :alt: Number of PyPI downloads


Homepage: `https://newspaper.readthedocs.org/ <https://newspaper.readthedocs.org/>`_

Inspired by ``requests`` for its simplicity and powered by ``lxml`` for its speed; **newspaper** is a Python 2 library
for extracting & curating articles from the web in a 3 step process defined below.

Newspaper utilizes async io and caching for speed. *Also, everything is in unicode :)*
There are two API's available. Low level ``article`` objects and ``newspaper`` objects.

The core 3 methods are:
* ``download()`` retrieves the html, with non blocking io whenever possible.
* ``parse()`` extracts the body text, authors, titles, etc from the html.
* ``nlp()`` extracts the summaries, keywords, sentiments from the text.

.. code-block:: pycon

    >>> import newspaper

    >>> cnn_paper = newspaper.build('http://cnn.com')

    >>> for article in cnn_paper.articles: 
    >>>     print article.url
    u'http://www.cnn.com/2013/11/27/justice/tucson-arizona-captive-girls/'
    u'http://www.cnn.com/2013/12/11/us/texas-teen-dwi-wreck/index.html?hpt=hp_t1'
    u'http://www.cnn.com/2013/12/07/us/life-pearl-harbor/?iref=obinsite'
    ...

    >>> print cnn_paper.category_urls    
    [u'http://lifestyle.cnn.com', u'http://cnn.com/world', u'http://tech.cnn.com' ...]

    >>> print cnn_paper.feeds_urls  
    [u'http://rss.cnn.com/rss/cnn_crime.rss', u'http://rss.cnn.com/rss/cnn_tech.rss', ...] 
    
    # download html for all articles **concurrently**, via async io
    >>> cnn_paper.download() 

    >>> print cnn_paper.articles[0].html
    u'<!DOCTYPE HTML><html itemscope itemtype="http://...'

    >>> print cnn_paper.articles[5].html 
    u'<!DOCTYPE HTML><html itemscope itemtype="http://...'

    # parse html for text, authors, etc on a per article basis **not concurrent**
    >>> cnn_paper.articles[0].parse() 

    >>> print cnn_paper.articles[0].text
    u'Three sisters who were imprisoned for possibly ... a constant barrage ...'

    >>> print cnn_paper.articles[0].top_img  
    u'http://some.cdn.com/3424hfd4565sdfgdg436/

    >>> print cnn_paper.articles[0].authors
    [u'Eliott C. McLaughlin', u'Some CoAuthor']
    
    >>> print cnn_paper.articles[0].title
    u'Police: 3 sisters imprisoned in Tucson home, tortured with music'

    # extract keywords, summaries, etc on a per article basis **not concurrent**
    >>> cnn_paper.articles[0].nlp()

    >>> print cnn_paper.articles[0].summary
    u'... imprisoned for possibly ... a constant barrage ...'

    >>> print cnn_paper.articles[0].keywords
    [u'music', u'Tucson', ... ]

    >>> print cnn_paper.brand
    u'cnn'

    ## Alternatively, parse and nlp all articles together. Will take a while...
    ## for article in cnn_paper.articles:
    ##     article.parse() 
    ##     article.nlp()

Alternatively, you may use newspaper's lower level Article api.

.. code-block:: pycon

    >>> from newspaper import Article

    >>> article = Article('http://cnn.com/2013/11/27/travel/weather-thanksgiving/index.html')

    >>> article.download()      ## download html

    >>> print article.html 
    u'<!DOCTYPE HTML><html itemscope itemtype="http://...'
    
    >>> article.parse()         ## parse out body text, title, authors, etc

    >>> print article.text
    u'The purpose of this article is to introduce to you all how to...'

    >>> print article.authors
    [u'Martha Stewart', u'Bob Smith']

    >>> article.nlp()           ## extract out summary, keywords, sentiment, etc
           
    >>> print article.summary
    u'...and so that is how a great Thanksgiving meal is cooked...'

    >>> print article.keywords
    [u'Thanksgiving', u'holliday', u'Walmart', ...]

``nlp()`` is expensive, as is ``parse()``, make sure you actually need them before calling them on all of your articles! In some cases, if you just need urls, even ``download()`` is not necessary.

Newspaper stands on the giant shoulders of `lxml`_, `nltk`_, and `requests`_.

.. _`lxml`: https://textblob.readthedocs.org/en/latest/quickstart.html#quickstart
.. _`nltk`: https://textblob.readthedocs.org/en/latest/quickstart.html#quickstart
.. _`requests`: https://textblob.readthedocs.org/en/latest/quickstart.html#quickstart

Features
--------

- Noun phrase extraction
- Part-of-speech tagging
- Sentiment analysis
- Classification (Naive Bayes, Decision Tree)
- Language translation and detection powered by Google Translate
- Tokenization (splitting text into words and sentences)
- Word and phrase frequencies
- Parsing
- `n`-grams
- Word inflection (pluralization and singularization) and lemmatization
- Spelling correction
- JSON serialization
- Add new models or languages through extensions
- WordNet integration

Get it now
----------
::

    $ pip install newspaper

Examples
--------

See more examples at the `Quickstart guide`_.

.. _`Quickstart guide`: https://newspaper.readthedocs.org/en/latest/quickstart.html#quickstart


Documentation
-------------

Full documentation is available at https://newspaper.readthedocs.org/.

Requirements
------------

- Python >= 2.6 and <= 2.7*

License
-------

MIT licensed. See the bundled `LICENSE <https://github.com/sloria/TextBlob/blob/master/LICENSE>`_ file for more details.
