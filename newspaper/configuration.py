# -*- coding: utf-8 -*-
"""
Config settings for both Source and Article objects.
Pass these in (optionally) via the constructors. Or
else a default Configuration() object will be used.
"""

import logging

from .text import StopWords
from .text import StopWordsChinese
from .text import StopWordsArabic
from .text import StopWordsKorean
from .parsers import Parser, ParserSoup
from .version import __version__

log = logging.getLogger(__name__)

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

        # maximum number of urls we memo per news domain
        self.MAX_FILE_MEMO = 20000

        # minimum bytes for an image we'd accept, (filter out small imgs)
        self.images_min_bytes = 5000

        # cache and save articles run after run
        self.is_memoize_articles = True

        # set this to false if you don't care about getting images
        # TODO: Make this work
        self.enable_image_fetching = True

        # TODO: Make this work
        # self.use_cached_categories = True

        # set this var to False if you want to force
        # the article language. Otherwise it will attempt to
        # find meta language and use the correct stopwords dictionary
        self.use_meta_language = True

        # english is our fallback
        self.language = 'en'
        self.stopwords_class = StopWords

        self.max_file_memo = 20000

        self.browser_user_agent = 'newspaper/%s' % __version__
        self.request_timeout = 7
        self.number_threads = 10 # number of threads when mthreading

        self.verbose = False # turn this on when debugging

        self.parser_class = 'lxml' # lxml vs soup

    def get_parser(self):
        """
        """
        return Parser if self.parser_class == 'lxml' else ParserSoup

    def set_language(self, language):
        """
        Language setting must be done in this method because non-occidental
        (western) langauges require a seperate stopwords class.
        """
        if not language or len(language) != 2:
            raise Exception("Your input language must be a 2 char langauge code, \
                for example: english-->en \n and german-->de")

        # Set oriental language stopword class.
        self.language = language
        if language == 'ko':
            self.stopwords_class = StopWordsKorean
        elif language == 'zh':
            self.stopwords_class = StopWordsChinese
        elif language == 'ar':
            self.stopwords_class = StopWordsArabic

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

