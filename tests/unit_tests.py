# -*- coding: utf-8 -*-
"""
All unit tests for the newspaper library should be contained in this file.
"""
import sys
import os
import unittest
import time
import traceback
import re
from collections import defaultdict, OrderedDict
import concurrent.futures

TEST_DIR = os.path.abspath(os.path.dirname(__file__))
PARENT_DIR = os.path.join(TEST_DIR, '..')

# newspaper's unit tests are in their own separate module, so
# insert the parent directory manually to gain scope of the
# core module
sys.path.insert(0, PARENT_DIR)

TEXT_FN = os.path.join(TEST_DIR, 'data', 'text')
HTML_FN = os.path.join(TEST_DIR, 'data', 'html')
URLS_FILE = os.path.join(TEST_DIR, 'data', 'fulltext_url_list.txt')

import newspaper
from newspaper import Article, fulltext, Source, ArticleException, news_pool
from newspaper.article import ArticleDownloadState
from newspaper.configuration import Configuration
from newspaper.urls import get_domain


def print_test(method):
    """
    Utility method for print verbalizing test suite, prints out
    time taken for test and functions name, and status
    """

    def run(*args, **kw):
        ts = time.time()
        print('\ttesting function %r' % method.__name__)
        method(*args, **kw)
        te = time.time()
        print('\t[OK] in %r %2.2f sec' % (method.__name__, te - ts))

    return run


def mock_resource_with(filename, resource_type):
    """
    Mocks an HTTP request by pulling text from a pre-downloaded file
    """
    VALID_RESOURCES = ['html', 'txt']
    if resource_type not in VALID_RESOURCES:
        raise Exception('Mocked resource must be one of: %s' %
                        ', '.join(VALID_RESOURCES))
    subfolder = 'text' if resource_type == 'txt' else 'html'
    resource_path = os.path.join(TEST_DIR, "data/%s/%s.%s" %
                                 (subfolder, filename, resource_type))
    with open(resource_path, 'r', encoding='utf-8') as f:
        return f.read()


def get_base_domain(url):
    """
    For example, the base url of uk.reuters.com => reuters.com
    """
    domain = get_domain(url)
    tld = '.'.join(domain.split('.')[-2:])
    if tld in ['co.uk', 'com.au', 'au.com']:  # edge cases
        end_chunks = domain.split('.')[-3:]
    else:
        end_chunks = domain.split('.')[-2:]
    base_domain = '.'.join(end_chunks)
    return base_domain


def check_url(*args, **kwargs):
    return ExhaustiveFullTextCase.check_url(*args, **kwargs)


@unittest.skipIf('fulltext' not in sys.argv, 'Skipping fulltext tests')
class ExhaustiveFullTextCase(unittest.TestCase):
    @staticmethod
    def check_url(args):
        """
        :param (basestr, basestr) url, res_filename:
        :return: (pubdate_failed, fulltext_failed)
        """
        url, res_filename = args
        pubdate_failed, fulltext_failed = False, False
        html = mock_resource_with(res_filename, 'html')
        try:
            a = Article(url)
            a.download(html)
            a.parse()
            if a.publish_date is None:
                pubdate_failed = True
        except Exception:
            print('<< URL: %s parse ERROR >>' % url)
            traceback.print_exc()
            pubdate_failed, fulltext_failed = True, True
        else:
            correct_text = mock_resource_with(res_filename, 'txt')
            if not (a.text == correct_text):
                # print('Diff: ', simplediff.diff(correct_text, a.text))
                # `correct_text` holds the reason of failure if failure
                print('%s -- %s -- %s' %
                      ('Fulltext failed',
                       res_filename, correct_text.strip()))
                fulltext_failed = True
                # TODO: assert statements are commented out for full-text
                # extraction tests because we are constantly tweaking the
                # algorithm and improving
                # assert a.text == correct_text
        return pubdate_failed, fulltext_failed

    @print_test
    def test_exhaustive(self):
        with open(URLS_FILE, 'r') as f:
            urls = [d.strip() for d in f.readlines() if d.strip()]

        domain_counters = {}

        def get_filename(url):
            domain = get_base_domain(url)
            domain_counters[domain] = domain_counters.get(domain, 0) + 1
            return '{}{}'.format(domain, domain_counters[domain])

        filenames = map(get_filename, urls)

        with concurrent.futures.ProcessPoolExecutor() as executor:
            test_results = list(executor.map(check_url, zip(urls, filenames)))

        total_pubdates_failed, total_fulltext_failed = \
            list(map(sum, zip(*test_results)))

        print('%s fulltext extractions failed out of %s' %
              (total_fulltext_failed, len(urls)))
        print('%s pubdate extractions failed out of %s' %
              (total_pubdates_failed, len(urls)))
        self.assertGreaterEqual(47, total_pubdates_failed)
        self.assertGreaterEqual(20, total_fulltext_failed)


