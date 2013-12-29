# -*- coding: utf-8 -*-

from .packages.feedparser import feedparser
from .source import Source
from .article import Article
from .settings import POPULAR_URLS, TRENDING_URL
from .configuration import Configuration
from .mthreading import NewsPool

def build(url=u'', is_memo=True, verbose=False):
    """
    returns a constructed source object without
    downloading or parsing the articles
    """
    url = url or '' # empty string precedence over None
    valid_href = ('://' in url) and (url[:4] == 'http')

    if not valid_href:
        print 'ERR: provide a valid url'
        return None

    test_configs = Configuration()
    test_configs.verbose = verbose
    test_configs.is_memoize_articles = is_memo
    s = Source(url, config=test_configs)
    s.build()
    return s

def build_article(url=u''):
    """
    returns a constructed article object without
    downloading or parsing
    """
    url = url or '' # empty string precedence over None
    a = Article(url)
    return a

def popular_urls():
    """
    returns a list of pre-extracted popular source urls
    """
    with open(POPULAR_URLS) as f:
        urls = ['http://' + u.strip() for u in f.readlines()]
        return urls

def hot():
    """
    returns a list of hit terms via google trends
    """
    try:
        listing = feedparser.parse(TRENDING_URL)['entries']
        trends = [item['title'] for item in listing]
        return trends
    except Exception, e:
        print 'ERR hot terms failed!', str(e)
        return None
