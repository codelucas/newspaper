.. _advanced:

Advanced
========

This section of the docs shows how to do some useful but advanced things
with newspaper.

Multi-threading article downloads
---------------------------------

**Downloading articles one at a time is slow.** But spamming a single news source
like cnn.com with tons of threads or with ASYNC-IO will cause rate limiting
and also doing that is very mean.

We solve this problem by allocating 1-2 threads per news source to both greatly
speed up the download time while being respectful.

.. code-block:: pycon

    >>> import newspaper
    >>> from newspaper import news_pool

    >>> slate_paper = newspaper.build('http://slate.com')
    >>> tc_paper = newspaper.build('http://techcrunch.com')
    >>> espn_paper = newspaper.build('http://espn.com')

    >>> papers = [slate_paper, tc_paper, espn_paper]
    >>> news_pool.set(papers, threads_per_source=2) # (3*2) = 6 threads total
    >>> news_pool.join()

    At this point, you can safely assume that download() has been
    called on every single article for all 3 sources.

    >>> print slate_paper.articles[10].html
    u'<html> ...'

Explicitly building a news source
---------------------------------

Instead of using the ``newspaper.build(..)`` api, we can take one step lower
into newspaper's ``Source`` api.

.. code-block:: pycon

    >>> from newspaper import Source
    >>> cnn_paper = Source('http://cnn.com')

    >>> print cnn_paper.size() # no articles, we have not built the source
    0

    >>> cnn_paper.build()
    >>> print cnn_paper.size()
    3100

Note the ``build()`` method above. You may go lower level and de-abstract it
for absolute control over how your sources are constructed.

.. code-block:: pycon

    >>> cnn_paper = Source('http://cnn.com')
    >>> cnn_paper.download()
    >>> cnn_paper.parse()
    >>> cnn_paper.set_categories()
    >>> cnn_paper.download_categories()
    >>> cnn_paper.parse_categories()
    >>> cnn_paper.set_feeds()
    >>> cnn_paper.download_feeds()
    >>> cnn_paper.generate_articles()

    >>> print cnn_paper.size()
    3100

And voila, we have mimic'd the ``build()`` method. In the above sequence,
every method is dependant on the method above it. Stop whenever you wish.

Config objects
--------------

You may configure your Source and Article objects however you want via
the ``Config`` object. Config objects are passed into the constructors
of ``Source()``, ``Article()``, and ``newspaper.build()`` initialization
methods.

Here are some examples of how Config objects are passed.

.. code-block:: pycon

    >>> import newspaper
    >>> from newspaper import Config, Article, Source

    >>> config = Config()

    >>> cbs_paper = newspaper.build('http://cbs.com', config)

    >>> article_1 = Article(url='http://espn/2013/09/...', config)

    >>> cbs_paper = Source('http://cbs.com', config)

Here are some examples of how to precisely modify a Config object.

.. code-block:: pycon

    >>> config = Config()
    >>> config.is_memoize_articles = False   # default True
    >>> config.verbose = True                # default False
    >>> config.request_timeout = 10          # default 7
    >>> config.parser_class = 'soup'         # default 'lxml'
    >>> config.target_language = 'es'        # default 'en'

    >>> cbs_paper = newspaper.build('http://cbs.com', config)

There are *many* more configuration options. You may view them in the
``newspaper/configuration.py`` file.

Caching
-------

TODO

Specifications
--------------

Here, we will define exactly *how* newspaper handles a lot of the data extraction.

TODO