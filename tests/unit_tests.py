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

import newspaper
from newspaper import Article, ArticleException
from newspaper import Source, Article
from newspaper.network import multithread_request

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
        self.test_download_html()
        self.test_pre_download_parse()
        self.test_parse_html()
        self.test_article_hash_key()
        self.test_pre_parse_nlp()
        self.test_nlp_body()

    def setUp(self):
        """called before the first test case of this unit begins"""

        self.article = Article(
            url='http://www.cnn.com/2013/11/27/travel/weather-thanksgiving/index.html?iref=allsearch')

    def tearDown(self):
        """called after all test cases finish of this unit"""
        pass

    @print_test
    def test_url(self):
        assert self.article.url == u'http://www.cnn.com/2013/11/27/travel/weather-thanksgiving/index.html'

    @print_test
    def test_download_html(self):
        self.article.download()
        # can't compare html because it changes on every page as time goes on
        assert len(self.article.html) > 5000

    @print_test
    def test_pre_download_parse(self):
        """before we download an article you should not be parsing!"""

        a2 = Article(url='http://www.cnn.com/2013/11/27/travel/weather-thanksgiving/index.html')
        def failfunc():
            a2.parse()
        self.assertRaises(ArticleException, failfunc)

    @print_test
    def test_parse_html(self):
        TOP_IMG = 'http://i2.cdn.turner.com/cnn/dam/assets/131129200805-01-weather-1128-story-top.jpg'
        DOMAIN = 'www.cnn.com'
        SCHEME = 'http'
        AUTHORS = ['Dana Ford', 'Tom Watkins']
        TITLE = 'After storm, forecasters see smooth sailing for Thanksgiving'
        LEN_IMGS = 49 # list is too big, we just check size of images arr

        self.article.parse()
        with open(os.path.join(TEST_DIR, 'data/body_example.txt'), 'r') as f:
            assert self.article.text == f.read()
        assert self.article.top_img == TOP_IMG
        assert self.article.authors == AUTHORS
        assert self.article.domain == DOMAIN
        assert self.article.scheme == SCHEME
        assert self.article.title == TITLE
        assert len(self.article.imgs) == LEN_IMGS

    @print_test
    def test_pre_parse_nlp(self):
        a2 = Article(url='http://www.cnn.com/2013/11/27/travel/weather-thanksgiving/index.html')
        a2.download()
        a3 = Article(url='http://www.cnn.com/2013/11/27/travel/weather-thanksgiving/index.html')
        def failfunc():
            a2.nlp()
        def failfunc2():
            a3.nlp()
        self.assertRaises(ArticleException, failfunc)
        self.assertRaises(ArticleException, failfunc2)

    @print_test
    def test_nlp_body(self):
        SUMMARY = """Wish the forecasters were wrong all the time :)"Though the worst of the storm has passed, winds could still pose a problem.\r\nForecasters see mostly smooth sailing into Thanksgiving.\r\nThe forecast has left up in the air the fate of the balloons in Macy's Thanksgiving Day Parade.\r\nThe storm caused some complications and inconveniences, but no major delays or breakdowns.\r\n"That's good news for people like Latasha Abney, who joined the more than 43 million Americans expected by AAA to travel over the Thanksgiving holiday weekend."""

        KEYWORDS = [u'great', u'good', u'flight', u'sailing', u'delays', u'smooth', u'thanksgiving',
                    u'snow', u'weather', u'york', u'storm', u'winds', u'balloons', u'forecasters']

        self.article.nlp()

        # print self.article.summary
        # print self.article.keywords
        assert self.article.summary == SUMMARY
        assert self.article.keywords == KEYWORDS

    @print_test
    def test_article_hash_key(self):
        KEY = 'jyYRJb9K6kN4-oiKfZvM1Q=='
        assert self.article.get_key() == KEY

class SourceTestCase(unittest.TestCase):
    def runTest(self):
        print 'testing source unit'
        self.source_url_input_none()
        self.test_cache_categories()
        self.test_source_build()

    @print_test
    def source_url_input_none(self):
        def failfunc():
            __ = Source(url=None)
        self.assertRaises(Exception, failfunc)

    @print_test
    def test_source_build(self):
        """builds a source object, validates it has no errors, prints out
        all valid categories and feed urls"""

        DESC = """CNN.com delivers the latest breaking news and information on the latest top stories, weather, business, entertainment, politics, and more. For in-depth coverage, CNN.com provides special reports, video, audio, photo galleries, and interactive guides."""
        BRAND = 'cnn'

        s = Source('http://cnn.com', verbose=False)
        s.clean_memo_cache()
        s.build()

        assert s.brand == BRAND
        assert s.description == DESC

        print '\t\tWe have %d articles currently!' % s.size()
        # We are printing the contents of a source instead of
        # assert checking because the results are always varying
        # s.print_summary()

    @print_test
    def test_cache_categories(self):
        """builds two same source objects in a row examines speeds of both"""

        s = Source('http://yahoo.com')
        s.download()
        s.parse()
        s.set_categories()

        saved_urls = s.category_urls()
        s.categories = [] # reset and try again with caching

        s.set_categories()

        assert sorted(s.category_urls()) == sorted(saved_urls)
        # print '[CATEGORIES]', s.category_urls()

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
                assert truth_val == valid_url(url, test=True)
            except AssertionError, e:
                print '\t\turl: %s is supposed to be %s' % (url, truth_val)
                raise

    @print_test
    def test_prepare_url(self):
        """normalizes a url, removes arguments, hashtags. If a relative url, it
        merges it with the source domain to make an abs url, etc"""

        pass

class APITestCase(unittest.TestCase):
    def runTest(self):
        print 'testing API unit'
        self.test_source_build()
        self.test_article_build()
        self.test_hot_trending()
        self.test_popular_urls()

    @print_test
    def test_source_build(self):
        huff_paper = newspaper.build('http://www.huffingtonpost.com/')
        assert isinstance(huff_paper, Source) == True

    @print_test
    def test_article_build(self):
        url = 'http://abcnews.go.com/blogs/politics/2013/12/states-cite-surge-in-obamacare-sign-ups-ahead-of-first-deadline/'
        article = newspaper.build_article(url)
        assert isinstance(article, Article) == True
        article.download()
        article.parse()
        article.nlp()
        #print article.title
        #print article.summary
        #print article.keywords

    @print_test
    def test_hot_trending(self):
        """grab google trending, just make sure this runs"""

        newspaper.hot()

    @print_test
    def test_popular_urls(self):
        """just make sure this runs"""

        newspaper.popular_urls()

if __name__ == '__main__':
    # unittest.main() # run all units and their cases
    suite = unittest.TestSuite()

    suite.addTest(UrlTestCase())
    suite.addTest(ArticleTestCase())
    suite.addTest(APITestCase())
    suite.addTest(SourceTestCase())

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
