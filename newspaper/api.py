# -*- coding: utf-8 -*-
"""
"""
__title__ = 'newspaper'
__author__ = 'Lucas Ou-Yang'
__license__ = 'MIT'
__copyright__ = 'Copyright 2014, Lucas Ou-Yang'

from .packages.feedparser import feedparser
from .source import Source
from .article import Article
from .settings import POPULAR_URLS, TRENDING_URL
from .configuration import Configuration
from .mthreading import NewsPool
from .configuration import Configuration

def build(url=u'', config=None):
    """
    returns a constructed source object without
    downloading or parsing the articles
    """
    config = Configuration() if not config else config
    url = url or '' # empty string precedence over None
    valid_href = ('://' in url) and (url[:4] == 'http')

    if not valid_href:
        print 'ERR: provide a valid url'
        return None

    s = Source(url, config)
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
