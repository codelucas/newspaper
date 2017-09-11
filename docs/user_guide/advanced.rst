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

    >>> print(slate_paper.articles[10].html)
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

The lxml (dom object) and top_node (chunk of dom that contains our 'Article') are also
cached incase users would like to use them.

Access **after parsing()** with:

.. code-block:: pycon

    >>> a.download()
    >>> a.parse()
    >>> a.clean_dom
    <lxml object ...  >

    >>> a.clean_top_node
    <lxml object ...  >


Adding new languages
--------------------

First, please reference this file and read from the highlighted line all the way
down to the end of the file.

`https://github.com/codelucas/newspaper/blob/master/newspaper/text.py#L57 <https://github.com/codelucas/newspaper/blob/master/newspaper/text.py#L57>`_

One aspect of our text extraction algorithm revolves around counting the number of
**stopwords** present in a text. Stopwords are: *some of the most common, short
function words, such as the, is, at, which, and on* in a language.

Reference this line to see it in action:
`https://github.com/codelucas/newspaper/blob/master/newspaper/extractors.py#L668 <https://github.com/codelucas/newspaper/blob/master/newspaper/extractors.py#L668>`_

**So for latin languages**, it is pretty basic. We first provide a list of
stopwords in ``stopwords-<language-code>.txt`` form. We then take some input text and
tokenize it into words by splitting the white space. After that we perform some
bookkeeping and then proceed to count the number of stopwords present.

**For non-latin languages**, as you may have noticed in the code above, we need to
tokenize the words in a different way, *splitting by whitespace simply won't work for
languages like Chinese or Arabic*. For the Chinese language we are using a whole new
open source library called *jieba* to split the text into words. For arabic we are
using a special nltk tokenizer to do the same job.

**So, to add full text extraction to a new (non-latin) language, we need:**

1. Push up a stopwords file in the format of ``stopwords-<2-char-language-code>.txt``
in ``newspaper/resources/text/.``

2. Provide a way of splitting/tokenizing text in that foreign language into words.
`Here are some examples for Chinese, Arabic, English <https://github.com/codelucas/newspaper/blob/master/newspaper/text.py#L105>`_

**For latin languages:**

1. Push up a stopwords file in the format of ``stopwords-<2-char-language-code>.txt``
in ``newspaper/resources/text/.`` and we are done!

**Finally, add the new language to the list of available languages in the following files:**

* README.rst
* docs/index.rst
* docs/user_guide/quickstart.rst
* newspaper/utils.py


Explicitly building a news source
---------------------------------

Instead of using the ``newspaper.build(..)`` api, we can take one step lower
into newspaper's ``Source`` api.

.. code-block:: pycon

    >>> from newspaper import Source
    >>> cnn_paper = Source('http://cnn.com')

    >>> print(cnn_paper.size()) # no articles, we have not built the source
    0

    >>> cnn_paper.build()
    >>> print(cnn_paper.size())
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

    >>> print(cnn_paper.size())
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

``http_success_only``, default True, "set to False to capture non 2XX responses as well"

``MIN_WORD_COUNT``, default 300, "num of word tokens in article text"

``MIN_SENT_COUNT``, default 7, "num of sentence tokens"

``MAX_TITLE``, default 200, "num of chars in article title"

``MAX_TEXT``, default 100000, "num of chars in article text"

``MAX_KEYWORDS``, default 35, "num of keywords in article"

``MAX_AUTHORS``, default 10, "num of author names in article"

``MAX_SUMMARY``, default 5000, "num of chars of the summary"

``MAX_SUMMARY_SENT``, default 5, "num of sentences in summary"

``MAX_FILE_MEMO``, default 20000, "python setup.py sdist bdist_wininst upload"

``memoize_articles``, default True, "cache and save articles run after run"

``fetch_images``, default True, "set this to false if you don't care about getting images"

``follow_meta_refresh``, default False, "follows a redirect url in a meta refresh html tag"

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
