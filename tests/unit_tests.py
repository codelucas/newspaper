# -*- coding: utf-8 -*-
"""
All unit tests for the newspaper library should be contained in this file.
"""
import sys
import os
import re
import unittest
import time
import codecs
import types
import responses
from collections import defaultdict

TEST_DIR = os.path.abspath(os.path.dirname(__file__))
PARENT_DIR = os.path.join(TEST_DIR, '..')

# tests is a separate module, insert parent dir manually
sys.path.insert(0, PARENT_DIR)

TEXT_FN = os.path.join(TEST_DIR, 'data/text')
HTML_FN = os.path.join(TEST_DIR, 'data/html')

import newspaper
from newspaper import Article, Source, ArticleException, news_pool
from newspaper import Config
from newspaper.network import multithread_request
from newspaper.configuration import Configuration
from newspaper.text import (StopWords, StopWordsArabic,
                            StopWordsKorean, StopWordsChinese)
from newspaper.utils.encoding import smart_str, smart_unicode
from newspaper.utils import encodeValue


def print_test(method):
    """Utility method for print verbalizing test suite, prints out
    time taken for test and functions name, and status
    """
    def run(*args, **kw):
        ts = time.time()
        print '\ttesting function %r' % method.__name__
        method(*args, **kw)
        te = time.time()
        print '\t[OK] in %r %2.2f sec' % (method.__name__, te-ts)
    return run


def mock_response_with(url, response_file):
    response_path = os.path.join(TEST_DIR, "data/html/%s.html" % response_file)
    with open(response_path, 'r') as f:
        body = f.read()

    responses.add(responses.GET, url, body=body, status=200,
                  content_type='text/html')


