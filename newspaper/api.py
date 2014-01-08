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
from .utils import print_available_languages

def build(url=u'', config=None):
    """
    Returns a constructed source object without
    downloading or parsing the articles.
    """
    config = config or Configuration() # Order matters
    url = url or ''                    # Empty string precedence over None
    valid_href = ('://' in url) and (url[:4] == 'http')

    if not valid_href:
        print 'ERR: provide a valid url'
        return None

    s = Source(url, config)
    s.build()
    return s

def build_article(url=u''):
    """
    Returns a constructed article object without
    downloading or parsing.
    """
    url = url or '' # empty string precedence over None
    a = Article(url)
    return a

def languages():
    """
    Returns a list of the supported languages.
    """
    print_available_languages()

def popular_urls():
    """
    Returns a list of pre-extracted popular source urls.
    """
    with open(POPULAR_URLS) as f:
        urls = ['http://' + u.strip() for u in f.readlines()]
        return urls

def hot():
    """
    Returns a list of hit terms via google trends.
    """
    try:
        listing = feedparser.parse(TRENDING_URL)['entries']
        trends = [item['title'] for item in listing]
        return trends
    except Exception, e:
        print 'ERR hot terms failed!', str(e)
        return None
