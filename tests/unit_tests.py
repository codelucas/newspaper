# -*- coding: utf-8 -*-
"""
All unit tests for the newspaper library should be contained in this file.
"""
from __future__ import print_function
import codecs
import sys
import os
# import simplediff
import unittest
import time
import traceback
from collections import defaultdict

TEST_DIR = os.path.abspath(os.path.dirname(__file__))
PARENT_DIR = os.path.join(TEST_DIR, '..')

# newspaper's unit tests are in their own seperate module, so
# insert the parent directory manually to gain scope of the
# core module
sys.path.insert(0, PARENT_DIR)

TEXT_FN = os.path.join(TEST_DIR, 'data/text')
HTML_FN = os.path.join(TEST_DIR, 'data/html')
URLS_FILE = os.path.join(TEST_DIR, 'data/fulltext_url_list.txt')

import newspaper
from newspaper import (
    Article, fulltext, Source, ArticleException, news_pool)
from newspaper.configuration import Configuration
from newspaper.urls import get_domain


# from newspaper import Config
# from newspaper.network import multithread_request
# from newspaper.text import (StopWords, StopWordsArabic,
#                             StopWordsKorean, StopWordsChinese)


def print_test(method):
    """Utility method for print verbalizing test suite, prints out
    time taken for test and functions name, and status
    """
    def run(*args, **kw):
        ts = time.time()
        print('\ttesting function %r' % method.__name__)
        method(*args, **kw)
        te = time.time()
        print('\t[OK] in %r %2.2f sec' % (method.__name__, te-ts))
    return run


def mock_resource_with(filename, resource_type):
    """Mocks an HTTP request by pulling text from a pre-downloaded file
    """
    VALID_RESOURCES = ['html', 'txt']
    if resource_type not in VALID_RESOURCES:
        raise Exception('Mocked resource must be one of: %s' %
                        ', '.join(VALID_RESOURCES))
    subfolder = 'text' if resource_type == 'txt' else 'html'
    resource_path = os.path.join(TEST_DIR, "data/%s/%s.%s" %
                                 (subfolder, filename, resource_type))
    with codecs.open(resource_path, 'r', 'utf8') as f:
        return f.read()


def get_base_domain(url):
    """For example, the base url of uk.reuters.com => reuters.com
    """
    domain = get_domain(url)
    tld = '.'.join(domain.split('.')[-2:])
    if tld in ['co.uk', 'com.au', 'au.com']:  # edge cases
        end_chunks = domain.split('.')[-3:]
    else:
        end_chunks = domain.split('.')[-2:]
    base_domain = '.'.join(end_chunks)
    return base_domain


class ExhaustiveFullTextCase(unittest.TestCase):

    @print_test
    def runTest(self):
        domain_counters = {}

        with open(URLS_FILE, 'r') as f:
            urls = [d.strip() for d in f.readlines() if d.strip()]

        fulltext_failed = 0
        pubdates_failed = 0
        for url in urls:
            domain = get_base_domain(url)
            if domain in domain_counters:
                domain_counters[domain] += 1
            else:
                domain_counters[domain] = 1

            res_filename = domain + str(domain_counters[domain])
            html = mock_resource_with(res_filename, 'html')
            try:
                a = Article(url)
                a.download(html)
                a.parse()
                if a.publish_date is None:
                    pubdates_failed += 1
            except Exception:
                print('<< URL: %s parse ERROR >>' % url)
                traceback.print_exc()
                continue

            correct_text = mock_resource_with(res_filename, 'txt')
            if not (a.text == correct_text):
                # print('Diff: ', simplediff.diff(correct_text, a.text))
                # `correct_text` holds the reason of failure if failure
                print('%s -- %s -- %s' %
                      ('Fulltext failed', res_filename, correct_text.strip()))
                fulltext_failed += 1
            # TODO: assert statements are commented out for full-text
            # extraction tests because we are constantly tweaking the
            # algorithm and improving
            # assert a.text == correct_text
        print('%s fulltext extractions failed out of %s' %
              (fulltext_failed, len(urls)))
        print('%s pubdate extractions failed out of %s' %
              (pubdates_failed, len(urls)))
        assert pubdates_failed == 47
        assert fulltext_failed == 20