class ArticleTestCase(unittest.TestCase):
    def runTest(self):
        self.test_url()
        self.test_download_html()
        self.test_pre_download_parse()
        self.test_parse_html()
        self.test_meta_type_extraction()
        self.test_meta_extraction()
        self.test_pre_parse_nlp()
        self.test_nlp_body()

    def setUp(self):
        """called before the first test case of this unit begins
        """
        self.article = Article(
            url='http://www.cnn.com/2013/11/27/travel/weather-'
                'thanksgiving/index.html?iref=allsearch')

    def tearDown(self):
        """Called after all test cases finish of this unit
        """
        pass

    @print_test
    def test_url(self):
        assert self.article.url == (
            u'http://www.cnn.com/2013/11/27/travel/weather-'
            'thanksgiving/index.html?iref=allsearch')

    @print_test
    @responses.activate
    def test_download_html(self):
        canon_url = 'http://www.cnn.com/2013/11/27/travel/weather-thanksgiving/index.html'
        mock_response_with(canon_url, 'cnn_article')
        self.article.download()
        assert len(self.article.html) == 75244

    @print_test
    def test_pre_download_parse(self):
        """Before we download an article you should not be parsing!
        """
        article = Article(self.article.url)

        def failfunc():
            article.parse()
        self.assertRaises(ArticleException, failfunc)

    @print_test
    @responses.activate
    def test_parse_html(self):
        TOP_IMG = ('http://i2.cdn.turner.com/cnn/dam/assets/131129200805-'
                   '01-weather-1128-story-top.jpg')
        DOMAIN = 'www.cnn.com'
        SCHEME = 'http'
        AUTHORS = ['Dana Ford', 'Tom Watkins']
        TITLE = 'After storm, forecasters see smooth sailing for Thanksgiving'
        LEN_IMGS = 46
        META_LANG = 'en'

        mock_response_with(self.article.url, 'cnn_article')
        self.article.build()
        with open(os.path.join(TEXT_FN, 'cnn.txt'), 'r') as f:
            assert self.article.text == f.read()
        assert self.article.top_img == TOP_IMG
        assert self.article.authors == AUTHORS
        assert self.article.title == TITLE
        assert len(self.article.imgs) == LEN_IMGS
        assert self.article.meta_lang == META_LANG

    @print_test
    @responses.activate
    def test_meta_type_extraction(self):
        mock_response_with(self.article.url, 'cnn_article')
        self.article.build()

        meta_type = self.article.extractor.get_meta_type(
            self.article.clean_doc)
        assert 'article' == meta_type

    @print_test
    @responses.activate
    def test_meta_extraction(self):
        mock_response_with(self.article.url, 'cnn_article')
        self.article.build()

        meta = self.article.extractor.get_meta_data(self.article.clean_doc)
        META_DATA = defaultdict(dict, {
            'medium': 'news',
            'googlebot': 'noarchive',
            'pubdate': '2013-11-27T08:36:32Z',
            'title': 'After storm, forecasters see smooth sailing for Thanksgiving - CNN.com',
            'og': {'site_name': 'CNN','description': 'A strong storm struck much of the eastern United States on Wednesday, complicating holiday plans for many of the 43 million Americans expected to travel.', 'title': 'After storm, forecasters see smooth sailing for Thanksgiving', 'url': 'http://www.cnn.com/2013/11/27/travel/weather-thanksgiving/index.html', 'image': 'http://i2.cdn.turner.com/cnn/dam/assets/131129200805-01-weather-1128-story-top.jpg', 'type': 'article'},
            'section': 'travel',
            'author': 'Dana Ford and Tom Watkins, CNN',
            'robots': 'index,follow',
            'vr': {'canonical': 'http://edition.cnn.com/2013/11/27/travel/weather-thanksgiving/index.html'},
            'source': 'CNN',
            'fb': {'page_id': 18793419640, 'app_id': 80401312489},
            'keywords': 'winter storm,holiday travel,Thanksgiving storm,Thanksgiving winter storm',
            'article': {'publisher': 'https://www.facebook.com/cnninternational'},
            'lastmod': '2013-11-28T02:03:23Z',
            'twitter': {'site': {'identifier': '@CNNI', 'id': 2097571}, 'card': 'summary', 'creator': {'identifier': '@cnntravel', 'id': 174377718}},
            'viewport':'width=1024',
            'news_keywords': 'winter storm,holiday travel,Thanksgiving storm,Thanksgiving winter storm'
        })

        assert meta == META_DATA

        # if the value for a meta key is another dict, that dict ought to be
        # filled with keys and values
        dict_values = filter(lambda v: isinstance(v, dict), meta.values())
        assert all(map(lambda d: len(d) > 0, dict_values))

        # there are exactly 5 top-level "og:type" type keys
        is_dict = lambda v: isinstance(v, dict)
        assert len(filter(is_dict, meta.values())) == 5

        # there are exactly 12 top-level "pubdate" type keys
        is_string = lambda v: isinstance(v, types.StringTypes)
        assert len(filter(is_string, meta.values())) == 12

    @print_test
    @responses.activate
    def test_pre_download_nlp(self):
        """Test running NLP algos before even downloading the article
        """
        mock_response_with(self.article.url, 'cnn_article')

        def failfunc():
            self.article.nlp()
        self.assertRaises(ArticleException, failfunc)

    @print_test
    def test_pre_parse_nlp(self):
        """Test running NLP algos before parsing the article
        """
        article = Article(self.article.url)
        article.download()

        def failfunc():
            article.nlp()
        self.assertRaises(ArticleException, failfunc)

    @print_test
    @responses.activate
    def test_nlp_body(self):
        SUMMARY = """Wish the forecasters were wrong all the time :)"Though the worst of the storm has passed, winds could still pose a problem.\r\nForecasters see mostly smooth sailing into Thanksgiving.\r\nThe forecast has left up in the air the fate of the balloons in Macy's Thanksgiving Day Parade.\r\nThe storm caused some complications and inconveniences, but no major delays or breakdowns.\r\nThat's good news for people like Latasha Abney, who joined the more than 43 million Americans expected by AAA to travel over the Thanksgiving holiday weekend."""

        KEYWORDS = [
            u'great', u'good', u'flight', u'sailing', u'delays',
            u'smooth', u'thanksgiving', u'snow', u'weather', u'york',
            u'storm', u'winds', u'balloons', u'forecasters']

        mock_response_with(self.article.url, 'cnn_article')
        self.article.build()
        self.article.nlp()
        # print self.article.summary
        # print self.article.keywords
        assert self.article.summary == SUMMARY
        assert self.article.keywords == KEYWORDS