class ArticleTestCase(unittest.TestCase):
    def setup_stage(self, stage_name):
        stages = OrderedDict([
            ('initial', lambda: None),
            ('download', lambda: self.article.download(
                mock_resource_with('cnn_article', 'html'))),
            ('parse', lambda: self.article.parse()),
            ('meta', lambda: None),  # Alias for nlp
            ('nlp', lambda: self.article.nlp())
        ])
        assert stage_name in stages
        for name, action in stages.items():
            if name == stage_name:
                break
            action()

    def setUp(self):
        """Called before the first test case of this unit begins
        """
        self.article = Article(
            url='http://www.cnn.com/2013/11/27/travel/weather-'
                'thanksgiving/index.html?iref=allsearch')

    @print_test
    def test_url(self):
        self.assertEqual(
            'http://www.cnn.com/2013/11/27/travel/weather-'
            'thanksgiving/index.html?iref=allsearch',
            self.article.url)

    @print_test
    def test_download_html(self):
        self.setup_stage('download')
        html = mock_resource_with('cnn_article', 'html')
        self.article.download(html)
        self.assertEqual(self.article.download_state, ArticleDownloadState.SUCCESS)
        self.assertEqual(self.article.download_exception_msg, None)
        self.assertEqual(75406, len(self.article.html))

    @print_test
    def test_meta_refresh_redirect(self):
        # TODO: We actually hit example.com in this unit test ... which is bad
        # Figure out how to mock an actual redirect
        config = Configuration()
        config.follow_meta_refresh = True
        article = Article(
            '', config=config)
        html = mock_resource_with('google_meta_refresh', 'html')
        article.download(input_html=html)
        article.parse()
        self.assertEqual(article.title, 'Example Domain')

    @print_test
    def test_meta_refresh_no_url_redirect(self):
        config = Configuration()
        config.follow_meta_refresh = True
        article = Article(
            '', config=config)
        html = mock_resource_with('ap_meta_refresh', 'html')
        article.download(input_html=html)
        article.parse()
        self.assertEqual(article.title, 'News from The Associated Press')

    @print_test
    def test_pre_download_parse(self):
        """Calling `parse()` before `download()` should yield an error
        """
        article = Article(self.article.url)
        self.assertRaises(ArticleException, article.parse)

    @print_test
    def test_parse_html(self):
        self.setup_stage('parse')

        AUTHORS = ['Chien-Ming Wang', 'Dana A. Ford', 'James S.A. Corey',
                   'Tom Watkins']
        TITLE = 'After storm, forecasters see smooth sailing for Thanksgiving'
        LEN_IMGS = 46
        META_LANG = 'en'
        META_SITE_NAME = 'CNN'

        self.article.parse()
        self.article.nlp()

        text = mock_resource_with('cnn', 'txt')
        self.assertEqual(text, self.article.text)
        self.assertEqual(text, fulltext(self.article.html))

        # NOTE: top_img extraction requires an internet connection
        # unlike the rest of this test file
        TOP_IMG = ('http://i2.cdn.turner.com/cnn/dam/assets/131129200805-'
                   '01-weather-1128-story-top.jpg')
        self.assertEqual(TOP_IMG, self.article.top_img)

        self.assertCountEqual(AUTHORS, self.article.authors)
        self.assertEqual(TITLE, self.article.title)
        self.assertEqual(LEN_IMGS, len(self.article.imgs))
        self.assertEqual(META_LANG, self.article.meta_lang)
        self.assertEqual(META_SITE_NAME, self.article.meta_site_name)
        self.assertEqual('2013-11-27 00:00:00', str(self.article.publish_date))

    @print_test
    def test_meta_type_extraction(self):
        self.setup_stage('meta')
        meta_type = self.article.extractor.get_meta_type(
            self.article.clean_doc)
        self.assertEqual('article', meta_type)

    @print_test
    def test_meta_extraction(self):
        self.setup_stage('meta')
        meta = self.article.extractor.get_meta_data(self.article.clean_doc)
        META_DATA = defaultdict(dict, {
            'medium': 'news',
            'googlebot': 'noarchive',
            'pubdate': '2013-11-27T08:36:32Z',
            'title': 'After storm, forecasters see smooth sailing for Thanksgiving - CNN.com',
            'og': {'site_name': 'CNN',
                   'description': 'A strong storm struck much of the eastern United States on Wednesday, complicating holiday plans for many of the 43 million Americans expected to travel.',
                   'title': 'After storm, forecasters see smooth sailing for Thanksgiving',
                   'url': 'http://www.cnn.com/2013/11/27/travel/weather-thanksgiving/index.html',
                   'image': 'http://i2.cdn.turner.com/cnn/dam/assets/131129200805-01-weather-1128-story-top.jpg',
                   'type': 'article'},
            'section': 'travel',
            'author': 'Dana A. Ford, James S.A. Corey, Chien-Ming Wang, and Tom Watkins, CNN',
            'robots': 'index,follow',
            'vr': {
                'canonical': 'http://edition.cnn.com/2013/11/27/travel/weather-thanksgiving/index.html'},
            'source': 'CNN',
            'fb': {'page_id': 18793419640, 'app_id': 80401312489},
            'keywords': 'winter storm,holiday travel,Thanksgiving storm,Thanksgiving winter storm',
            'article': {
                'publisher': 'https://www.facebook.com/cnninternational'},
            'lastmod': '2013-11-28T02:03:23Z',
            'twitter': {'site': {'identifier': '@CNNI', 'id': 2097571},
                        'card': 'summary',
                        'creator': {'identifier': '@cnntravel',
                                    'id': 174377718}},
            'viewport': 'width=1024',
            'news_keywords': 'winter storm,holiday travel,Thanksgiving storm,Thanksgiving winter storm'
        })

        self.assertDictEqual(META_DATA, meta)

        # if the value for a meta key is another dict, that dict ought to be
        # filled with keys and values
        dict_values = [v for v in list(meta.values()) if isinstance(v, dict)]
        self.assertTrue(all([len(d) > 0 for d in dict_values]))

        # there are exactly 5 top-level "og:type" type keys
        is_dict = lambda v: isinstance(v, dict)
        self.assertEqual(5, len([i for i in meta.values() if is_dict(i)]))

        # there are exactly 12 top-level "pubdate" type keys
        is_string = lambda v: isinstance(v, str)
        self.assertEqual(12, len([i for i in meta.values() if is_string(i)]))

    @print_test
    def test_pre_download_nlp(self):
        """Test running NLP algos before even downloading the article
        """
        self.setup_stage('initial')
        new_article = Article(self.article.url)
        self.assertRaises(ArticleException, new_article.nlp)

    @print_test
    def test_pre_parse_nlp(self):
        """Test running NLP algos before parsing the article
        """
        self.setup_stage('parse')
        self.assertRaises(ArticleException, self.article.nlp)

    @print_test
    def test_nlp_body(self):
        self.setup_stage('nlp')
        self.article.nlp()
        KEYWORDS = ['balloons', 'delays', 'flight', 'forecasters',
                    'good', 'sailing', 'smooth', 'storm', 'thanksgiving',
                    'travel', 'weather', 'winds', 'york']
        SUMMARY = mock_resource_with('cnn_summary', 'txt')
        self.assertEqual(SUMMARY, self.article.summary)
        self.assertCountEqual(KEYWORDS, self.article.keywords)


