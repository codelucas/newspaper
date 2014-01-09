Newspaper: Article scraping & curation
=======================================

.. image:: https://badge.fury.io/py/newspaper.png
    :target: http://badge.fury.io/py/newspaper
        :alt: Latest version

*Newspaper* is a Python 2 library for extracting & curating articles from the web. It is inspired by `requests`_ for its simplicity and powered by `lxml`_ for its speed.

**We support 10+ languages and everything is in unicode!**

.. code-block:: pycon

    >>> import newspaper     
    >>> newspaper.languages()

    Your available langauges are:
    input code      full name

      ar              Arabic
      de              German
      en              English
      es              Spanish
      fr              French
      it              Italian
      ko              Korean
      no              Norwegian
      pt              Portugease
      sv              Swedish
      zh              Chinese


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

    >>> article.top_image
    u'http://someCDN.com/blah/blah/blah/file.png'

    >>> article.movies
    [u'http://youtube.com/path/to/link.com', ...]

.. code-block:: pycon

    >>> article.nlp()

    >>> article.keywords
    ['New Years', 'resolution', ...]

    >>> article.summary
    u'The study shows that 93% of people ...'


Newspaper has *seamless* language extraction and detection.
If no language is specified, Newspaper will attempt to auto detect a language.

.. code-block:: pycon

    >>> from newspaper import Article
    >>> url = 'http://www.bbc.co.uk/zhongwen/simp/chinese_news/2012/12/121210_hongkong_politics.shtml'

    >>> a = Article(url, language='zh') # Chinese
    
    >>> a.download()
    >>> a.parse()

    >>> print a.text[:150]
    香港行政长官梁振英在各方压力下就其大宅的违章建筑（僭建）问题到立法会接受质询，并向香港民众道歉。
    梁振英在星期二（12月10日）的答问大会开始之际在其演说中道歉，但强调他在违章建筑问题上没有隐瞒的意图和动机。
    一些亲北京阵营议员欢迎梁振英道歉，且认为应能获得香港民众接受，但这些议员也质问梁振英有
   
    >>> print a.title
    港特首梁振英就住宅违建事件道歉


If you are certain that an *entire* news source is in one language, **go ahead and use the same api :)**

.. code-block:: pycon

    >>> import newspaper
    >>> sina_paper = newspaper.build('http://www.sina.com.cn/', langauge='zh')

    >>> for category in sina_paper.category_urls():
    >>>     print category
    u'http://health.sina.com.cn'
    u'http://eladies.sina.com.cn'
    u'http://english.sina.com'
    ...

    >>> article = sina_paper.articles[0]
    >>> article.download()
    >>> article.parse()

    >>> print article.text
    新浪武汉汽车综合 随着汽车市场的日趋成熟，传统的“集全家之力抱得爱车归”的全额购车模式已然过时，另一种轻松的新兴
    车模式――金融购车正逐步成为时下消费者购买爱车最为时尚的消费理念，他们认为，这种新颖的购车模式既能在短期内
    ...

    >>> print article.title
    两年双免0手续0利率 科鲁兹掀背金融轻松购_武汉车市_武汉汽车网_新浪汽车_新浪网


Documentation
-------------

Check out `The Documentation`_ for full and detailed guides using newspaper.

Features
--------

- Works in 10+ languages (English, Chinese, German, Arabic, ...)
- Multi-threaded article download framework
- News url identification
- Text extraction from html
- Top image extraction from html
- All image extraction from html
- Keyword extraction from text
- Summary extraction from text
- Author extraction from text
- Google trending terms extraction

Get it now
----------

Installing newspaper is simple with `pip <http://www.pip-installer.org/>`_.
However, you will run into fixable issues if you are trying to install on ubuntu.

**If you are not using ubuntu**, install with the following:

::

    $ pip install newspaper

    $ curl https://raw.github.com/codelucas/newspaper/master/download_corpora.py | python2.7


**If you are**, install using the following:

::

    $ apt-get install libxml2-dev libxslt-dev

    $ easy_install lxml  # NOT PIP
    
    $ pip install newspaper 

    $ curl https://raw.github.com/codelucas/newspaper/master/download_corpora.py | python2.7


It is also important to note that the line 

::

    $ curl https://raw.github.com/codelucas/newspaper/master/download_corpora.py | python2.7


is not needed unless you need the natural language, ``nlp()``, features like keywords extraction and summarization.

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

