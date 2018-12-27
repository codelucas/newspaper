.. _quickstart:

Quickstart
==========

Eager to get started? This page gives a good introduction in how to get started
with newspaper. This assumes you already have newspaper installed. If you do not,
head over to the :ref:`Installation <install>` section.

Building a news source
----------------------

Source objects are an abstraction of online news media websites like CNN or ESPN.
You can initialize them in two *different* ways.

Building a ``Source`` will extract its categories, feeds, articles, brand, and description for you.

You may also provide configuration parameters like ``language``, ``browser_user_agent``, and etc seamlessly. Navigate to the :ref:`advanced <advanced>` section for details.

.. code-block:: pycon

    >>> import newspaper
    >>> cnn_paper = newspaper.build('http://cnn.com')

    >>> sina_paper = newspaper.build('http://www.lemonde.fr/', language='fr')

However, if needed, you may also play with the lower level ``Source`` object as described
in the :ref:`advanced <advanced>` section.

Extracting articles
-------------------

Every news source has a set of *recent* articles.

The following examples assume that a news source has been
initialized and built.

.. code-block:: pycon

    >>> for article in cnn_paper.articles:
    >>>     print(article.url)

    u'http://www.cnn.com/2013/11/27/justice/tucson-arizona-captive-girls/'
    u'http://www.cnn.com/2013/12/11/us/texas-teen-dwi-wreck/index.html'
    ...

    >>> print(cnn_paper.size()) # cnn has 3100 articles
    3100

Article caching
---------------

By default, newspaper caches all previously extracted articles and **eliminates any
article which it has already extracted**.

This feature exists to prevent duplicate articles and to increase extraction speed.

.. code-block:: pycon

    >>> cbs_paper = newspaper.build('http://cbs.com')
    >>> cbs_paper.size()
    1030

    >>> cbs_paper = newspaper.build('http://cbs.com')
    >>> cbs_paper.size()
    2

The return value of ``cbs_paper.size()`` changes from 1030 to 2 because when we first
crawled cbs we found 1030 articles. However, on our second crawl, we eliminate all
articles which have already been crawled.

This means **2** new articles have been published since our first extraction.

You may opt out of this feature with the ``memoize_articles`` parameter.

You may also pass in the lower level``Config`` objects as covered in the :ref:`advanced <advanced>` section.

.. code-block:: pycon

    >>> import newspaper

    >>> cbs_paper = newspaper.build('http://cbs.com', memoize_articles=False)
    >>> cbs_paper.size()
    1030

    >>> cbs_paper = newspaper.build('http://cbs.com', memoize_articles=False)
    >>> cbs_paper.size()
    1030


Extracting Source categories
----------------------------

.. code-block:: pycon

    >>> for category in cnn_paper.category_urls():
    >>>     print(category)

    u'http://lifestyle.cnn.com'
    u'http://cnn.com/world'
    u'http://tech.cnn.com'
    ...

Extracting Source feeds
-----------------------

.. code-block:: pycon

    >>> for feed_url in cnn_paper.feed_urls():
    >>>     print(feed_url)

    u'http://rss.cnn.com/rss/cnn_crime.rss'
    u'http://rss.cnn.com/rss/cnn_tech.rss'
    ...

Extracting Source brand & description
-------------------------------------

.. code-block:: pycon

    >>> print(cnn_paper.brand)
    u'cnn'

    >>> print(cnn_paper.description)
    u'CNN.com delivers the latest breaking news and information on the latest...'

News Articles
-------------

Article objects are abstractions of news articles. For example, a news ``Source``
would be CNN while a news ``Article`` would be a specific CNN article.
You may reference an ``Article`` from an existing news ``Source`` or initialize
one by itself.

Referencing it from a ``Source``.

.. code-block:: pycon

    >>> first_article = cnn_paper.articles[0]

Initializing an ``Article`` by itself.

.. code-block:: pycon

    >>> from newspaper import Article
    >>> first_article = Article(url="http://www.lemonde.fr/...", language='fr')


Note the similar ``language=`` named paramater above. All the config parameters as described for ``Source`` objects also apply for ``Article`` objects! **Source and Article objects have a very similar api**.

