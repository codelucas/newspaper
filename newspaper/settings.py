# -*- coding: utf-8 -*-
"""
Unlike configuration.py, this file is meant for static, entire project
encompassing settings, like memoization and caching file directories.
"""
__title__ = 'newspaper'
__author__ = 'Lucas Ou-Yang'
__license__ = 'MIT'
__copyright__ = 'Copyright 2014, Lucas Ou-Yang'

import logging
import os
import tempfile

from http.cookiejar import CookieJar as cj

from .version import __version__

log = logging.getLogger(__name__)

PARENT_DIRECTORY = os.path.dirname(os.path.abspath(__file__))

POPULAR_URLS = os.path.join(
    PARENT_DIRECTORY, 'resources/misc/popular_sources.txt')
USERAGENTS = os.path.join(PARENT_DIRECTORY, 'resources/misc/useragents.txt')

STOPWORDS_DIR = os.path.join(PARENT_DIRECTORY, 'resources/text')

# NLP stopwords are != regular stopwords for now...
NLP_STOPWORDS_EN = os.path.join(
    PARENT_DIRECTORY, 'resources/misc/stopwords-nlp-en.txt')

DATA_DIRECTORY = '.newspaper_scraper'

TOP_DIRECTORY = os.path.join(tempfile.gettempdir(), DATA_DIRECTORY)
if not os.path.exists(TOP_DIRECTORY):
    os.mkdir(TOP_DIRECTORY)

# Error log
LOGFILE = os.path.join(TOP_DIRECTORY, 'newspaper_errors_%s.log' % __version__)
MONITOR_LOGFILE = os.path.join(
    TOP_DIRECTORY, 'newspaper_monitors_%s.log' % __version__)

# Memo directory (same for all concur crawlers)
MEMO_FILE = 'memoized'
MEMO_DIR = os.path.join(TOP_DIRECTORY, MEMO_FILE)

if not os.path.exists(MEMO_DIR):
    os.mkdir(MEMO_DIR)

# category and feed cache
CF_CACHE_DIRECTORY = 'feed_category_cache'
ANCHOR_DIRECTORY = os.path.join(TOP_DIRECTORY, CF_CACHE_DIRECTORY)

if not os.path.exists(ANCHOR_DIRECTORY):
    os.mkdir(ANCHOR_DIRECTORY)

TRENDING_URL = 'http://www.google.com/trends/hottrends/atom/feed?pn=p1'
