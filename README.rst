Newspaper: Article scraping & curation
======================================

.. image:: https://badge.fury.io/py/newspaper.png
    :target: http://badge.fury.io/py/newspaper
        :alt: Latest version

.. image:: https://pypip.in/d/newspaper/badge.png
    :target: https://crate.io/packages/newspaper/
        :alt: Number of PyPI downloads


Inspired by ``requests`` for its simplicity and powered by ``lxml`` for its speed; **newspaper**
is a Python 2 library for extracting & curating articles from the web.

Newspaper wants to change the way people handle ``article extraction`` with ``a new, more precise
layer of abstraction``.  Visit our homepage at: `Newspaper Docs`_.

Newspaper utilizes lxml and caching for speed. *Also, everything is in unicode*

.. code-block:: pycon

    >>> import newspaper

    >>> cnn_paper = newspaper.build('http://cnn.com') # ~15 seconds 

    >>> for article in cnn_paper.articles: # filters urls 
    >>>     print article.url 

    u'http://www.cnn.com/2013/11/27/justice/tucson-arizona-captive-girls/'
    u'http://www.cnn.com/2013/12/11/us/texas-teen-dwi-wreck/index.html'
    u'http://www.cnn.com/2013/12/07/us/life-pearl-harbor/'
    ...

    >>> print cnn_paper.size() # number of articles
    3100 

    >>> print cnn_paper.category_urls() 
    [u'http://lifestyle.cnn.com', u'http://cnn.com/world', u'http://tech.cnn.com' ...]

    >>> print cnn_paper.feed_urls() 
    [u'http://rss.cnn.com/rss/cnn_crime.rss', u'http://rss.cnn.com/rss/cnn_tech.rss', ...] 

The first step is to ``download()`` an article.    
    
.. code-block:: pycon

    >>> first_article = cnn_paper.articles[0]

    >>> first_article.download()

    >>> print first_article.html # html fetched from download()
    u'<!DOCTYPE HTML><html itemscope itemtype="http://...'
    
    # we have not downloaded this article yet, it will fail
    >>> print cnn_paper.articles[7].html 
    u'' 

We may also extract meaningful content from the html, like authors, body-text..
You must called ``download()`` on the article before calling ``parse()``.

.. code-block:: pycon

    >>> first_article.parse()  

    >>> print first_article.text
    u'Three sisters who were imprisoned for possibly...'

    >>> print first_article.top_img  
    u'http://some.cdn.com/3424hfd4565sdfgdg436/

    >>> print first_article.authors
    [u'Eliott C. McLaughlin', u'Some CoAuthor']
    
    >>> print first_article.title
    u'Police: 3 sisters imprisoned in Tucson home'

Finally, you may extract out natural language properties from the text. You must have
called both ``download()`` and ``parse()`` the article before calling ``nlp()``.

.. code-block:: pycon

    >>> first_article.nlp() # must be on an already parse()'ed article

    >>> print first_article.summary
    u'...imprisoned for possibly a constant barrage...'

    >>> print first_article.keywords
    [u'music', u'Tucson', ... ]

    >>> print cnn_paper.articles[100].nlp() # fail, not been downloaded yet
    Traceback (...
       ...
    ArticleException: You must parse an article before you try to..


Some other news-source level functionality

.. code-block:: pycon

    >>> print cnn_paper.brand
    u'cnn'

    >>> print cnn_paper.description
    u'CNN.com delivers the latest breaking news and information on the latest...'

    >>> newspaper.hot()[:5] # top google trending terms
    ['Ned Vizzini', Brian Boitano', Crossword Inventor', 'Alex and Sierra', 'Claire Davis']

    >>> newspaper.popular_urls() 
    ['http://slate.com', 'http://cnn.com', 'http://huffingtonpost.com', ...]

^ Just a few friendly suggestions if you forget the popular news sites!


**IMPORTANT**
    
Unless told not to in the constructor via the ``is_memo_articles`` param (default true), 
newspaper automatically caches all category, feed, and article urls. 
This is both to avoid duplicate articles and for speed.

.. code-block:: pycon

    Suppose the above code has already been run on the cnn domain once. Previous
    article urls are cached and dupes are removed so we only get new articles.

    >>> import newspaper

    >>> cnn_paper = newspaper.build('http://cnn.com')
    >>> cnn_paper.size()
    60    # since we last ran build(), cnn published 60 new articles!

    >>> # If you'd like to opt out of memoization, init newspapers with

    >>> cnn_paper2 = newspaper.build('http://cnn.com', is_memo=False)
    >>> cnn_paper2.size()
    3100


Alternatively, you may use newspaper's lower level Article api.

.. code-block:: pycon

    >>> from newspaper import Article

    >>> article = Article('http://cnn.com/2013/11/27/travel/weather-thanksgiving/index.html')
    >>> article.download()

    >>> print article.html 
    u'<!DOCTYPE HTML><html itemscope itemtype="http://...'
    
    >>> article.parse()

    >>> print article.text
    u'The purpose of this article is to introduce...'

    >>> print article.authors
    [u'Martha Stewart', u'Bob Smith']

    >>> print article.top_img
    u'http://some.cdn.com/3424hfd4565sdfgdg436/

    >>> print article.title
    u'Thanksgiving Weather Guide Travel ...'

    >>> article.nlp()
           
    >>> print article.summary
    u'...and so that's how a Thanksgiving meal is cooked...'

    >>> print article.keywords
    [u'Thanksgiving', u'holliday', u'Walmart', ...]


``nlp()`` is expensive, as is ``parse()``, make sure you actually need them before calling them on
all of your articles! In some cases, if you just need urls, even ``download()`` is not necessary.

Newspaper stands on the giant shoulders of `lxml`_, `nltk`_, and `requests`_. Newspaper also uses much of
`goose`_'s code internally. 

.. _`lxml`: http://lxml.de/
.. _`nltk`: http://nltk.org/
.. _`requests`: http://docs.python-requests.org/en/latest/
.. _`goose`: https://github.com/grangier/python-goose

Features
--------

- News url identification
- Text extraction from html
- Keyword extraction from text
- Summary extraction from text
- Author extraction from text
- Top Image & All image extraction from html
- Top Google trending terms 
- News article extraction from news domain
- Quick html downloads via multithreading

Get it now
----------
::

    $ pip install newspaper

    ### IMPORTANT ###
    # If you KNOW for sure you will use the natural language features, nlp(), you must
    # download some seperate nltk corpora below, it may take a while!

    $ curl https://raw.github.com/codelucas/newspaper/master/download_corpora.py | python2.7

Examples TODO
-------------

See more examples at the `Quickstart guide`_.


Documentation
-------------

Full documentation is available at `Newspaper Docs`_.

Requirements
------------

- Python >= 2.6 and <= 2.7*

License
-------

MIT licensed. 
Also, view the LICENSE for our internally used libraries at: `goose-license`_

.. _`goose-license`: https://github.com/codelucas/newspaper/tree/master/newspaper/packages/python-goose-documents
.. _`Quickstart guide`: https://newspaper.readthedocs.org/en/latest/quickstart.html#quickstart
.. _`Newspaper Docs`: http://newspaper.readthedocs.org