class TestDownloadScheme(unittest.TestCase):
    @print_test
    def test_download_file_success(self):
        url = "file://" + os.path.join(HTML_FN, "cnn_article.html")
        article = Article(url=url)
        article.download()
        self.assertEqual(article.download_state, ArticleDownloadState.SUCCESS)
        self.assertEqual(article.download_exception_msg, None)
        self.assertEqual(75406, len(article.html))

    @print_test
    def test_download_file_failure(self):
        url = "file://" + os.path.join(HTML_FN, "does_not_exist.html")
        article = Article(url=url)
        article.download()
        self.assertEqual(0, len(article.html))
        self.assertEqual(article.download_state, ArticleDownloadState.FAILED_RESPONSE)
        self.assertEqual(article.download_exception_msg, "No such file or directory")


class ContentExtractorTestCase(unittest.TestCase):
    """Test specific element extraction cases"""

    def setUp(self):
        self.extractor = newspaper.extractors.ContentExtractor(Configuration())
        self.parser = newspaper.parsers.Parser

    def _get_title(self, html):
        doc = self.parser.fromstring(html)
        return self.extractor.get_title(doc)

    def test_get_title_basic(self):
        html = '<title>Test title</title>'
        self.assertEqual(self._get_title(html), 'Test title')

    def test_get_title_split(self):
        html = '<title>Test page » Test title</title>'
        self.assertEqual(self._get_title(html), 'Test title')

    def test_get_title_split_escaped(self):
        html = '<title>Test page &raquo; Test title</title>'
        self.assertEqual(self._get_title(html), 'Test title')

    def test_get_title_quotes(self):
        title = 'Test page and «something in quotes»'
        html = '<title>{}</title>'.format(title)
        self.assertEqual(self._get_title(html), title)

    def _get_canonical_link(self, article_url, html):
        doc = self.parser.fromstring(html)
        return self.extractor.get_canonical_link(article_url, doc)

    def test_get_canonical_link_rel_canonical(self):
        url = 'http://www.example.com/article.html'
        html = '<link rel="canonical" href="{}">'.format(url)
        self.assertEqual(self._get_canonical_link('', html), url)

    def test_get_canonical_link_rel_canonical_absolute_url(self):
        url = 'http://www.example.com/article.html'
        html = '<link rel="canonical" href="article.html">'
        article_url = 'http://www.example.com/article?foo=bar'
        self.assertEqual(self._get_canonical_link(article_url, html), url)

    def test_get_canonical_link_og_url_absolute_url(self):
        url = 'http://www.example.com/article.html'
        html = '<meta property="og:url" content="article.html">'
        article_url = 'http://www.example.com/article?foo=bar'
        self.assertEqual(self._get_canonical_link(article_url, html), url)

    def test_get_canonical_link_hostname_og_url_absolute_url(self):
        url = 'http://www.example.com/article.html'
        html = '<meta property="og:url" content="www.example.com/article.html">'
        article_url = 'http://www.example.com/article?foo=bar'
        self.assertEqual(self._get_canonical_link(article_url, html), url)

    def test_get_top_image_from_meta(self):
        html = '<meta property="og:image" content="https://example.com/meta_img_filename.jpg" />' \
               '<meta name="og:image" content="https://example.com/meta_another_img_filename.jpg"/>'
        html_empty_og_content = '<meta property="og:image" content="" />' \
            '<meta name="og:image" content="https://example.com/meta_another_img_filename.jpg"/>'
        html_empty_all = '<meta property="og:image" content="" />' \
            '<meta name="og:image" />'
        html_rel_img_src = html_empty_all + '<link rel="img_src" href="https://example.com/meta_link_image.jpg" />'
        html_rel_img_src2 = html_empty_all + '<link rel="image_src" href="https://example.com/meta_link_image2.jpg" />'
        html_rel_icon = html_empty_all + '<link rel="icon" href="https://example.com/meta_link_rel_icon.ico" />'

        doc = self.parser.fromstring(html)
        self.assertEqual(
            self.extractor.get_meta_img_url('http://www.example.com/article?foo=bar', doc),
            'https://example.com/meta_img_filename.jpg'
        )
        doc = self.parser.fromstring(html_empty_og_content)
        self.assertEqual(
            self.extractor.get_meta_img_url('http://www.example.com/article?foo=bar', doc),
            'https://example.com/meta_another_img_filename.jpg'
        )
        doc = self.parser.fromstring(html_empty_all)
        self.assertEqual(
            self.extractor.get_meta_img_url('http://www.example.com/article?foo=bar', doc),
            ''
        )
        doc = self.parser.fromstring(html_rel_img_src)
        self.assertEqual(
            self.extractor.get_meta_img_url('http://www.example.com/article?foo=bar', doc),
            'https://example.com/meta_link_image.jpg'
        )
        doc = self.parser.fromstring(html_rel_img_src2)
        self.assertEqual(
            self.extractor.get_meta_img_url('http://www.example.com/article?foo=bar', doc),
            'https://example.com/meta_link_image2.jpg'
        )
        doc = self.parser.fromstring(html_rel_icon)
        self.assertEqual(
            self.extractor.get_meta_img_url('http://www.example.com/article?foo=bar', doc),
            'https://example.com/meta_link_rel_icon.ico'
        )


