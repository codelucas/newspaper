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

Keeping Html of main body article
---------------------------------

Keeping the html of just an article's body text is helpbut because it allows you 
to retain some of the semantic information in the html. Also it will help if you 
end up displaying the extracted article somehow.

Here is how to do so:

.. code-block:: pycon

    >>> from newspaper import Article

    >>> a = Article('http://www.cnn.com/2014/01/12/world/asia/north-korea-charles-smith/index.html'
        , keep_article_html=True)

    >>> a.download()
    >>> a.parse()

    >>> a.article_html
    u'<div> \n<p><strong>(CNN)</strong> -- Charles Smith insisted Sunda...'

Adding new languages
--------------------

Newspaper is an ever-growing and adding support for new languages is quite easy, 
especially if it is a Latin-based language.

To add support for a latin language, first find a `stopwords`_ file for it. Place the
file in `newspaper/resources/text/stopwords-<COUNTRY_CODE_GOES_HERE>`. Refer to 
`this article`_ for a guide on country codes.

Then, send a pull request and wait for the author to merge and add ur langauge 
into the api.

For non-latin languages, usually there are added complexities, so I will update
this portion of the docs in the future.

.. _`this article`: http://www.iso.org/iso/country_names_and_code_elements
.. _`stopwords`: http://en.wikipedia.org/wiki/Stop_words

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

Parameters and Configurations
-----------------------------

Newspaper provides two api's for users to configure their ``Article`` and 
``Source`` objects. One is via named parameter passing **recommended** and
the other is via ``Config`` objects. 

Here are some named parameter passing examples:

.. code-block:: pycon

    >>> import newspaper
    >>> from newspaper import Article, Source

    >>> cnn = newspaper.build('http://cnn.com', language='en', memoize_articles=False)

    >>> article = Article(url='http://cnn.com/french/...', language='fr', fetch_images=False)
    
    >>> cnn = Source(url='http://latino.cnn.com/...', language='es', request_timeout=10, 
                                                                number_threads=20)


Here are some examples of how Config objects are passed.

.. code-block:: pycon

    >>> import newspaper
    >>> from newspaper import Config, Article, Source

    >>> config = Config()
    >>> config.memoize_articles = False

    >>> cbs_paper = newspaper.build('http://cbs.com', config)

    >>> article_1 = Article(url='http://espn/2013/09/...', config)

    >>> cbs_paper = Source('http://cbs.com', config)


Here is a full list of the configuration options:

``keep_article_html``, default False, "set to True if you want to preserve html of body text"

``MIN_WORD_COUNT``, default 300, "num of word tokens in article text"

``MIN_SENT_COUNT``, default 7, "num of sentence tokens"

``MAX_TITLE``, default 200, "num of chars in article title"

``MAX_TEXT``, default 100000, "num of chars in article text"

``MAX_KEYWORDS``, default 35, "num of keywords in article"

``MAX_AUTHORS``, default 10, "num of author names in article"

``MAX_SUMMARY``, default 5000, "num of chars of the summary"

``MAX_FILE_MEMO``, default 20000, "python setup.py sdist bdist_wininst upload"

``parser_class``, default 'lxml', "lxml vs soup"

``memoize_articles``, default True, "cache and save articles run after run"

``fetch_images``, default True, "set this to false if you don't care about getting images"

``image_dimension_ration``, default 16/9.0, "max ratio for height/width, we ignore if greater"

``language``, default 'en', "run ``newspaper.languages()`` to see available options."

``browser_user_agent``, default 'newspaper/%s' % __version__

``request_timeout``, default 7

``number_threads``, default 10, "number of threads when mthreading"

``verbose``, default False, "turn this on when debugging"

You may notice other config options in the ``newspaper/configuration.py`` file,
however, they are private, **please do not toggle them**.

Caching
-------

TODO

Specifications
--------------

Here, we will define exactly *how* newspaper handles a lot of the data extraction.

TODO
