# -*- coding: utf-8 -*-
"""
All unit tests for the newspaper library should be contained in this file.
"""
import sys
import os
import unittest
import time
import codecs

TEST_DIR = os.path.abspath(os.path.dirname(__file__))
PARENT_DIR = os.path.join(TEST_DIR, '..')

# tests is a separate module, insert parent dir manually
sys.path.insert(0, PARENT_DIR)

URLS_FN = os.path.join(TEST_DIR, 'data/100K_urls.txt')
TEXT_FN = os.path.join(TEST_DIR, 'data/body_text')
HTML_FN = os.path.join(TEST_DIR, 'data/html')

import newspaper
from newspaper import Article, Source, ArticleException, news_pool
from newspaper import Config
from newspaper.network import multithread_request
from newspaper.configuration import Configuration
from newspaper.utils.encoding import smart_str, smart_unicode
from newspaper.utils import encodeValue


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
        self.assertEqual(self.article.url, u'http://www.cnn.com/2013/11/27/travel/weather-thanksgiving/index.html')

    @print_test
    def test_download_html(self):
        self.article.download()
        # can't compare html because it changes on every page as time goes on
        self.assertGreater(len(self.article.html), 5000)

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
        LEN_IMGS = 47 # list is too big, we just check size of images arr

        self.article.parse()
        with open(os.path.join(TEST_DIR, 'data/body_example.txt'), 'r') as f:
            self.assertEqual(self.article.text, f.read())
        self.assertEqual(self.article.top_img, TOP_IMG)
        self.assertEqual(self.article.authors, AUTHORS)
        self.assertEqual(self.article.title, TITLE)
        print 'we now have ', len(self.article.imgs), 'images'
        self.assertEqual(len(self.article.imgs), LEN_IMGS)

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
        self.assertEqual(self.article.summary, SUMMARY)
        self.assertEqual(self.article.keywords, KEYWORDS)

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
        """
        builds a source object, validates it has no errors, prints out
        all valid categories and feed urls
        """
        DESC = """CNN.com delivers the latest breaking news and information on the latest top stories, weather, business, entertainment, politics, and more. For in-depth coverage, CNN.com provides special reports, video, audio, photo galleries, and interactive guides."""
        BRAND = 'cnn'

        config = Configuration()
        config.verbose = False
        s = Source('http://cnn.com', config=config)
        s.clean_memo_cache()
        s.build()

        self.assertEqual(s.brand, BRAND)
        self.assertEqual(s.description, DESC)

        # For this test case and a few more, I don't believe you can actually
        # assert two values to equal eachother because some values are ever changing.

        # Insead, i'm just going to print some stuff out so it is just as easy to take
        # a glance and see if it looks OK.

        print '\t\tWe have %d articles currently!' % s.size()
        print
        print '\t\t%s categories are: %s' % (s.url, str(s.category_urls()))

        # We are printing the contents of a source instead of
        # assert checking because the results are always varying
        # s.print_summary()

    @print_test
    def test_cache_categories(self):
        """
        builds two same source objects in a row examines speeds of both
        """
        s = Source('http://yahoo.com')
        s.download()
        s.parse()
        s.set_categories()

        saved_urls = s.category_urls()
        s.categories = [] # reset and try again with caching
        s.set_categories()
        self.assertEqual(sorted(s.category_urls()), sorted(saved_urls))

class UrlTestCase(unittest.TestCase):
    def runTest(self):
        print 'testing url unit'
        self.test_valid_urls()

    @print_test
    def test_valid_urls(self):
        """
        prints out a list of urls with our heuristic guess if it is a
        valid news url purely based on the url
        """
        from newspaper.urls import valid_url

        with open(os.path.join(TEST_DIR, 'data/test_urls.txt'), 'r') as f:
            lines = f.readlines()
            test_tuples = [tuple(l.strip().split(' ')) for l in lines]
            # tuples are ('1', 'url_goes_here') form, '1' means valid, '0' otherwise

        for tup in test_tuples:
            lst = int(tup[0])
            url = tup[1]
            self.assertEqual(len(tup), 2)
            truth_val = True if lst == 1 else False
            try:
                self.assertEqual(truth_val, valid_url(url, test=True))
            except AssertionError, e:
                print '\t\turl: %s is supposed to be %s' % (url, truth_val)
                raise

    @print_test
    def test_prepare_url(self):
        """
        normalizes a url, removes arguments, hashtags. If a relative url, it
        merges it with the source domain to make an abs url, etc
        """
        pass

