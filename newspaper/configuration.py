# -*- coding: utf-8 -*-
"""
This class holds configuration objects, which can be thought of
as settings.py but dynamic and changing for whatever parent object
holds them. For example, pass in a config object to an Article
object, Source object, or even network methods, and it just works.
"""
__title__ = 'newspaper'
__author__ = 'Lucas Ou-Yang'
__license__ = 'MIT'
__copyright__ = 'Copyright 2014, Lucas Ou-Yang'

import logging

from .parsers import Parser
from .text import (StopWords, StopWordsArabic, StopWordsChinese,
                   StopWordsKorean, StopWordsHindi, StopWordsJapanese)
from .version import __version__

log = logging.getLogger(__name__)


class Configuration(object):
    def __init__(
        self,
        MIN_WORD_COUNT=300,
        MIN_SENT_COUNT=7,
        MAX_TITLE=200,
        MAX_TEXT=100000,
        MAX_KEYWORDS=35,
        MAX_AUTHORS=10,
        MAX_SUMMARY=5000,
        MAX_SUMMARY_SENT=5,
        MAX_FILE_MEMO=20000,
        memoize_articles=True,
        fetch_images=True,
        image_dimension_ration=16/9.0,
        follow_meta_refresh=False,
        keep_article_html=False,
        http_success_only=True,
        language='en',
        browser_user_agent='newspaper/{}'.format(__version__),
        headers=None,
        request_timeout=7,
        proxies=None,
        number_threads=10,
        verbose=False
    ):
        """Initalize a custom configuration.

        :param MIN_WORD_COUNT: Number of word tokens in text
        :param MIN_SENT_COUNT: Number of sentence tokens
        :param MAX_TITLE: Number of chars
        :param MAX_TEXT: Number of chars
        :param MAX_KEYWORDS: Number of strings in list
        :param MAX_AUTHORS: Number strings in list
        :param MAX_SUMMARY:  Number of chars
        :param MAX_SUMMARY_SENT: Number of sentences
        :param MAX_FILE_MEMO: Max number of URLS we cache for each news source
        :param memoize_articles: Whether to cache and save articles run after run
        :param fetch_images: Set this to False if you don't care about getting images
        :param image_dimension_ration:
        :param follow_meta_refresh: Follow meta refresh redirect when downloading
        :param keep_article_html: Keep the HTML of just the main article body
        :param http_success_only: Raise for non-200 responses (e.g. 404 page), using request's :function:`raise_for_status`
        :param language: Language, default English ('en')
        :param browser_user_agent: User-Agent string, default 'newspaper/{__version__}'
        :param headers: Headers to send with GET requests
        :param request_timeout: Total request timeout
        :param proxies: Proxy to use in GET requests
        :param number_threads: Number of threads used with multithreaded requests
        :param verbose: Set to True for increased verbosity in debugging
        """

        # TODO: Have a separate ArticleConfig and SourceConfig extend this!

        self.MIN_WORD_COUNT = MIN_WORD_COUNT
        self.MIN_SENT_COUNT = MIN_SENT_COUNT
        self.MAX_TITLE = MAX_TITLE
        self.MAX_TEXT = MAX_TEXT
        self.MAX_KEYWORDS = MAX_KEYWORDS
        self.MAX_AUTHORS = MAX_AUTHORS
        self.MAX_SUMMARY = MAX_SUMMARY
        self.MAX_SUMMARY_SENT = MAX_SUMMARY_SENT
        self.MAX_FILE_MEMO = MAX_FILE_MEMO

        self.memoize_articles = memoize_articles
        self.fetch_images = fetch_images
        self.image_dimension_ration = image_dimension_ration
        self.follow_meta_refresh = follow_meta_refresh
        self.keep_article_html = keep_article_html
        self.http_success_only = http_success_only

        self.browser_user_agent = browser_user_agent
        self.headers = headers or {}
        self.request_timeout = request_timeout
        self.proxies = proxies or {}
        self.number_threads = number_threads
        self.verbose = verbose

        self._language = language

        # Don't toggle this variable, done internally
        self.use_meta_language = True

        # Unique stopword classes for oriental languages, don't toggle
        self.stopwords_class = StopWords

        self.thread_timeout_seconds = 1
        self.ignored_content_types_defaults = {}
        # Set this to False if you want to recompute the categories
        # *every* time you build a `Source` object
        # TODO: Actually make this work
        # self.use_cached_categories = True

    def get_language(self):
        return self._language

    def del_language(self):
        raise Exception('wtf are you doing?')

    def set_language(self, language):
        """Language setting must be set in this method b/c non-occidental
        (western) languages require a separate stopwords class.
        """
        if not language or len(language) != 2:
            raise Exception("Your input language must be a 2 char language code, \
                for example: english-->en \n and german-->de")

        # If explicitly set language, don't use meta
        self.use_meta_language = False

        # Set oriental language stopword class
        self._language = language
        self.stopwords_class = self.get_stopwords_class(language)

    language = property(get_language, set_language,
                        del_language, "language prop")

    @staticmethod
    def get_stopwords_class(language):
        sw = {
            'ko': StopWordsKorean,
            'hi': StopWordsHindi,
            'zh': StopWordsChinese,
            # Persian and Arabic Share an alphabet
            # There is a persian parser https://github.com/sobhe/hazm,
            # but nltk is likely sufficient.
            'ar': StopWordsArabic,
            'fa': StopWordsArabic,
            'ja': StopWordsJapanese
        }
        return sw.get(language, StopWords)

    @staticmethod
    def get_parser():
        return Parser


class ArticleConfiguration(Configuration):
    pass


class SourceConfiguration(Configuration):
    pass