class SourceTestCase(unittest.TestCase):
    @print_test
    def test_source_url_input_none(self):
        with self.assertRaises(Exception):
            Source(url=None)

    @unittest.skip("Need to mock download")
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

    @unittest.skip("Need to mock download")
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
        self.assertCountEqual(saved_urls, s.category_urls())


class UrlTestCase(unittest.TestCase):
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

        for lst, url in test_tuples:
            truth_val = bool(int(lst))
            try:
                self.assertEqual(truth_val, valid_url(url, test=True))
            except AssertionError:
                print('\t\turl: %s is supposed to be %s' % (url, truth_val))
                raise


    @print_test
    def test_pubdate(self):
        """Checks that irrelevant data in url isn't considered as publishing date"""
        from newspaper.urls import STRICT_DATE_REGEX

        with open(os.path.join(TEST_DIR, 'data/test_urls_pubdate.txt'), 'r') as f:
            lines = f.readlines()
            test_tuples = [tuple(l.strip().split(' ')) for l in lines]
            # tuples are ('1', 'url_goes_here') form, '1' means publishing date
            # is present in the url, '0' otherwise

            for pubdate, url in test_tuples:
                is_present = bool(int(pubdate))
                date_match = re.search(STRICT_DATE_REGEX, url)
                try:
                    self.assertEqual(is_present, bool(date_match))
                except AssertionError:
                    if is_present:
                        print('\t\tpublishing date in %s should be present' % (url))
                    else:
                        print('\t\tpublishing date in %s should not be present' % (url))
                    raise


    @unittest.skip("Need to write an actual test")
    @print_test
    def test_prepare_url(self):
        """Normalizes a url, removes arguments, hashtags. If a relative url, it
        merges it with the source domain to make an abs url, etc
        """
        from newspaper.urls import prepare_url

        with open(os.path.join(TEST_DIR, 'data/test_prepare_urls.txt'), 'r') as f:
            lines = f.readlines()
            test_tuples = [tuple(l.strip().split(' ')) for l in lines]
            # tuples are ('real_url', 'url_path', 'source_url') form

        for real, url, source in test_tuples:
            try:
                self.assertEqual(real, prepare_url(url, source))
            except AssertionError:
                print('\t\turl: %s + %s is supposed to be %s' % (url, source, real))
                raise


