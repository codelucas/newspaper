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

from .text import StopWords
from .text import StopWordsChinese
from .text import StopWordsArabic
from .text import StopWordsKorean
from .parsers import Parser, ParserSoup
from .urls import is_abs_url, get_domain
from .version import __version__

log = logging.getLogger(__name__)


"""
class HintsDict(dict):
    def __init__(self, *args):
        '''
        Works like a regular dict but the :meth:`get` method is different.

        ~~Hints~~ new feature:
        Example usage:
        Suppose newspaper article extractor was having issues with extracting
        text from 'Quartz' at qz.com. We can aid our extractor by providing simple
        hints obtained by just glancing at the page, like tag names or attributes & values
        of the tag containing our article.

        After inspecting a random quartz article suppose the body text is clearly
        in a <div> tag with a class labeled 'bodyArticle'.

        {'www.qz.com': {'tag': 'div', 'attr': 'class', 'value': 'bodyArticle'}
        ...}

        '''
        dict.__init__(self, args)

    def set(self, key, val):
        key = get_domain(key) if is_abs_url(key) else key
        if isinstance(val, dict):
            self[key] = val
        else:
            raise Exception("Not valid Hint value, must be in the form of \
            {'www.news.domain': {'tag': 'div', 'attr': 'class', 'value': 'bodyArticle'}")

    def get(self, key, default=None):
        key = get_domain(key) if is_abs_url(key) else key
        try:
            val = self[key]
        except (KeyError, ValueError):
            val = default
        return val
"""

class Configuration(object):

    def __init__(self):
        """
        Modify any of these Article / Source properties
        TODO: Have a seperate ArticleConfig and SourceConfig extend this!
        """
        self.MIN_WORD_COUNT  = 300      # num of word tokens in text
        self.MIN_SENT_COUNT  = 7        # num of sentence tokens
        self.MAX_TITLE       = 200      # num of chars
        self.MAX_TEXT        = 100000   # num of chars
        self.MAX_KEYWORDS    = 35       # num of strings in list
        self.MAX_AUTHORS     = 10       # num strings in list
        self.MAX_SUMMARY     = 5000     # num of chars

        # max number of urls we cache for each news source
        self.MAX_FILE_MEMO = 20000

        self.parser_class = 'lxml' # lxml vs soup

        # cache and save articles run after run
        self.memoize_articles = True

        # set this to false if you don't care about getting images
        self.fetch_images = True
        self.image_dimension_ration = 16/9.0

        # don't toggle this variable
        self.use_meta_language = True

        # you may keep the html of just the main article body
        self.keep_article_html = False

        # english is our fallback
        self._language = 'en'

        # unique stopword classes for oriental languages, don't toggle
        self.stopwords_class = StopWords

        self.browser_user_agent = 'newspaper/%s' % __version__
        self.request_timeout = 7
        self.number_threads = 10 # number of threads when mthreading

        self.verbose = False # turn this on when debugging

        # set this to False if you want to recompute the categories *every* time
        # self.use_cached_categories = True # TODO: Make this work

        # self.hints = None TODO: Maybe a future release?


    def get_language(self):
        return self._language

    def del_language(self):
        raise Exception('wtf are you doing?')

    def set_language(self, language):
        """
        Language setting must be done in this method because non-occidental
        (western) langauges require a seperate stopwords class.
        """
        if not language or len(language) != 2:
            raise Exception("Your input language must be a 2 char langauge code, \
                for example: english-->en \n and german-->de")

        self.use_meta_language = False # if explicitly set langauge, don't use meta

        # Set oriental language stopword class.
        self._language = language
        if language == 'ko':
            self.stopwords_class = StopWordsKorean
        elif language == 'zh':
            self.stopwords_class = StopWordsChinese
        elif language == 'ar':
            self.stopwords_class = StopWordsArabic

    language = property(get_language, set_language, del_language, "langauge prop")

    def get_parser(self):
        return Parser if self.parser_class == 'lxml' else ParserSoup

    def get_publishdate_extractor(self):
        """
        """
        return self.extract_publishdate

    def set_publishdate_extractor(self, extractor):
        """
        Pass in to extract article publish dates.
        @param extractor a concrete instance of PublishDateExtractor
        """
        if not extractor:
            raise ValueError("extractor must not be null!")
        self.extract_publishdate = extractor

    def get_additionaldata_extractor(self):
        """
        """
        return self.additional_data_extractor

    def set_additionaldata_extractor(self, extractor):
        """
        Pass in to extract any additional data not defined within
        @param extractor a concrete instance of AdditionalDataExtractor
        """
        if not extractor:
            raise ValueError("extractor must not be null!")
        self.additional_data_extractor = extractor


# TODO: Since we have Source() and Article() objects, we should split up
# TODO: the config options for both

class ArticleConfiguration(Configuration):
    pass

class SourceConfiguration(Configuration):
    pass