class APITestCase(unittest.TestCase):
    def runTest(self):
        print 'testing API unit'
        # self.test_source_build()
        self.test_article_build()
        self.test_hot_trending()
        self.test_popular_urls()

    @print_test
    def test_source_build(self):
        huff_paper = newspaper.build('http://www.huffingtonpost.com/', dry=True)
        self.assertIsInstance(huff_paper, Source)

    @print_test
    def test_article_build(self):
        url = 'http://abcnews.go.com/blogs/politics/2013/12/states-cite-surge-in-obamacare-sign-ups-ahead-of-first-deadline/'
        article = newspaper.build_article(url)
        self.assertIsInstance(article, Article)
        article.download()
        article.parse()
        article.nlp()
        # print article.title
        # print article.summary
        # print article.keywords

    @print_test
    def test_hot_trending(self):
        """
        grab google trending, just make sure this runs
        """
        newspaper.hot()

    @print_test
    def test_popular_urls(self):
        """
        just make sure this runs
        """
        newspaper.popular_urls()

class EncodingTestCase(unittest.TestCase):
    def runTest(self):
        self.uni_string = u"∆ˆˆø∆ßåßlucas yang˜"
        self.normal_string = "∆ƒˆƒ´´lucas yang"
        self.test_encode_val()
        self.test_smart_unicode()
        self.test_smart_str()

    @print_test
    def test_encode_val(self):
        self.assertEqual(encodeValue(self.uni_string), self.uni_string)
        self.assertEqual(encodeValue(self.normal_string), u'∆ƒˆƒ´´lucas yang')

    @print_test
    def test_smart_unicode(self):
        self.assertEqual(smart_unicode(self.uni_string), self.uni_string)
        self.assertEqual(smart_unicode(self.normal_string), u'∆ƒˆƒ´´lucas yang')

    @print_test
    def test_smart_str(self):
        self.assertEqual(smart_str(self.uni_string), "∆ˆˆø∆ßåßlucas yang˜")
        self.assertEqual(smart_str(self.normal_string), "∆ƒˆƒ´´lucas yang")


class MThreadingTestCase(unittest.TestCase):
    def runTest(self):
        self.test_download_works()

    @print_test
    def test_download_works(self):
        """
        """
        config = Configuration()
        config.memoize_articles = False
        slate_paper = newspaper.build('http://slate.com', config)
        tc_paper = newspaper.build('http://techcrunch.com', config)
        espn_paper = newspaper.build('http://espn.com', config)

        print 'slate has %d articles tc has %d articles espn has %d articles' \
                % (slate_paper.size(), tc_paper.size(), espn_paper.size())

        papers = [slate_paper, tc_paper, espn_paper]
        news_pool.set(papers, threads_per_source=2)

        news_pool.join()

        print 'Downloaded slate mthread len', len(slate_paper.articles[0].html)
        print 'Downloaded espn mthread len', len(espn_paper.articles[-1].html)
        print 'Downloaded tc mthread len', len(tc_paper.articles[1].html)