class APITestCase(unittest.TestCase):
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


@unittest.skip("Need to mock download")
class MThreadingTestCase(unittest.TestCase):
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
    """Test if our **kwargs to config building setup actually works.
    NOTE: No need to mock responses as we are just initializing the
    objects, not actually calling download(..)
    """
    @print_test
    def test_article_default_params(self):

        a = Article(url='http://www.cnn.com/2013/11/27/'
                        'travel/weather-thanksgiving/index.html')
        self.assertEqual('en', a.config.language)
        self.assertTrue(a.config.memoize_articles)
        self.assertTrue(a.config.use_meta_language)

    @print_test
    def test_article_custom_params(self):
        a = Article(url='http://www.cnn.com/2013/11/27/travel/'
                        'weather-thanksgiving/index.html',
                    language='zh', memoize_articles=False)
        self.assertEqual('zh', a.config.language)
        self.assertFalse(a.config.memoize_articles)
        self.assertFalse(a.config.use_meta_language)

    @print_test
    def test_source_default_params(self):
        s = Source(url='http://cnn.com')
        self.assertEqual('en', s.config.language)
        self.assertEqual(20000, s.config.MAX_FILE_MEMO)
        self.assertTrue(s.config.memoize_articles)
        self.assertTrue(s.config.use_meta_language)

    @print_test
    def test_source_custom_params(self):
        s = Source(url="http://cnn.com", memoize_articles=False,
                   MAX_FILE_MEMO=10000, language='en')
        self.assertFalse(s.config.memoize_articles)
        self.assertEqual(10000, s.config.MAX_FILE_MEMO)
        self.assertEqual('en', s.config.language)
        self.assertFalse(s.config.use_meta_language)


