# -*- coding: utf-8 -*-
"""\
This is a python port of "Goose" orignialy licensed to Gravity.com
under one or more contributor license agreements.  See the NOTICE file
distributed with this work for additional information
regarding copyright ownership.

Python port was written by Xavier Grangier for Recrutae

Gravity.com licenses this file
to you under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance
with the License.  You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
import os
import tempfile
from .text import StopWords
from .parsers import Parser
from .parsers import ParserSoup
from .version import __version__


class Configuration(object):

    def __init__(self):
        # What's the minimum bytes for an image we'd accept is,
        # alot of times we want to filter out the author's little images
        # in the beginning of the article
        self.images_min_bytes = 4500

        # set this guy to false if you don't care about getting images,
        # otherwise you can either use the default
        # image extractor to implement the ImageExtractor
        # interface to build your own
        self.enable_image_fetching = True

        # set this valriable to False if you want to force
        # the article language. OtherWise it will attempt to
        # find meta language and use the correct stopwords dictionary
        self.use_meta_language = True

        # default language
        # it will be use as fallback
        # if use_meta_language is set to false, targetlanguage will
        # be use
        self.target_language = 'en'

        # defautl stopwrods class
        self.stopwords_class = StopWords

        # path to your imagemagick convert executable,
        # on the mac using mac ports this is the default listed
        self.imagemagick_convert_path = "/opt/local/bin/convert"

        # path to your imagemagick identify executable
        self.imagemagick_identify_path = "/opt/local/bin/identify"

        # used as the user agent that
        # is sent with your web requests to extract an article
        # self.browser_user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_2)"\
        #                         " AppleWebKit/534.52.7 (KHTML, like Gecko) "\
        #                         "Version/5.1.2 Safari/534.52.7"
        self.browser_user_agent = 'Goose/%s' % __version__

        # debug mode
        # enable this to have additional debugging information
        # sent to stdout
        self.debug = False

        # TODO
        self.extract_publishdate = None

        # TODO
        self.additional_data_extractor = None

        # Parser type
        self.parser_class = 'lxml'

    @property
    def local_storage_path(self):
        return os.path.join(tempfile.gettempdir(), 'goose')

    def get_parser(self):
        return Parser if self.parser_class == 'lxml' else ParserSoup

    def get_publishdate_extractor(self):
        return self.extract_publishdate

    def set_publishdate_extractor(self, extractor):
        """\
        Pass in to extract article publish dates.
        @param extractor a concrete instance of PublishDateExtractor
        """
        if not extractor:
            raise ValueError("extractor must not be null!")
        self.extract_publishdate = extractor

    def get_additionaldata_extractor(self):
        return self.additional_data_extractor

    def set_additionaldata_extractor(self, extractor):
        """\
        Pass in to extract any additional data not defined within
        @param extractor a concrete instance of AdditionalDataExtractor
        """
        if not extractor:
            raise ValueError("extractor must not be null!")
        self.additional_data_extractor = extractor