class ArticleTestCase(unittest.TestCase):
    def runTest(self):
        self.test_url()
        self.test_download_html()
        self.test_pre_download_parse()
        self.test_parse_html()
        self.test_meta_type_extraction()
        self.test_meta_extraction()
        self.test_pre_download_nlp()
        self.test_pre_parse_nlp()
        self.test_nlp_body()

    def setUp(self):
        """Called before the first test case of this unit begins
        """
        self.article = Article(
            url='http://www.cnn.com/2013/11/27/travel/weather-'
                'thanksgiving/index.html?iref=allsearch')

    def tearDown(self):
        """Called after all cases have been completed, intended to
        free resources and etc
        """
        pass

    @print_test
    def test_url(self):
        assert self.article.url == (
            'http://www.cnn.com/2013/11/27/travel/weather-'
            'thanksgiving/index.html?iref=allsearch')

    @print_test
    def test_download_html(self):
        html = mock_resource_with('cnn_article', 'html')
        self.article.download(html)
        assert len(self.article.html) == 75244

    @print_test
    def test_pre_download_parse(self):
        """Calling `parse()` before `download()` should yield an error
        """
        article = Article(self.article.url)
        self.assertRaises(ArticleException, article.parse)

    @print_test
    def test_parse_html(self):
        AUTHORS = ['Dana Ford', 'Tom Watkins']
        TITLE = 'After storm, forecasters see smooth sailing for Thanksgiving'
        LEN_IMGS = 46
        META_LANG = 'en'

        self.article.parse()
        self.article.nlp()

        text = mock_resource_with('cnn', 'txt')
        assert self.article.text == text
        assert fulltext(self.article.html) == text

        # NOTE: top_img extraction requires an internet connection
        # unlike the rest of this test file
        TOP_IMG = ('http://i2.cdn.turner.com/cnn/dam/assets/131129200805-'
                   '01-weather-1128-story-top.jpg')
        assert self.article.top_img == TOP_IMG

        assert sorted(self.article.authors) == AUTHORS
        assert self.article.title == TITLE
        assert len(self.article.imgs) == LEN_IMGS
        assert self.article.meta_lang == META_LANG
        assert str(self.article.publish_date) == '2013-11-27 00:00:00'

    @print_test
    def test_meta_type_extraction(self):
        meta_type = self.article.extractor.get_meta_type(
            self.article.clean_doc)
        assert 'article' == meta_type

    @print_test
    def test_meta_extraction(self):
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
        dict_values = [v for v in list(meta.values()) if isinstance(v, dict)]
        assert all([len(d) > 0 for d in dict_values])

        # there are exactly 5 top-level "og:type" type keys
        is_dict = lambda v: isinstance(v, dict)
        assert len(list(filter(is_dict, list(meta.values())))) == 5

        # there are exactly 12 top-level "pubdate" type keys
        is_string = lambda v: isinstance(v, str)
        assert len(list(filter(is_string, list(meta.values())))) == 12

    @print_test
    def test_pre_download_nlp(self):
        """Test running NLP algos before even downloading the article
        """
        new_article = Article(self.article.url)
        self.assertRaises(ArticleException, new_article.nlp)

    @print_test
    def test_pre_parse_nlp(self):
        """Test running NLP algos before parsing the article
        """
        new_article = Article(self.article.url)
        html = mock_resource_with('cnn_article', 'html')
        new_article.download(html)
        self.assertRaises(ArticleException, new_article.nlp)

    @print_test
    def test_nlp_body(self):
        KEYWORDS = [u'balloons', u'delays', u'flight', u'forecasters',
                    u'good', u'sailing', u'smooth', u'storm', u'thanksgiving',
                    u'travel', u'weather', u'winds', u'york']
        SUMMARY = mock_resource_with('cnn_summary', 'txt')

        assert self.article.summary == SUMMARY
        assert sorted(self.article.keywords) == sorted(KEYWORDS)