class SourceTestCase(unittest.TestCase):
    def runTest(self):
        self.source_url_input_none()
        self.test_cache_categories()
        self.test_source_build()

    @print_test
    def source_url_input_none(self):
        def failfunc():
            __ = Source(url=None)
        self.assertRaises(Exception, failfunc)

    @print_test
    @responses.activate
    def test_source_build(self):
        """
        builds a source object, validates it has no errors, prints out
        all valid categories and feed urls
        """
        DESC = ('CNN.com International delivers breaking news from across '
                'the globe and information on the latest top stories, '
                'business, sports and entertainment headlines. Follow the '
                'news as it happens through: special reports, videos, '
                'audio, photo galleries plus interactive maps and timelines.')
        CATEGORY_URLS = [
            u'http://cnn.com/ASIA', u'http://connecttheworld.blogs.cnn.com',
            u'http://cnn.com/HLN', u'http://cnn.com/MIDDLEEAST',
            u'http://cnn.com', u'http://ireport.cnn.com',
            u'http://cnn.com/video', u'http://transcripts.cnn.com',
            u'http://cnn.com/espanol',
            u'http://partners.cnn.com', u'http://www.cnn.com',
            u'http://cnn.com/US', u'http://cnn.com/EUROPE',
            u'http://cnn.com/TRAVEL', u'http://cnn.com/cnni',
            u'http://cnn.com/SPORT', u'http://cnn.com/mostpopular',
            u'http://arabic.cnn.com', u'http://cnn.com/WORLD',
            u'http://cnn.com/LATINAMERICA', u'http://us.cnn.com',
            u'http://travel.cnn.com', u'http://mexico.cnn.com',
            u'http://cnn.com/SHOWBIZ', u'http://edition.cnn.com',
            u'http://amanpour.blogs.cnn.com', u'http://money.cnn.com',
            u'http://cnn.com/tools/index.html', u'http://cnnespanol.cnn.com',
            u'http://cnn.com/CNNI', u'http://business.blogs.cnn.com',
            u'http://cnn.com/AFRICA', u'http://cnn.com/TECH',
            u'http://cnn.com/BUSINESS']
        FEEDS = [u'http://rss.cnn.com/rss/edition.rss']
        BRAND = 'cnn'

        s = Source('http://cnn.com', verbose=False, memoize_articles=False)
        url_re = re.compile(".*cnn\.com")
        mock_response_with(url_re, 'cnn_main_site')
        s.clean_memo_cache()
        s.build()

        assert s.brand == BRAND
        assert s.description == DESC
        assert s.size() == 266
        assert s.category_urls() == CATEGORY_URLS
        # TODO: A lot of the feed extraction is NOT being tested because feeds
        # are primarly extracted from the HTML of category URLs. We lose this
        # effect by just mocking CNN's main page HTML. Warning: tedious fix.
        assert s.feed_urls() == FEEDS

    @print_test
    @responses.activate
    def test_cache_categories(self):
        """Builds two same source objects in a row examines speeds of both
        """
        url = 'http://uk.yahoo.com'
        mock_response_with(url, 'yahoo_main_site')
        s = Source(url)
        s.download()
        s.parse()
        s.set_categories()

        saved_urls = s.category_urls()
        s.categories = []
        s.set_categories()
        assert sorted(s.category_urls()) == sorted(saved_urls)


class UrlTestCase(unittest.TestCase):
    def runTest(self):
        self.test_valid_urls()

    @print_test
    def test_valid_urls(self):
        """Prints out a list of urls with our heuristic guess if it is a
        valid news url purely based on the url
        """
        from newspaper.urls import valid_url

        with open(os.path.join(TEST_DIR, 'data/test_urls.txt'), 'r') as f:
            lines = f.readlines()
            test_tuples = [tuple(l.strip().split(' ')) for l in lines]
            # tuples are ('1', 'url_goes_here') form, '1' means valid,
            # '0' otherwise

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
        """Normalizes a url, removes arguments, hashtags. If a relative url, it
        merges it with the source domain to make an abs url, etc
        """
        pass


class APITestCase(unittest.TestCase):
    def runTest(self):
        # self.test_source_build()
        self.test_article_build()
        self.test_hot_trending()
        self.test_popular_urls()

    @print_test
    def test_source_build(self):
        huff_paper = newspaper.build(
            'http://www.huffingtonpost.com/', dry=True)
        assert isinstance(huff_paper, Source) is True

    @print_test
    def test_article_build(self):
        url = ('http://abcnews.go.com/blogs/politics/2013/12/'
               'states-cite-surge-in-obamacare-sign-ups-ahead'
               '-of-first-deadline/')
        article = newspaper.build_article(url)
        assert isinstance(article, Article) is True
        article.build()
        article.nlp()

    @print_test
    def test_hot_trending(self):
        """Grab google trending, just make sure this runs
        """
        newspaper.hot()

    @print_test
    def test_popular_urls(self):
        """Just make sure this method runs
        """
        newspaper.popular_urls()


class EncodingTestCase(unittest.TestCase):
    def runTest(self):
        self.test_encode_val()
        self.test_smart_unicode()
        self.test_smart_str()

    def setUp(self):
        self.uni_string = u"∆ˆˆø∆ßåßlucas yang˜"
        self.normal_string = "∆ƒˆƒ´´lucas yang"

    @print_test
    def test_encode_val(self):
        assert encodeValue(self.uni_string) == self.uni_string
        assert encodeValue(self.normal_string) == u'∆ƒˆƒ´´lucas yang'

    @print_test
    def test_smart_unicode(self):
        assert smart_unicode(self.uni_string) == self.uni_string
        assert smart_unicode(self.normal_string) == u'∆ƒˆƒ´´lucas yang'

    @print_test
    def test_smart_str(self):
        assert smart_str(self.uni_string) == "∆ˆˆø∆ßåßlucas yang˜"
        assert smart_str(self.normal_string) == "∆ƒˆƒ´´lucas yang"


