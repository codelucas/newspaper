# -*- coding: utf-8 -*-

import os
import unittest
import logging

from newspaper.article import Article
from newspaper.source import Source
from newspaper.utils import print_duration
from newspaper.settings import ANCHOR_DIR



# class ArticleTestCase(unittest.TestCase):
#
#     def setUp(self):
#         """initializer, create data set with headers"""
#         print 'this goes first'
#
#     def tearDown(self):
#         """teardown and free components"""
#         print 'this goes last'
#
#     def test_url(self):
#         a = Article(url='http://www.cnn.com/2013/11/27/travel/weather-thanksgiving/index.html?hpt=hp_t1')
#         assert a.url == u'http://www.cnn.com/2013/11/27/travel/weather-thanksgiving/index.html'
#         print a.title

class SourceTestCase(unittest.TestCase):

    def test_url_none(self):
        def failfunc():
            __ = Source(url=None)
        self.assertRaises(Exception, failfunc)

    def test_source_build(self):
        """builds a source object, validates it has no errors, prints out
        all valid categories and feed urls"""

        s = Source('http://cnn.com')
        s.build()
        s.print_summary()

    def test_cache_categories(self):
        """builds two same source objects in a row examines speeds of both"""

        @print_duration
        def wrap_category_urls(source):
            source.set_category_urls()

        s = Source('http://yahoo.com')
        s.download()
        s.parse()

        saved_urls = []
        print 'before',
        wrap_category_urls(s)
        print len(s.category_urls)
        saved_urls = s.category_urls
        s.category_urls = [] # reset and try again with caching
        print 'after',
        wrap_category_urls(s)
        assert sorted(s.category_urls) == sorted(saved_urls)

        print os.listdir(ANCHOR_DIR), 'at', ANCHOR_DIR



if __name__ == '__main__':
    unittest.main()