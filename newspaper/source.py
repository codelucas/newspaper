# -*- coding: utf-8 -*-

import logging

from . import parsers
from . import network
from .article import Article
from .urls import get_domain, get_scheme, prepare_url
from .settings import ANCHOR_DIR
from .packages.tldextract import tldextract
from .packages.feedparser import feedparser
from .utils import (
    fix_unicode, memoize_articles, cache_disk, print_duration,
    clear_memo_cache)

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
        # self.dom = None    TODO Speed up feedparser

class Source(object):
    """
    Sources are abstractions of online news vendors like HuffingtonPost or cnn.

    domain     =  'www.cnn.com'
    scheme     =  'http'
    categories =  ['http://cnn.com/world', 'http://money.cnn.com']
    feeds      =  ['http://cnn.com/rss.atom', ..]
    articles   =  [<article obj>, <article obj>, ..]
    brand      =  'cnn'

    """

    def __init__(self, url=None, is_memo=True, verbose=False):

        if (url is None) or ('://' not in url) or (url[:4] != 'http'):
            raise Exception('Input url is bad!')

        self.verbose = verbose

        self.url = fix_unicode(url)
        self.url = prepare_url(url)

        self.domain = get_domain(self.url)
        self.scheme = get_scheme(self.url)

        self.is_memo = is_memo

        self.categories = []
        self.feeds = []
        self.articles = []

        self.html = u''
        self.lxml_root = None

        self.logo_url = u''
        self.favicon = u''
        self.brand = tldextract.extract(self.url).domain
        self.description = u''

        self.is_parsed = False     # flags to warn users if they forgot to
        self.is_downloaded = False # download() or parse()

    def build(self, parse=True):
        """Encapsulates download and basic parsing with lxml. May be a
        good idea to split this into download() and parse() methods."""

        self.download()
        self.parse()

        # Can not merge category and feed tasks together because
        # computing feed urls relies on the category urls!
        self.set_categories()
        self.download_categories() # mthread
        self.parse_categories()

        self.set_feeds()
        self.download_feeds()      # mthread
        # self.parse_feeds()       # TODO regexing out feeds until fix feedparser!

        self.generate_articles()
        # self.download_articles()

    def purge_articles(self, reason, in_articles=None):
        """delete rejected articles, if there is an articles param, we
        purge from there, otherwise purge from our source instance"""

        # TODO TODO Figure out why using the 'del' command on input list reference
        # isn't actually filtering the list?!
        # cur_articles = self.articles if in_articles is None else in_articles
        new_articles = []

        for index, article in enumerate(in_articles):
            if reason == 'url' and not article.is_valid_url():
                #print 'deleting article', cur_articles[index].url
                #del cur_articles[index]
                #del in_articles[index]
                pass
            elif reason == 'url':
                new_articles.append(in_articles[index])

            if reason == 'body' and not article.is_valid_body():
                #del cur_articles[index]
                pass
            elif reason == 'body':
                new_articles.append(cur_articles[index])

        if in_articles is not None: # if they give an input, output filtered
            return new_articles
        #else: # no input, we are playing with self.articles
        #    self.articles = new_articles

    @cache_disk(seconds=(86400*1), cache_folder=ANCHOR_DIR)
    def _get_category_urls(self, domain):
        """the domain param is **necessary**, see .utils.cache_disk for reasons.
        the boilerplate method is so we can use this decorator right. We are
        caching categories for 1 day."""

        return parsers.get_category_urls(self)

    def set_categories(self):
        """"""

        urls = self._get_category_urls(self.domain)
        self.categories = [Category(url=url) for url in urls]

    def set_feeds(self):
        """don't need to cache getting feed urls, it's almost
        instant w/ xpath"""

        urls = parsers.get_feed_urls(self)
        self.feeds = [Feed(url=url) for url in urls]

    def set_description(self):
        """sets a blub for this source, for now we just
        query the desc html attribute"""

        if self.lxml_root is not None:
            _list = self.lxml_root.xpath('//meta[@name="description"]')
            if len(_list) > 0:
                content_list = _list[0].xpath('@content')
                if len(content_list) > 0:
                    self.description = fix_unicode(content_list[0])

    def download(self):
        """downloads html of source"""

        self.html = network.get_html(self.url)

    # @print_duration
    def download_categories(self):
        """individually download all category html, async io'ed"""

        category_urls = [c.url for c in self.categories]
        requests = network.multithread_request(category_urls)

        # the weird for loop is like this because the del keyword auto adjusts
        # the list index after deletion only if the list being iterated contains elem deleted
        for index, _ in enumerate(self.categories):
            req = requests[index]
            if req.resp is not None:
                self.categories[index].html = req.resp.text
            else:
                if self.verbose:
                    print 'deleting category', self.categories[index].url, 'due to download err'
                del self.categories[index] # TODO

    # @print_duration
    def download_feeds(self):
        """individually download all feed html, async io'ed"""

        feed_urls = [f.url for f in self.feeds]
        requests = network.multithread_request(feed_urls)

        # the weird for loop is like this because the del keyword auto adjusts
        # the list index after deletion only if the list being iterated contains elem deleted
        for index, _ in enumerate(self.feeds):
            req = requests[index]
            if req.resp is not None:
                self.feeds[index].rss = req.resp.text
            else:
                if self.verbose:
                    print 'deleting feed', self.categories[index].url, 'due to download err'
                del self.feeds[index] # TODO

    def parse(self, summarize=True, keywords=True):
        """sets the lxml root, also sets lxml roots of all
        children links, also sets description"""

        self.lxml_root = parsers.get_lxml_root(self.html)
        self.set_description()

    def parse_categories(self):
        """parse out the lxml root in each category"""

        log.debug('We are extracting from %d categories' % len(self.categories))
        for category in self.categories:
            lxml_root = parsers.get_lxml_root(category.html)
            category.lxml_root = lxml_root

        self.categories = [c for c in self.categories if c.lxml_root is not None]

    def parse_feeds(self): # TODO Use this method after we figure out how to make it fast
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
                if self.verbose: print feed.url

        self.feeds = [feed for feed in self.feeds if feed.dom is not None]

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

        articles = []
        for feed in self.feeds:
            urls = parsers.get_urls(feed.rss, regex=True)
            cur_articles = []
            before_purge = len(urls)

            for url in urls:
                article = Article(
                    url=url,
                    source_url=self.url,
                    # title=?  # TODO
                 )
                cur_articles.append(article)

            cur_articles = self.purge_articles('url', cur_articles)
            after_purge = len(cur_articles)

            if self.is_memo:
                cur_articles = memoize_articles(cur_articles, self.domain)
            after_memo = len(cur_articles)

            articles.extend(cur_articles)

            if self.verbose:
                print '%d->%d->%d for %s' % (before_purge, after_purge, after_memo, feed.url)
            log.debug('%d->%d->%d for %s' % (before_purge, after_purge, after_memo, feed.url))
        return articles

    def categories_to_articles(self):
        """takes the categories, splays them into a big list of urls and churns
        the articles out of each url with the url_to_article method"""

        articles = []
        for category in self.categories:
            cur_articles = []
            url_title_tups = parsers.get_urls(category.lxml_root, titles=True)
            before_purge = len(url_title_tups)

            for tup in url_title_tups:
                indiv_url = tup[0]
                indiv_title = tup[1]

                _article = Article(
                    url=indiv_url,
                    source_url=self.url,
                    title=indiv_title
                )
                cur_articles.append(_article)

            cur_articles = self.purge_articles('url', cur_articles)
            after_purge = len(cur_articles)

            if self.is_memo:
                cur_articles = memoize_articles(cur_articles, self.domain)
            after_memo = len(cur_articles)

            articles.extend(cur_articles)

            if self.verbose:
                print '%d->%d->%d for %s' % (before_purge, after_purge, after_memo, category.url)
            log.debug('%d->%d->%d for %s' % (before_purge, after_purge, after_memo, category.url))

        return articles

    def _generate_articles(self):
        """returns a list of all articles, from both categories and feeds"""

        category_articles = self.categories_to_articles()
        feed_articles = self.feeds_to_articles()

        articles = feed_articles + category_articles
        uniq = { article.url:article for article in articles }
        return uniq.values()

    def generate_articles(self, limit=5000):
        """saves all current articles of news source, filter out bad urls"""

        articles = self._generate_articles()
        self.articles = articles[:limit]

        # for a in self.articles:
        #   print 'test examine url:', a.url

        # log.critical('total', len(articles), 'articles and cutoff was at', limit)

    # @print_duration
    def download_articles(self, multithread=False):
        """downloads all articles attached to self"""

        urls = [a.url for a in self.articles]
        failed_articles = []
        self.is_downloaded = True

        # TODO Note that del statements automatically handle index movement,
        # but only if the elem deleted is consistent with element(s) of loop
        if not multithread:
            for index, article in enumerate(self.articles):
                url = urls[index]
                html = network.get_html(url)
                if html:
                    self.articles[index].html = html
                else:
                    failed_articles.append(self.articles[index])
                    del self.articles[index] # TODO iffy using del here
        else:
            filled_requests = network.multithread_request(urls)
            # Note that the responses are returned in original order
            for index, req in enumerate(filled_requests):
                if req.resp is not None:
                    self.articles[index].html = req.resp.text
                else:
                    failed_articles.append(self.articles[index])
                    del self.articles[index] # TODO iffy using del here

        if len(failed_articles) > 0:
            print '[ERROR], these article urls failed the download:', \
                [a.url for a in failed_articles]

    def parse_articles(self):
        """sync parse all articles, delete if too small"""

        for index, article in enumerate(self.articles):
            article.parse()

        self.articles = self.purge_articles('body', self.articles)
        self.is_parsed = True

    def size(self):
        """number of articles linked to this news source"""

        if self.articles is None:
            return 0
        return len(self.articles)

    def clean_memo_cache(self):
        """clears the memoization cache for this specific news domain"""

        clear_memo_cache(self)

    def feed_urls(self):
        """
        """
        return [feed.url for feed in self.feeds]

    def category_urls(self):
        """
        """
        return [category.url for category in self.categories]

    def article_urls(self):
        """
        """

        return [article.url for article in self.articles]

    def print_summary(self):
        """prints out a summary of the data in our source instance"""

        print '[source url]:',              self.url
        print '[source brand]:',            self.brand
        print '[source domain]:',           self.domain
        print '[source len(articles)]:',    len(self.articles)
        print '[source description[:50]]:', self.description[:50]

        print 'printing out 10 sample articles...'

        for a in self.articles[:10]:
            print '\t', '[url]:', a.url
            print '\t[title]:', a.title
            print '\t[len of text]:', len(a.text)
            print '\t[keywords]:', a.keywords
            print '\t[len of html]:', len(a.html)
            print '\t=============='

        print 'feed_urls:', self.feed_urls()
        print '\r\n'
        print 'category_urls:', self.category_urls()