class MultiLanguageTestCase(unittest.TestCase):
    @print_test
    def test_chinese_fulltext_extract(self):
        url = 'http://news.sohu.com/20050601/n225789219.shtml'
        article = Article(url=url, language='zh')
        html = mock_resource_with('chinese_article', 'html')
        article.download(html)
        article.parse()
        text = mock_resource_with('chinese', 'txt')
        self.assertEqual(text, article.text)
        self.assertEqual(text, fulltext(article.html, 'zh'))

    @print_test
    def test_arabic_fulltext_extract(self):
        url = 'http://arabic.cnn.com/2013/middle_east/8/3/syria.clashes/' \
              'index.html'
        article = Article(url=url)
        html = mock_resource_with('arabic_article', 'html')
        article.download(html)
        article.parse()
        self.assertEqual('ar', article.meta_lang)
        text = mock_resource_with('arabic', 'txt')
        self.assertEqual(text, article.text)
        self.assertEqual(text, fulltext(article.html, 'ar'))

    @print_test
    def test_spanish_fulltext_extract(self):
        url = 'http://ultimahora.es/mallorca/noticia/noticias/local/fiscal' \
              'ia-anticorrupcion-estudia-recurre-imputacion-infanta.html'
        article = Article(url=url, language='es')
        html = mock_resource_with('spanish_article', 'html')
        article.download(html)
        article.parse()
        text = mock_resource_with('spanish', 'txt')
        self.assertEqual(text, article.text)
        self.assertEqual(text, fulltext(article.html, 'es'))

    @print_test
    def test_japanese_fulltext_extract(self):
        url = 'https://www.nikkei.com/article/DGXMZO31897660Y8A610C1000000/?n_cid=DSTPCS001'
        article = Article(url=url, language='ja')
        html = mock_resource_with('japanese_article', 'html')
        article.download(html)
        article.parse()
        text = mock_resource_with('japanese', 'txt')
        self.assertEqual(text, article.text)
        self.assertEqual(text, fulltext(article.html, 'ja'))

    @print_test
    def test_japanese_fulltext_extract2(self):
        url = 'http://www.afpbb.com/articles/-/3178894'
        article = Article(url=url, language='ja')
        html = mock_resource_with('japanese_article2', 'html')
        article.download(html)
        article.parse()
        text = mock_resource_with('japanese2', 'txt')
        self.assertEqual(text, article.text)
        self.assertEqual(text, fulltext(article.html, 'ja'))

    @print_test
    def test_thai_fulltext_extract(self):
        url = 'https://prachatai.com/journal/2019/01/80642'
        article = Article(url=url, language='th')
        html = mock_resource_with('thai_article', 'html')
        article.download(html)
        article.parse()
        text = mock_resource_with('thai', 'txt')
        self.assertEqual(text, article.text)
        self.assertEqual(text, fulltext(article.html, 'th'))


class TestNewspaperLanguagesApi(unittest.TestCase):
    @print_test
    def test_languages_api_call(self):
        newspaper.languages()


class TestDownloadPdf(unittest.TestCase):

    @print_test
    def test_article_pdf_ignoring(self):
        empty_pdf = "%PDF-"  # empty PDF constant
        a = Article(url='http://www.technik-medien.at/ePaper_Download/'
                        'IoT4Industry+Business_2018-10-31_2018-03.pdf',
                    ignored_content_types_defaults={"application/pdf": empty_pdf,
                                                    "application/x-pdf": empty_pdf,
                                                    "application/x-bzpdf": empty_pdf,
                                                    "application/x-gzpdf": empty_pdf})
        a.download()
        self.assertEqual(empty_pdf, a.html)

    @print_test
    def test_article_pdf_fetching(self):
        a = Article(url='https://www.adobe.com/pdf/pdfs/ISO32000-1PublicPatentLicense.pdf')
        a.download()
        self.assertNotEqual('%PDF-', a.html)

if __name__ == '__main__':
    argv = list(sys.argv)
    if 'fulltext' in argv:
        argv.remove('fulltext')  # remove it here, so it doesn't pass to unittest

    unittest.main(verbosity=0, argv=argv)
