# -*- coding: utf-8 -*-

import logging

from .network import get_html, async_request
from .article import Article
from .urls import get_domain, get_scheme, prepare_url
from .settings import ANCHOR_DIR
from .packages.tldextract import tldextract
from .packages.feedparser import feedparser
from .parsers import (
    get_lxml_root, get_urls, get_feed_urls, get_category_urls)
from .utils import (
    fix_unicode, memoize_articles, cache_disk, print_duration)

log = logging.getLogger(__name__)

class Category(object):
    def __init__(self, url):
        self.url = url
        self.html = None
        self.lxml_root = None

class Feed(object):
    def __init__(self, url):
        self.url = url
        self.rss = None
        # self.dom = None           TODO Speed up feedparser

class Source(object):
    """
    Sources are abstractions of online news
    vendors like HuffingtonPost or cnn.

    domain     =  www.cnn.com
    scheme     =  http, https
    categories =  ['http://cnn.com/world', 'http://money.cnn.com']
    feeds      =  ['http://cnn.com/rss.atom', ..]
    links      =  [<link obj>, <link obj>, ..]

    """

    def __init__(self, url=None):
        if (url is None) or ('://' not in url) or (url[:4] != 'http'):
            raise Exception

        self.url = fix_unicode(url)
        self.url = prepare_url(url)

        self.domain = get_domain(self.url)
        self.scheme = get_scheme(self.url)

        self.categories = []
        self.feeds = []
        self.articles = []

        self.html = u''
        self.lxml_root = None

        self.brand = tldextract.extract(self.url).domain
        self.description = u''

    def build(self, parse=True):
        """Encapsulates download and basic parsing with lxml. May be a
        good idea to split this into download() and parse() methods."""

        self.download()
        self.parse()

        # Can not merge category and feed tasks together because
        # computing feed urls relies on the category urls!
        self.set_category_urls()
        self.download_categories() # async
        self.parse_categories()

        self.set_feed_urls()
        self.download_feeds()      # async
        # self.parse_feeds()  TODO We are directly regexing out feeds until we speed up feedparser!

        self.generate_articles()
        self.async_download_articles()

    def purge_articles(self, articles=None):
        """delete rejected articles, if there is an articles param, we
        purge from there, otherwise purge from our source instance"""

        ret = []
        if articles is not None:
            for article in articles:
                if not article.rejected:
                    ret.append(article)
                else:
                    pass # Maybe something here in future
            return ret

        for article in self.articles:
            if not article.rejected:
                ret.append(article)

        self.articles = ret

    @cache_disk(seconds=(86400*1), cache_folder=ANCHOR_DIR)
    def _get_category_urls(self, domain):
        """the domain param is **necessary**, see .utils.cache_disk for reasons.
        the boilerplate method is so we can use this decorator right. We are
        caching categories for 1 DAY."""

        return get_category_urls(self)

    def set_category_urls(self):
        """"""

        urls = self._get_category_urls(self.domain)
        self.categories = [Category(url=url) for url in urls]

    def set_feed_urls(self):
        """don't need to cache getting feed urls, it's almost
        instant w/ xpath"""

        urls = get_feed_urls(self)
        self.feeds = [Feed(url=url) for url in urls]

    def set_description(self):
        """sets a blub for this source, for now we just
        query the desc html attribute"""

        if self.lxml_root is not None:
            _list = self.lxml_root.xpath('//meta[@name="description"]')
            if len(_list) > 0:
                content_list = _list[0].xpath('@content')
                if len(content_list) > 0:
                    self.description = content_list[0]

    def download(self):
        """downloads html of source"""

        self.html = get_html(self.url)

    @print_duration
    def download_categories(self):
        """individually download all category html, async io'ed"""

        category_urls = [c.url for c in self.categories]
        responses = async_request(category_urls)

        # Note that the responses are returned in original order
        for index, resp in enumerate(responses):
            self.categories[index].html = resp.text

    @print_duration
    def download_feeds(self):
        """individually download all feed html, async io'ed"""

        feed_urls = [f.url for f in self.feeds]
        responses = async_request(feed_urls)
        for index, resp in enumerate(responses):
            self.feeds[index].rss = resp.text

    def parse(self, summarize=True, keywords=True, processes=1):
        """sets the lxml root, also sets lxml roots of all
        children links, also sets description"""

        self.lxml_root = get_lxml_root(self.html)
        self.set_description()

    def parse_categories(self):
        """parse out the lxml root in each category"""

        log.debug('We are extracting from %d categories' % len(self.categories))
        for category in self.categories:
            lxml_root = get_lxml_root(category.html)
            category.lxml_root = lxml_root

        self.categories = [c for c in self.categories if c.lxml_root is not None]

    @print_duration
    def parse_feeds(self):
        """due to the slow speed of feedparser, we won't be dom parsing
        our .rss feeds, but rather regex searching for urls in the .rss
        text and then relying on our article logic to detect false urls"""

        def feedparse_wrapper(html):
            return feedparser.parse(html)

        for feed in self.feeds:
            try:
                feed.dom = feedparse_wrapper(feed.html)
            except Exception, e:
                log.critical('feedparser failed %s' % e)
                print feed.url

        self.feeds = [ feed for feed in self.feeds if feed.dom is not None ]

    def feeds_to_articles(self):
        """returns articles given the url of a feed"""

        # all_tuples = []
        # for feed in self.feeds:
        #     dom = feed.dom
        #
        #     if dom.get('entries'):
        #         ll = dom['entries']
        #         tuples = [(l['link'], l['title']) for l in ll
        #                         if l.get('link') and l.get('title')]
        #         all_tuples.extend(tuples)

        urls = []
        for feed in self.feeds:
            urls.extend(get_urls(feed.rss, titles=False, regex=True))

        articles = []
        for url in urls:
            article = Article(
                url=url,
                source_url=self.url,
                # title=???, TODO
             )
            articles.append(article)

        articles = self.purge_articles(articles)
        articles = memoize_articles(articles, self.domain)
        log.debug('%d from feeds at %s' % (len(articles), str(self.feeds[:10])))
        return articles

    def categories_to_articles(self):
        """takes the categories, splays them into a big list of urls and churns
        the articles out of each url with the url_to_article method"""

        total = []
        for category in self.categories:
            articles = []
            tups = get_urls(category.lxml_root, titles=True)
            before = len(tups)

            for tup in tups:
                indiv_url = tup[0]
                indiv_title = tup[1]

                _article = Article(
                    url=indiv_url,
                    source_url=self.url,
                    title=indiv_title
                )
                articles.append(_article)

            articles = self.purge_articles(articles)
            after = len(articles)

            articles = memoize_articles(articles, self.domain)
            after_memo = len(articles)

            total.extend(articles)
            log.debug('%d->%d->%d for %s' % (before, after, after_memo, category.url))

        return total

    def _generate_articles(self):
        """returns a list of all articles, from both categories and feeds"""

        category_articles = self.categories_to_articles()
        feed_articles = self.feeds_to_articles()

        articles = feed_articles + category_articles
        uniq = { article.url:article for article in articles }
        return uniq.values()

    def generate_articles(self, limit=5000):
        """saves all current articles of news source"""

        articles = self._generate_articles()
        self.articles = articles[:limit]
        log.debug('Saved', limit, 'articles and cut', (len(articles)-limit), 'articles')

    @print_duration
    def async_download_articles(self):
        """downloads all articles attached to self async-io"""

        article_urls = [a.url for a in self.articles][:500]
        responses = async_request(article_urls)

        # Note that the responses are returned in original order
        for index, resp in enumerate(responses):
            self.articles[index].html = resp.text

    def size(self):
        """number of articles linked to this news source"""

        if self.articles is None:
            return 0
        return len(self.articles)

    def print_summary(self):
        """prints out a summary of the data in our source instance"""

        print '[source url]:',              self.url
        print '[source brand]:',            self.brand
        print '[source domain]:',           self.domain
        print '[source len(articles)]:',    len(self.articles)
        print '[source description[:50]]:', self.description[:50]

        print 'printing out 10 sample articles...'
        for a in self.articles[:10]:
            print '\t', '[url]:', a.url, '[title]:', a.title,\
                   '[len of text]:', len(a.text), '[keywords]:', a.keywords,\
                    '[len of html]:', len(a.html)

        for f in self.feeds:
            print 'feed_url:', f.url

        for c in self.categories:
            print 'category_url:', c.url
