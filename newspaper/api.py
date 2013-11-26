# -*- coding: utf-8 -*-

from .source import Source
from .article import Article
from .settings import POP_URLS_FN

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

    with open(POP_URLS_FN) as f:
        urls = ['http://'+u.strip() for u in f.readlines()]
        return urls

