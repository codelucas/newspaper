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
                   StopWordsKorean)
from .version import __version__

log = logging.getLogger(__name__)


class Configuration(object):

    def __init__(self):
        """
        Modify any of these Article / Source properties
        TODO: Have a seperate ArticleConfig and SourceConfig extend this!
        """
        self.MIN_WORD_COUNT = 300  # num of word tokens in text
        self.MIN_SENT_COUNT = 7    # num of sentence tokens
        self.MAX_TITLE = 200       # num of chars
        self.MAX_TEXT = 100000     # num of chars
        self.MAX_KEYWORDS = 35     # num of strings in list
        self.MAX_AUTHORS = 10      # num strings in list
        self.MAX_SUMMARY = 5000    # num of chars

        # max number of urls we cache for each news source
        self.MAX_FILE_MEMO = 20000

        # Cache and save articles run after run
        self.memoize_articles = True

        # Set this to false if you don't care about getting images
        self.fetch_images = True
        self.image_dimension_ration = 16/9.0

        # Don't toggle this variable, done internally
        self.use_meta_language = True

        # You may keep the html of just the main article body
        self.keep_article_html = False

        # English is the fallback
        self._language = 'en'

        # Unique stopword classes for oriental languages, don't toggle
        self.stopwords_class = StopWords

        self.browser_user_agent = 'newspaper/%s' % __version__
        self.request_timeout = 7
        self.number_threads = 10

        self.verbose = False  # for debugging

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
        (western) langauges require a seperate stopwords class.
        """
        if not language or len(language) != 2:
            raise Exception("Your input language must be a 2 char langauge code, \
                for example: english-->en \n and german-->de")

        # If explicitly set langauge, don't use meta
        self.use_meta_language = False

        # Set oriental language stopword class
        self._language = language
        self.stopwords_class = self.get_stopwords_class(language)

    language = property(get_language, set_language,
                        del_language, "langauge prop")

    def get_stopwords_class(self, language):
        if language == 'ko':
            return StopWordsKorean
        elif language == 'zh':
            return StopWordsChinese
        elif language == 'ar':
            return StopWordsArabic
        return StopWords

    def get_parser(self):
        return Parser


class ArticleConfiguration(Configuration):
    pass


class SourceConfiguration(Configuration):
    pass
