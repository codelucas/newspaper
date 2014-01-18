# -*- coding: utf-8 -*-
"""
Wherever smart people work, doors are unlocked. -- Steve Wozniak
"""
__title__ = 'newspaper'
__author__ = 'Lucas Ou-Yang'
__license__ = 'MIT'
__copyright__ = 'Copyright 2014, Lucas Ou-Yang'

from .article import Article, ArticleException
from .source import Source

from .api import build, build_article, popular_urls, hot, languages
from .api import NewsPool, Configuration as Config

news_pool = NewsPool()

from .version import __version__

# Set default logging handler to avoid "No handler found" warnings.
import logging

try:  # Python 2.7+
    from logging import NullHandler
except ImportError:
    class NullHandler(logging.Handler):
        def emit(self, record):
            pass

logging.getLogger(__name__).addHandler(NullHandler())