class SourceTestCase(unittest.TestCase):
    def runTest(self):
        self.source_url_input_none()
        self.test_cache_categories()
        self.test_source_build()

    @print_test
    def source_url_input_none(self):
        def failfunc():
            Source(url=None)
        self.assertRaises(Exception, failfunc)

    @print_test
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
            'http://cnn.com/ASIA', 'http://connecttheworld.blogs.cnn.com',
            'http://cnn.com/HLN', 'http://cnn.com/MIDDLEEAST',
            'http://cnn.com', 'http://ireport.cnn.com',
            'http://cnn.com/video', 'http://transcripts.cnn.com',
            'http://cnn.com/espanol',
            'http://partners.cnn.com', 'http://www.cnn.com',
            'http://cnn.com/US', 'http://cnn.com/EUROPE',
            'http://cnn.com/TRAVEL', 'http://cnn.com/cnni',
            'http://cnn.com/SPORT', 'http://cnn.com/mostpopular',
            'http://arabic.cnn.com', 'http://cnn.com/WORLD',
            'http://cnn.com/LATINAMERICA', 'http://us.cnn.com',
            'http://travel.cnn.com', 'http://mexico.cnn.com',
            'http://cnn.com/SHOWBIZ', 'http://edition.cnn.com',
            'http://amanpour.blogs.cnn.com', 'http://money.cnn.com',
            'http://cnn.com/tools/index.html', 'http://cnnespanol.cnn.com',
            'http://cnn.com/CNNI', 'http://business.blogs.cnn.com',
            'http://cnn.com/AFRICA', 'http://cnn.com/TECH',
            'http://cnn.com/BUSINESS']
        FEEDS = ['http://rss.cnn.com/rss/edition.rss']
        BRAND = 'cnn'

        s = Source('http://cnn.com', verbose=False, memoize_articles=False)
        # html = mock_resource_with('http://cnn.com', 'cnn_main_site')
        s.clean_memo_cache()
        s.build()

        # TODO: The rest of the source extraction features will be fully tested
        # after I figure out a way to sensibly mock the HTTP requests for all
        # of the category and feeed URLs

        # assert s.brand == BRAND
        # assert s.description == DESC
        # assert s.size() == 266
        # assert s.category_urls() == CATEGORY_URLS

        # TODO: A lot of the feed extraction is NOT being tested because feeds
        # are primarly extracted from the HTML of category URLs. We lose this
        # effect by just mocking CNN's main page HTML. Warning: tedious fix.
        # assert s.feed_urls() == FEEDS

    @print_test
    def test_cache_categories(self):
        """Builds two same source objects in a row examines speeds of both
        """
        url = 'http://uk.yahoo.com'
        html = mock_resource_with('yahoo_main_site', 'html')
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
            except AssertionError:
                print('\t\turl: %s is supposed to be %s' % (url, truth_val))
                raise

    @print_test
    def test_prepare_url(self):
        """Normalizes a url, removes arguments, hashtags. If a relative url, it
        merges it with the source domain to make an abs url, etc
        """
        pass


class APITestCase(unittest.TestCase):
    def runTest(self):
        self.test_hot_trending()
        self.test_popular_urls()

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

        print(('Slate has %d articles TC has %d articles ESPN has %d articles'
               % (slate_paper.size(), tc_paper.size(), espn_paper.size())))

        papers = [slate_paper, tc_paper, espn_paper]
        news_pool.set(papers, threads_per_source=2)

        news_pool.join()

        print('Downloaded Slate mthread len',
              len(slate_paper.articles[0].html))
        print('Downloaded ESPN mthread len',
              len(espn_paper.articles[-1].html))
        print('Downloaded TC mthread len',
              len(tc_paper.articles[1].html))


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
        article = Article(url=url, language='zh')
        html = mock_resource_with('chinese_article', 'html')
        article.download(html)
        article.parse()
        text = mock_resource_with('chinese', 'txt')
        assert article.text == text
        assert fulltext(article.html, 'zh') == text

    @print_test
    def test_arabic_fulltext_extract(self):
        url = 'http://arabic.cnn.com/2013/middle_east/8/3/syria.clashes/'\
              'index.html'
        article = Article(url=url)
        html = mock_resource_with('arabic_article', 'html')
        article.download(html)
        article.parse()
        assert article.meta_lang == 'ar'
        text = mock_resource_with('arabic', 'txt')
        assert article.text == text
        assert fulltext(article.html, 'ar') == text

    @print_test
    def test_spanish_fulltext_extract(self):
        url = 'http://ultimahora.es/mallorca/noticia/noticias/local/fiscal'\
              'ia-anticorrupcion-estudia-recurre-imputacion-infanta.html'
        article = Article(url=url, language='es')
        html = mock_resource_with('spanish_article', 'html')
        article.download(html)
        article.parse()
        text = mock_resource_with('spanish', 'txt')
        assert article.text == text
        assert fulltext(article.html, 'es') == text


if __name__ == '__main__':
    # unittest.main()  # run all units and their cases

    suite = unittest.TestSuite()

    if len(sys.argv) > 1 and sys.argv[1] == 'fulltext':
        suite.addTest(ExhaustiveFullTextCase())

    suite.addTest(ConfigBuildTestCase())
    suite.addTest(MultiLanguageTestCase())
    suite.addTest(UrlTestCase())
    suite.addTest(ArticleTestCase())
    suite.addTest(APITestCase())
    unittest.TextTestRunner().run(suite)

    # TODO: suite.addTest(SourceTestCase())
    # suite.addTest(MThreadingTestCase())