Initializing an ``Article`` with the particular content-type ignoring.

There is option to skip loading of articles with particular content-type,
that can be useful if it is not desired to have delays because of long PDF resources.
The default html value for the particular content type can be provided and then used in order to define the actual content-type of the article

.. code-block:: pycon

    >>> from newspaper import Article
    >>> pdf_defaults = {"application/pdf": "%PDF-",
                      "application/x-pdf": "%PDF-",
                      "application/x-bzpdf": "%PDF-",
                      "application/x-gzpdf": "%PDF-"}
    >>> pdf_article = Article(url='https://www.adobe.com/pdf/pdfs/ISO32000-1PublicPatentLicense.pdf',
                                            ignored_content_types_defaults=pdf_defaults)
    >>> pdf_article.download()
    >>> print(pdf_article.html)
    %PDF-

There are endless possibilities on how we can manipulate and build articles.

Downloading an Article
----------------------

We begin by calling ``download()`` on an article. If you are interested in how to
quickly download articles concurrently with multi-threading check out the
:ref:`advanced <advanced>` section.

.. code-block:: pycon

    >>> first_article = cnn_paper.articles[0]

    >>> first_article.download()

    >>> print(first_article.html)
    u'<!DOCTYPE HTML><html itemscope itemtype="http://...'

    >>> print(cnn_paper.articles[7].html)
    u'' fail, not downloaded yet

Parsing an Article
------------------

You may also extract meaningful content from the html, like authors and body-text.
You **must** have called ``download()`` on an article before calling ``parse()``.

.. code-block:: pycon

    >>> first_article.parse()

    >>> print(first_article.text)
    u'Three sisters who were imprisoned for possibly...'

    >>> print(first_article.top_image)
    u'http://some.cdn.com/3424hfd4565sdfgdg436/

    >>> print(first_article.authors)
    [u'Eliott C. McLaughlin', u'Some CoAuthor']

    >>> print(first_article.title)
    u'Police: 3 sisters imprisoned in Tucson home'

    >>> print(first_article.images)
    ['url_to_img_1', 'url_to_img_2', 'url_to_img_3', ...]

    >>> print(first_article.movies)
    ['url_to_youtube_link_1', ...] # youtube, vimeo, etc


Performing NLP on an Article
----------------------------

Finally, you may extract out natural language properties from the text.
You **must** have called both ``download()`` and ``parse()`` on the article
before calling ``nlp()``.

**As of the current build, nlp() features only work on western languages.**

.. code-block:: pycon

    >>> first_article.nlp()

    >>> print(first_article.summary)
    u'...imprisoned for possibly a constant barrage...'

    >>> print(first_article.keywords)
    [u'music', u'Tucson', ... ]

    >>> print(cnn_paper.articles[100].nlp()) # fail, not been downloaded yet
    Traceback (...
    ArticleException: You must parse an article before you try to..


``nlp()`` is expensive, as is ``parse()``, make sure you actually need them before calling them on
all of your articles! In some cases, if you just need urls, even ``download()`` is not necessary.

Easter Eggs
-----------

Here are random but hopefully useful features! ``hot()`` returns a list of the top
trending terms on Google using a public api. ``popular_urls()`` returns a list
of popular news source urls.. In case you need help choosing a news source!

.. code-block:: pycon

    >>> import newspaper

    >>> newspaper.hot()
    ['Ned Vizzini', Brian Boitano', Crossword Inventor', 'Alex & Sierra', ... ]

    >>> newspaper.popular_urls()
    ['http://slate.com', 'http://cnn.com', 'http://huffingtonpost.com', ... ]

    >>> newspaper.languages()

    Your available languages are:
    input code      full name

      ar              Arabic
      de              German
      en              English
      es              Spanish
      fr              French
      he              Hebrew
      it              Italian
      ko              Korean
      no              Norwegian
      fa              Persian
      pl              Polish
      pt              Portuguese
      sv              Swedish
      zh              Chinese
      uk              Ukrainian
      sw              Swahili
      bg              Bulgarian
      hr              Croatian
      ro              Romanian
      sl              Slovenian
      sr              Serbian
      et              Estonian
      ja              Japanese
      be              Belarusian
      lt              Lithuanian