class ConfigBuildTestCase(unittest.TestCase):
    def runTest(self):
        self.test_config_build()

    @print_test
    def test_config_build(self):
        """
        Test if our **kwargs to config building setup actually works.
        """
        a = Article(url='http://www.cnn.com/2013/11/27/travel/weather-thanksgiving/index.html')
        self.assertEqual(a.config.language, 'en')
        self.assertTrue(a.config.memoize_articles)
        self.assertTrue(a.config.use_meta_language)

        a = Article(url='http://www.cnn.com/2013/11/27/travel/weather-thanksgiving/index.html',
                language='zh', memoize_articles=False)
        self.assertEqual(a.config.language, 'zh')
        self.assertFalse(a.config.memoize_articles)
        self.assertFalse(a.config.use_meta_language)

        s = Source(url='http://cnn.com')
        self.assertEqual(s.config.language, 'en')
        self.assertEqual(s.config.MAX_FILE_MEMO, 20000)
        self.assertTrue(s.config.memoize_articles)
        self.assertTrue(s.config.use_meta_language)

        s = Source(url="http://cnn.com", memoize_articles=False,
                MAX_FILE_MEMO=10000, language='en')
        self.assertFalse(s.config.memoize_articles)
        self.assertEqual(s.config.MAX_FILE_MEMO, 10000)
        self.assertEqual(s.config.language, 'en')
        self.assertFalse(s.config.use_meta_language)

        s = newspaper.build('http://cnn.com', dry=True)
        self.assertEqual(s.config.language, 'en')
        self.assertEqual(s.config.MAX_FILE_MEMO, 20000)
        self.assertTrue(s.config.memoize_articles)
        self.assertTrue(s.config.use_meta_language)

        s = newspaper.build('http://cnn.com', dry=True, memoize_articles=False,
                MAX_FILE_MEMO=10000, language='zh')
        self.assertEqual(s.config.language, 'zh')
        self.assertEqual(s.config.MAX_FILE_MEMO, 10000)
        self.assertFalse(s.config.memoize_articles)
        self.assertFalse(s.config.use_meta_language)

class MultiLanguageTestCase(unittest.TestCase):
    def runTest(self):
        self.test_chinese_fulltext_extract()
        self.test_arabic_fulltext_extract()
        #self.test_spanish_fulltext_extract()

    @print_test
    def test_chinese_fulltext_extract(self):
        url = 'http://www.bbc.co.uk/zhongwen/simp/chinese_news/2012/12/121210_hongkong_politics.shtml'
        article = Article(url=url, language='zh')
        article.download()
        article.parse()
        with codecs.open(os.path.join(TEXT_FN, 'chinese_text_1.txt'), 'r', 'utf8') as f:
            self.assertEqual(article.text, f.read())

        # with codecs.open(os.path.join(HTML_FN, 'chinese_html_1.html'), 'w', 'utf8') as f:
        #    f.write(article.html)

    @print_test
    def test_arabic_fulltext_extract(self):
        url = 'http://arabic.cnn.com/2013/middle_east/8/3/syria.clashes/index.html'
        article = Article(url=url, language='ar')
        article.download()
        article.parse()
        with codecs.open(os.path.join(TEXT_FN, 'arabic_text_1.txt'), 'r', 'utf8') as f:
            self.assertEqual(article.text, f.read())

        # with codecs.open(os.path.join(HTML_FN, 'arabic_html_1.html'), 'w', 'utf8') as f:
        #    f.write(article.html)

    @print_test
    def test_spanish_fulltext_extract(self):
        url = 'http://ultimahora.es/mallorca/noticia/noticias/local/fiscalia-anticorrupcion-estudia-recurre-imputacion-infanta.html'
        article = Article(url=url, language='es')
        article.download()
        article.parse()
        with codecs.open(os.path.join(TEXT_FN, 'spanish_text_1.txt'), 'r', 'utf8') as f:
            self.assertEqual(article.text, f.read())

        # with codecs.open(os.path.join(HTML_FN, 'spanish_html_1.html'), 'w', 'utf8') as f:
        #    f.write(article.html)

if __name__ == '__main__':
    # unittest.main() # run all units and their cases

    suite = unittest.TestSuite()

    suite.addTest(ConfigBuildTestCase())
    # suite.addTest(MThreadingTestCase())
    suite.addTest(MultiLanguageTestCase())
    suite.addTest(SourceTestCase())
    suite.addTest(EncodingTestCase())
    suite.addTest(UrlTestCase())
    suite.addTest(ArticleTestCase())
    suite.addTest(APITestCase())
    unittest.TextTestRunner().run(suite) # run custom subset