class MThreadingTestCase(unittest.TestCase):
    def runTest(self):
        self.test_download_works()

    @print_test
    def test_download_works(self):
        config = Configuration()
        config.memoize_articles = False
        slate_paper = newspaper.build('http://slate.com', config=config)
        tc_paper = newspaper.build('http://techcrunch.com', config=config)
        espn_paper = newspaper.build('http://espn.com', config=config)

        print ('Slate has %d articles TC has %d articles ESPN has %d articles'
               % (slate_paper.size(), tc_paper.size(), espn_paper.size()))

        papers = [slate_paper, tc_paper, espn_paper]
        news_pool.set(papers, threads_per_source=2)

        news_pool.join()

        print 'Downloaded Slate mthread len', len(slate_paper.articles[0].html)
        print 'Downloaded ESPN mthread len', len(espn_paper.articles[-1].html)
        print 'Downloaded TC mthread len', len(tc_paper.articles[1].html)


class ConfigBuildTestCase(unittest.TestCase):
    def runTest(self):
        self.test_config_build()

    @print_test
    def test_config_build(self):
        """Test if our **kwargs to config building setup actually works.
        NOTE: No need to mock responses as we are just initializing the
        objects, not actually calling download(..)
        """
        a = Article(url='http://www.cnn.com/2013/11/27/'
                    'travel/weather-thanksgiving/index.html')
        assert a.config.language == 'en'
        assert a.config.memoize_articles is True
        assert a.config.use_meta_language is True

        a = Article(url='http://www.cnn.com/2013/11/27/travel/'
                    'weather-thanksgiving/index.html',
                    language='zh', memoize_articles=False)
        assert a.config.language == 'zh'
        assert a.config.memoize_articles is False
        assert a.config.use_meta_language is False

        s = Source(url='http://cnn.com')
        assert s.config.language == 'en'
        assert s.config.MAX_FILE_MEMO == 20000
        assert s.config.memoize_articles is True
        assert s.config.use_meta_language is True

        s = Source(url="http://cnn.com", memoize_articles=False,
                   MAX_FILE_MEMO=10000, language='en')
        assert s.config.memoize_articles is False
        assert s.config.MAX_FILE_MEMO == 10000
        assert s.config.language == 'en'
        assert s.config.use_meta_language is False


class MultiLanguageTestCase(unittest.TestCase):
    def runTest(self):
        self.test_chinese_fulltext_extract()
        self.test_arabic_fulltext_extract()
        self.test_spanish_fulltext_extract()

    @print_test
    def test_chinese_fulltext_extract(self):
        url = 'http://news.sohu.com/20050601/n225789219.shtml'
        mock_response_with(url, 'chinese_article')
        article = Article(url=url, language='zh')
        article.build()
        with codecs.open(os.path.join(TEXT_FN, 'chinese.txt'),
                         'r', 'utf8') as f:
            assert article.text == f.read()

    @print_test
    def test_arabic_fulltext_extract(self):
        url = 'http://arabic.cnn.com/2013/middle_east/8/3/syria.clashes/'\
              'index.html'
        mock_response_with(url, 'arabic_article')
        article = Article(url=url)
        article.build()
        assert article.meta_lang == 'ar'
        with codecs.open(os.path.join(TEXT_FN, 'arabic.txt'),
                         'r', 'utf8') as f:
            assert article.text == f.read()

    @print_test
    def test_spanish_fulltext_extract(self):
        url = 'http://ultimahora.es/mallorca/noticia/noticias/local/fiscal'\
              'ia-anticorrupcion-estudia-recurre-imputacion-infanta.html'
        mock_response_with(url, 'spanish_article')
        article = Article(url=url, language='es')
        article.build()
        with codecs.open(os.path.join(TEXT_FN, 'spanish.txt'),
                         'r', 'utf8') as f:
            assert article.text == f.read()


if __name__ == '__main__':
    # unittest.main()  # run all units and their cases

    suite = unittest.TestSuite()

    suite.addTest(ConfigBuildTestCase())
    suite.addTest(MultiLanguageTestCase())
    suite.addTest(SourceTestCase())
    suite.addTest(EncodingTestCase())
    suite.addTest(UrlTestCase())
    suite.addTest(ArticleTestCase())
    suite.addTest(APITestCase())
    unittest.TextTestRunner().run(suite)

    # suite.addTest(MThreadingTestCase())
