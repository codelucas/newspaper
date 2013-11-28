# -*- coding: utf-8 -*-

import random
import logging
import os

from cookielib import CookieJar as cj

VERSION = '0.0.1'

PARENT_DIR = os.path.dirname(os.path.abspath(__file__))
POP_URLS_FILEN = os.path.join(PARENT_DIR, 'source/popular_urls.txt')

DATA_DIR = '.newspaper_scraper'
TOPDIR = os.path.join(os.path.expanduser("~"), DATA_DIR)

if not os.path.exists(TOPDIR):
    os.mkdir(TOPDIR)

# Error log
LOGFILE = os.path.join(TOPDIR, 'newspaper_errors_%s.log' % VERSION)
M_LOGFILE =  os.path.join(TOPDIR, 'newspaper_monitors_%s.log' % VERSION)

# Memo directory (same for all concur crawlers)
MEMO_FILE = 'memoized'
MEMODIR = os.path.join(TOPDIR, MEMO_FILE)

if not os.path.exists(MEMODIR):
    os.mkdir(MEMODIR)

# category and feed cache
CFDIR = 'feed_category_cache'
ANCHOR_DIR = os.path.join(TOPDIR, CFDIR)

if not os.path.exists(ANCHOR_DIR):
    os.mkdir(ANCHOR_DIR)

USERAGENT = 'newspaper/%s' % VERSION

KEYW_STOPWORDS = {
    'monday':True,
    'tuesday':True,
    'wednesday':True,
    'thursday':True,
    'friday':True,
    'saturday':True,
    'sunday':True,

    'january':True,
    'february':True,
    'april':True,
    'may':True,
    'june':True,
    'july':True,
    'august':True,
    'september':True,
    'october':True,
    'november':True,
    'december':True,

    'use':True,
    'questions':True,
    'action':True,
}

TRENDING_URL = 'http://www.google.com/trends/hottrends/atom/feed?pn=p1'

MAX_FILE_MEMO = 20000
