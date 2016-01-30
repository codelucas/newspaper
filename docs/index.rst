Newspaper: Article scraping & curation
======================================

Release v0.1.2. :ref:`(Installation) <install>`.

Inspired by `requests`_ for its simplicity and powered by `lxml`_ for its speed.

    "Newspaper is an amazing python library for extracting & curating articles."
    -- `tweeted by`_ Kenneth Reitz, Author of `requests`_

    "Newspaper delivers Instapaper style article extraction." -- `The Changelog`_

.. _`tweeted by`: https://twitter.com/kennethreitz/status/419520678862548992
.. _`The Changelog`: http://thechangelog.com/

**We support 10+ languages and everything is in unicode!**

.. code-block:: pycon

    >>> import newspaper
    >>> newspaper.languages()

    Your available langauges are:
    input code      full name

      ar              Arabic
      ru              Russian
      nl              Dutch
      de              German
      en              English
      es              Spanish
      fr              French
      he              Hebrew
      it              Italian
      ko              Korean
      no              Norwegian
      pt              Portuguese
      sv              Swedish
      hu              Hungarian
      fi              Finnish
      da              Danish
      zh              Chinese
      id              Indonesian
      vi              Vietnamese

A Glance:
---------

.. code-block:: pycon

    >>> import newspaper

    >>> cnn_paper = newspaper.build('http://cnn.com')

    >>> for article in cnn_paper.articles:
    >>>     print(article.url)
    u'http://www.cnn.com/2013/11/27/justice/tucson-arizona-captive-girls/'
    u'http://www.cnn.com/2013/12/11/us/texas-teen-dwi-wreck/index.html'
    ...

    >>> for category in cnn_paper.category_urls():
    >>>     print(category)

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

    >>> print(a.text[:150])
    香港行政长官梁振英在各方压力下就其大宅的违章建
    筑（僭建）问题到立法会接受质询，并向香港民众道歉。
    梁振英在星期二（12月10日）的答问大会开始之际在其
    演说中道歉，但强调他在违章建筑问题上没有隐瞒的意
    图和动机。 一些亲北京阵营议员欢迎梁振英道歉，
    且认为应能获得香港民众接受，但这些议员也质问梁振英有

    >>> print(a.title)
    港特首梁振英就住宅违建事件道歉


If you are certain that an *entire* news source is in one language, **go ahead and use the same api :)**

.. code-block:: pycon

    >>> import newspaper
    >>> sina_paper = newspaper.build('http://www.sina.com.cn/', language='zh')

    >>> for category in sina_paper.category_urls():
    >>>     print(category)
    u'http://health.sina.com.cn'
    u'http://eladies.sina.com.cn'
    u'http://english.sina.com'
    ...

    >>> article = sina_paper.articles[0]
    >>> article.download()
    >>> article.parse()

    >>> print(article.text)
    新浪武汉汽车综合 随着汽车市场的日趋成熟，传统的“集
    全家之力抱得爱车归”的全额购车模式已然过时，另一种轻
    松的新兴 车模式――金融购车正逐步成为时下消费者购买
    爱车最为时尚的消费理 念，他们认为，这种新颖的购车模
    式既能在短期内
    ...

    >>> print(article.title)
    两年双免0手续0利率 科鲁兹掀背金融轻松购_武汉车市_武汉
    汽车网_新浪汽车_新浪网


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


User Guide
----------

.. toctree::
   :maxdepth: 2

   user_guide/install
   user_guide/quickstart
   user_guide/advanced

.. toctree::
   :maxdepth: 1

   user_guide/contributors


.. _`lxml`: http://lxml.de/
.. _`nltk`: http://nltk.org/
.. _`requests`: https://github.com/kennethreitz/requests
.. _`goose`: https://github.com/grangier/python-goose


LICENSE
-------

Authored and maintained by `Lucas Ou-Yang`_.

Newspaper uses a lot of `python-goose's`_ parsing code. View their license `here`_.

Please feel free to `email & contact me`_ if you run into issues or just would like
to talk about the future of this library and news extraction in general!

.. _`Lucas Ou-Yang`: http://lucasou.com
.. _`email & contact me`: mailto:lucasyangpersonal@gmail.com
.. _`python-goose's`: https://github.com/grangier/python-goose
.. _`here`: https://github.com/codelucas/newspaper/blob/master/GOOSE-LICENSE.txt
