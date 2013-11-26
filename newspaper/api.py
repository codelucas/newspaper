# -*- coding: utf-8 -*-

import feedparser

from .source import Source
from .article import Article
from .settings import POP_URLS_FILEN, TRENDING_URL


def build(url=u''):
    """returns a constructed source object without
    downloading or parsing the articles"""

    url = url or '' # empty string precedence over None
    valid_href = ('://' in url) and (url[:4] == 'http')

    if not valid_href:
        print 'ERR: provide valid url'
        return None

    s = Source(url)
    return s


def build_article(url=u''):
    """returns a constructed article object without
    downloading or parsing"""

    a = Article(url)
    return a


def popular_urls():
    """returns a list of pre-extracted popular source urls"""

    with open(POP_URLS_FILEN) as f:
        urls = ['http://'+u.strip() for u in f.readlines()]
        return urls


def hot():
    """returns a list of hit terms via google trends"""

    try:
        listing = feedparser.parse(TRENDING_URL)['entries']
        trends = [item['title'] for item in listing]
        return trends
    except:
        return None