# -*- coding: utf-8 -*-
import sys
import os
import unittest

TEST_DIR = os.path.abspath(os.path.dirname(__file__))
PARENT_DIR = os.path.join(TEST_DIR, '..')

# parent dir needs to be manually inserted as tests
# is a separate module
sys.path.insert(0, PARENT_DIR)

from newspaper.article import Article
from newspaper.source import Source
from newspaper.utils import print_duration
from newspaper.settings import ANCHOR_DIR
from newspaper.network import async_request

def read_urls(base_fn=os.path.join(TEST_DIR, 'data/100K_urls.txt'), amount=100):
    """extracts out a listing of sample urls"""
    import codecs

    f = codecs.open(base_fn, 'r', 'utf8')
    lines = f.readlines()
    lines = [l.strip() for l in lines]
    return lines[:amount]

class GrequestsTestCase(unittest.TestCase):

    @print_duration
    def test_ordering(self):
        """assert that responses return in same order as requests"""
        import requests
        # import goose

        TEST_SIZE = 100
        dd = {}
        urls = read_urls(amount=100)
        for index, url in enumerate(urls):
            # ensure that first 200 chars of html is the same
            dd[index] = url #requests.get(u).text[:TEST_SIZE]

        responses = async_request(urls, timeout=7)

        for index, resp in enumerate(responses):
            print dd[index]
            print resp.url # resp.text[:TEST_SIZE]
            print '=============='
            #assert dd[index] == resp.text[:TEST_SIZE]

    @print_duration
    def test_capacity(self):
        """try to send out a bunch of requests, see if it works"""
        urls = read_urls(amount=1000)
        responses = async_request(urls, timeout=3)
        failed = 0
        for index, r in enumerate(responses):
            if r is not None:
                print '[SUCCESS]', r.url
            else:
                print '[FAIL]', urls[index]
                failed += 1
        print '\r\n\r\ntotal:', len(urls), 'failed', failed

class ArticleTestCase(unittest.TestCase):
    def setUp(self):
        """initializer, create data set with headers"""
        print 'setUp ArticleTestCase'

    def tearDown(self):
        """teardown and free components"""
        print 'tearDown ArticleTestCase'

    def test_url(self):
        a = Article(url='http://www.cnn.com/2013/11/27/travel/weather-thanksgiving/index.html?hpt=hp_t1')
        assert a.url == u'http://www.cnn.com/2013/11/27/travel/weather-thanksgiving/index.html'
        print a.title

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

        print 'before',
        wrap_category_urls(s)
        print len(s.categories)
        saved_urls = [c.url for c in s.categories]

        s.category_urls = [] # reset and try again with caching
        print 'after',
        wrap_category_urls(s)
        assert sorted([c.url for c in s.categories]) == sorted(saved_urls)

        print os.listdir(ANCHOR_DIR), 'at', ANCHOR_DIR

class UrlTestCase(unittest.TestCase):
    def test_valid_urls(self):
        """prints out a list of urls with our heuristic guess if it is a
        valid news url purely based on the url"""

        from newspaper.urls import valid_url
        from newspaper.parsers import get_urls
        import requests

        rss_fn = open(os.path.join(TEST_DIR, 'data/cnn_rss_feeds.txt'), 'r')
        rss_urls = rss_fn.readlines()
        total_urls = []
        for url in rss_urls:
            text = requests.get(url).text
            total_urls.extend(get_urls(text, regex=True))

        rss_fn.close()
        total_urls = list(set(total_urls))
        urls_fn = open(os.path.join(TEST_DIR, 'data/sample_urls_1.txt'), 'w')
        for url in total_urls:
            urls_fn.write(url+'\r\n')
        urls_fn.close()

        # for url in rss_urls:
        #   print valid_url(url), url

        # urls_fn = open(os.path.join(PARENT_DIR, 'data/sample_urls_1.txt'), 'r')
        # urls = urls_fn.readlines()
        # urls_fn.close()
        # urls = list(set(urls))
        # urls_fn2 = open(os.path.join(PARENT_DIR, 'data/sample_urls_1.txt'), 'w')
        # urls_fn2.write('\r\n'.join(urls))
        # urls_fn2.close()

if __name__ == '__main__':
    unittest.main()
