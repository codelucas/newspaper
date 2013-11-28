Newspaper: Article scraping & curation
======================================

.. image:: https://badge.fury.io/py/textblob.png
    :target: http://badge.fury.io/py/textblob
        :alt: Latest version

.. image:: https://travis-ci.org/sloria/TextBlob.png?branch=master
    :target: https://travis-ci.org/sloria/TextBlob
        :alt: Travis-CI

.. image:: https://pypip.in/d/textblob/badge.png
    :target: https://crate.io/packages/textblob/
        :alt: Number of PyPI downloads

.. image:: https://badge.waffle.io/sloria/TextBlob.png?label=Ready
    :target: https://waffle.io/sloria/TextBlob
        :alt: Issues in Ready


Homepage: `https://textblob.readthedocs.org/ <https://textblob.readthedocs.org/>`_

Inspired by `requests` for its simplicity and powered by `lxml` for its speed; `Newspaper` is a Python 2 library
for extracting articles from the web and curating text (NLP) for keywords, summaries, authors, etc.
Newspaper utilizes async io and caching for speed. Everything is in unicode :)


.. code-block:: python

    import newspaper

    # Watch Newspaper extract out all recent articles on CNN, no ads or boilerplate

    cnn_paper = newspaper.build('http://cnn.com')

    print cnn_paper.articles[0].title
    # u'Police: 3 sisters imprisoned in Tucson home, tortured with music'

    print cnn_paper.articles[0].keywords
    # [u'music', u'Tucson', ... ]

    print cnn_paper.articles[0].text
    # u'Three sisters who were imprisoned for possibly ... a constant barrage ...'

    print cnn_paper.articles[0].summary
    # u'... imprisoned for possibly ... a constant barrage ...'

    print cnn_paper.articles[0].top_img   # <-- Using Reddit's thumbnail alg to find top img
    # u'http://some.cdn.com/3424hfd4565sdfgdg436/

    print cnn_paper.articles[0].authors
    # [u'Eliott C. McLaughlin', u'Some CoAuthor']

    print cnn_paper.length() # <- Number of articles just crawled, we can limit this
    # 3020

    print cnn_paper.category_urls
    # [u'http://lifestyle.cnn.com', u'http://cnn.com/world', u'http://tech.cnn.com' ...]

    print cnn_paper.feeds_urls
    # [u'http://rss.cnn.com/rss/cnn_crime.rss', ...] <-- We crawl CNN and search for feeds on every category page

    print cnn_paper.brand
    # u'cnn'


    # Alternatively, you can use newspaper's lower level Article api

    from newspaper import Article

    article = Article('http://www.cnn.com/2013/11/27/travel/weather-thanksgiving/index.html?hpt=hp_t1')
    article.download()
    article.parse()

    print article.url # Note that the argument is gone
    # http://www.cnn.com/2013/11/27/travel/weather-thanksgiving/index.html

    print article.summary
    # u'blah blah blah'

Newspaper stands on the giant shoulders of `lxml`_, `goose-extractor`_, `nltk`_, and `requests`_.

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
    $ curl https://raw.github.com/sloria/TextBlob/master/download_corpora.py | python

Examples
--------

See more examples at the `Quickstart guide`_.

.. _`Quickstart guide`: https://textblob.readthedocs.org/en/latest/quickstart.html#quickstart


Documentation
-------------

Full documentation is available at https://textblob.readthedocs.org/.

Requirements
------------

- Python >= 2.6 and <= 2.7*

License
-------

MIT licensed. See the bundled `LICENSE <https://github.com/sloria/TextBlob/blob/master/LICENSE>`_ file for more details.

.. _pattern: http://www.clips.ua.ac.be/pattern
.. _NLTK: http://nltk.org/
