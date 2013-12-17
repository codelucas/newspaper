# -*- coding: utf-8 -*-

import sys
import os
import unittest
import time
import codecs
import urlparse

TEST_DIR = os.path.abspath(os.path.dirname(__file__))
PARENT_DIR = os.path.join(TEST_DIR, '..')

# tests is a separate module, insert parent dir manually
sys.path.insert(0, PARENT_DIR)

URLS_FN = os.path.join(TEST_DIR, 'data/100K_urls.txt')

from newspaper.article import Article
from newspaper.source import Source
from newspaper.settings import ANCHOR_DIR
from newspaper.network import async_request

def print_test(method):
    """utility method for print verbalizing test suite, prints out
    time taken for test and functions name, and status"""

    def run(*args, **kw):
        ts = time.time()
        print '\ttesting function %r' % method.__name__
        method(*args, **kw)
        te = time.time()
        print '\t[OK] in %r %2.2f sec' % (method.__name__, te-ts)
    return run

def read_urls(base_fn=URLS_FN, amount=100):
    """utility funct which extracts out a listing of sample urls"""

    f = codecs.open(base_fn, 'r', 'utf8')
    lines = f.readlines()
    lines = [l.strip() for l in lines]
    return lines[:amount]

class ArticleTestCase(unittest.TestCase):
    def runTest(self):
        print 'testing article unit'
        self.test_url()

    def setUp(self):
        """called before the first test case of this unit begins"""
        pass

    def tearDown(self):
        """called after all test cases finish of this unit"""
        pass

    @print_test
    def test_url(self):
        a = Article(url='http://www.cnn.com/2013/11/27/travel/weather-thanksgiving/index.html?hpt=hp_t1')
        assert a.url == u'http://www.cnn.com/2013/11/27/travel/weather-thanksgiving/index.html'

class SourceTestCase(unittest.TestCase):
    def runTest(self):
        print 'testing source unit'
        self.source_url_input_none()
        #self.test_source_build()
        #self.test_cache_categories()

    @print_test
    def source_url_input_none(self):
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

        @print_test
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
    def runTest(self):
        print 'testing url unit'
        self.test_valid_urls()

    @print_test
    def test_valid_urls(self):
        """prints out a list of urls with our heuristic guess if it is a
        valid news url purely based on the url"""

        from newspaper.urls import valid_url

        with open(os.path.join(TEST_DIR, 'data/test_urls.txt'), 'r') as f:
            lines = f.readlines()
            test_tuples = [tuple(l.strip().split(' ')) for l in lines]
            # tuples are ('1', 'url_goes_here') form, '1' means valid, '0' otherwise

        for tup in test_tuples:
            lst = int(tup[0])
            url = tup[1]
            assert len(tup) == 2
            truth_val = True if lst == 1 else False
            try:
                assert truth_val == valid_url(url)
            except AssertionError, e:
                print '\t\turl: %s is supposed to be %s' % (url, truth_val)
                raise

if __name__ == '__main__':
    # unittest.main() # run all units and their cases
    suite = unittest.TestSuite()

    suite.addTest(ArticleTestCase())
    suite.addTest(SourceTestCase())
    suite.addTest(UrlTestCase())

    unittest.TextTestRunner().run(suite) # run custom subset

"""
class GrequestsTestCase(unittest.TestCase):
    def runTest(self):
        print 'testing grequests unit'
        #self.test_ordering()
        self.test_capacity()

    @print_test
    def test_ordering(self):

        TEST_SIZE = 25
        dd = {}
        urls = read_urls(amount=TEST_SIZE)

        # don't count feeds, they always redirect to some other url
        urls = [u for u in urls if 'feeds' not in urlparse.urlparse(u).netloc.split('.')]

        for index, url in enumerate(urls):
            _ul = urlparse.urlparse(url)
            normalized = _ul.netloc + _ul.path
            dd[index] = normalized

        responses = async_request(urls, timeout=3)
        for index, resp in enumerate(responses):
            _ul = urlparse.urlparse(resp.url)
            normalized = _ul.netloc + _ul.path
            # print dd[index], '==', normalized
            assert dd[index] == normalized

    @print_test
    def test_capacity(self):

        TEST_SIZE = 450
        urls = read_urls(amount=TEST_SIZE)
        responses = async_request(urls, timeout=3)
        failed = 0
        for index, r in enumerate(responses):
            if r is not None:
                pass
            else:
                #print '[FAIL]', urls[index]
                failed += 1
        print '\t\ttotal:', len(urls), 'failed', failed

"""
