# -*- coding: utf-8 -*-
"""
Source objects abstract online news source websites & domains.
www.cnn.com would be its own source.
"""
__title__ = 'newspaper'
__author__ = 'Lucas Ou-Yang'
__license__ = 'MIT'
__copyright__ = 'Copyright 2014, Lucas Ou-Yang'

import logging
from urllib.parse import urljoin, urlsplit, urlunsplit

from tldextract import tldextract

from . import network
from . import urls
from . import utils
from .article import Article
from .configuration import Configuration
from .extractors import ContentExtractor
from .settings import ANCHOR_DIRECTORY

log = logging.getLogger(__name__)


class Category(object):
    def __init__(self, url):
        self.url = url
        self.html = None
        self.doc = None


class Feed(object):
    def __init__(self, url):
        self.url = url
        self.rss = None
        # TODO self.dom = None, speed up Feedparser


class Source(object):
    """Sources are abstractions of online news vendors like huffpost or cnn.
    domain     =  'www.cnn.com'
    scheme     =  'http'
    categories =  ['http://cnn.com/world', 'http://money.cnn.com']
    feeds      =  ['http://cnn.com/rss.atom', ..]
    articles   =  [<article obj>, <article obj>, ..]
    brand      =  'cnn'
    """

    def __init__(self, url, config=None, **kwargs):
        """The config object for this source will be passed into all of this
        source's children articles unless specified otherwise or re-set.
        """
        if (url is None) or ('://' not in url) or (url[:4] != 'http'):
            raise Exception('Input url is bad!')

        self.config = config or Configuration()
        self.config = utils.extend_config(self.config, kwargs)

        self.extractor = ContentExtractor(self.config)

        self.url = url
        self.url = urls.prepare_url(url)

        self.domain = urls.get_domain(self.url)
        self.scheme = urls.get_scheme(self.url)

        self.categories = []
        self.feeds = []
        self.articles = []

        self.html = ''
        self.doc = None

        self.logo_url = ''
        self.favicon = ''
        self.brand = tldextract.extract(self.url).domain
        self.description = ''

        self.is_parsed = False
        self.is_downloaded = False

    def build(self):
        """Encapsulates download and basic parsing with lxml. May be a
        good idea to split this into download() and parse() methods.
        """
        self.download()
        self.parse()

        self.set_categories()
        self.download_categories()  # mthread
        self.parse_categories()

        self.set_feeds()
        self.download_feeds()  # mthread
        # self.parse_feeds()

        self.generate_articles()

    def purge_articles(self, reason, articles):
        """Delete rejected articles, if there is an articles param,
        purge from there, otherwise purge from source instance.

        Reference this StackOverflow post for some of the wonky
        syntax below:
        http://stackoverflow.com/questions/1207406/remove-items-from-a-
        list-while-iterating-in-python
        """
        if reason == 'url':
            articles[:] = [a for a in articles if a.is_valid_url()]
        elif reason == 'body':
            articles[:] = [a for a in articles if a.is_valid_body()]
        return articles

    @utils.cache_disk(seconds=(86400 * 1), cache_folder=ANCHOR_DIRECTORY)
    def _get_category_urls(self, domain):
        """The domain param is **necessary**, see .utils.cache_disk for reasons.
        the boilerplate method is so we can use this decorator right.
        We are caching categories for 1 day.
        """
        return self.extractor.get_category_urls(self.url, self.doc)

    def set_categories(self):
        urls = self._get_category_urls(self.domain)
        self.categories = [Category(url=url) for url in urls]

    def set_feeds(self):
        """Don't need to cache getting feed urls, it's almost
        instant with xpath
        """
        common_feed_urls = ['/feed', '/feeds', '/rss']
        common_feed_urls = [urljoin(self.url, url) for url in common_feed_urls]

        split = urlsplit(self.url)
        if split.netloc in ('medium.com', 'www.medium.com'):
            # should handle URL to user or user's post
            if split.path.startswith('/@'):
                new_path = '/feed/' + split.path.split('/')[1]
                new_parts = split.scheme, split.netloc, new_path, '', ''
                common_feed_urls.append(urlunsplit(new_parts))

        common_feed_urls_as_categories = [Category(url=url) for url in common_feed_urls]

        category_urls = [c.url for c in common_feed_urls_as_categories]
        requests = network.multithread_request(category_urls, self.config)

        for index, _ in enumerate(common_feed_urls_as_categories):
            response = requests[index].resp
            if response and response.ok:
                common_feed_urls_as_categories[index].html = network.get_html(
                    response.url, response=response)

        common_feed_urls_as_categories = [c for c in common_feed_urls_as_categories if c.html]

        for _ in common_feed_urls_as_categories:
            doc = self.config.get_parser().fromstring(_.html)
            _.doc = doc

        common_feed_urls_as_categories = [c for c in common_feed_urls_as_categories if
                                          c.doc is not None]

        categories_and_common_feed_urls = self.categories + common_feed_urls_as_categories
        urls = self.extractor.get_feed_urls(self.url, categories_and_common_feed_urls)
        self.feeds = [Feed(url=url) for url in urls]

    def set_description(self):
        """Sets a blurb for this source, for now we just query the
        desc html attribute
        """
        desc = self.extractor.get_meta_description(self.doc)
        self.description = desc

    def download(self):
        """Downloads html of source
        """
        self.html = network.get_html(self.url, self.config)

    def download_categories(self):
        """Download all category html, can use mthreading
        """
        category_urls = [c.url for c in self.categories]
        requests = network.multithread_request(category_urls, self.config)

        for index, _ in enumerate(self.categories):
            req = requests[index]
            if req.resp is not None:
                self.categories[index].html = network.get_html(
                    req.url, response=req.resp)
            else:
                if self.config.verbose:
                    print(('deleting category',
                           self.categories[index].url, 'due to download err'))
        self.categories = [c for c in self.categories if c.html]

    def download_feeds(self):
        """Download all feed html, can use mthreading
        """
        feed_urls = [f.url for f in self.feeds]
        requests = network.multithread_request(feed_urls, self.config)

        for index, _ in enumerate(self.feeds):
            req = requests[index]
            if req.resp is not None:
                self.feeds[index].rss = network.get_html(
                    req.url, response=req.resp)
            else:
                if self.config.verbose:
                    print(('deleting feed',
                           self.categories[index].url, 'due to download err'))
        self.feeds = [f for f in self.feeds if f.rss]

    def parse(self):
        """Sets the lxml root, also sets lxml roots of all
        children links, also sets description
        """
        # TODO: This is a terrible idea, ill try to fix it when i'm more rested
        self.doc = self.config.get_parser().fromstring(self.html)
        if self.doc is None:
            print('[Source parse ERR]', self.url)
            return
        self.set_description()

    def parse_categories(self):
        """Parse out the lxml root in each category
        """
        log.debug('We are extracting from %d categories' %
                  len(self.categories))
        for category in self.categories:
            doc = self.config.get_parser().fromstring(category.html)
            category.doc = doc

        self.categories = [c for c in self.categories if c.doc is not None]

    def _map_title_to_feed(self, feed):
        doc = self.config.get_parser().fromstring(feed.rss)
        if doc is None:
            # http://stackoverflow.com/a/24893800
            return None

        elements = self.config.get_parser().getElementsByTag(doc, tag='title')
        feed.title = next((element.text for element in elements if element.text), self.brand)
        return feed

    def parse_feeds(self):
        """Add titles to feeds
        """
        log.debug('We are parsing %d feeds' %
                  len(self.feeds))
        self.feeds = [self._map_title_to_feed(f) for f in self.feeds]

    def feeds_to_articles(self):
        """Returns articles given the url of a feed
        """
        articles = []
        for feed in self.feeds:
            urls = self.extractor.get_urls(feed.rss, regex=True)
            cur_articles = []
            before_purge = len(urls)

            for url in urls:
                article = Article(
                    url=url,
                    source_url=self.url,
                    config=self.config)
                cur_articles.append(article)

            cur_articles = self.purge_articles('url', cur_articles)
            after_purge = len(cur_articles)

            if self.config.memoize_articles:
                cur_articles = utils.memoize_articles(self, cur_articles)
            after_memo = len(cur_articles)

            articles.extend(cur_articles)

            if self.config.verbose:
                print(('%d->%d->%d for %s' %
                       (before_purge, after_purge, after_memo, feed.url)))
            log.debug('%d->%d->%d for %s' %
                      (before_purge, after_purge, after_memo, feed.url))
        return articles

    def categories_to_articles(self):
        """Takes the categories, splays them into a big list of urls and churns
        the articles out of each url with the url_to_article method
        """
        articles = []
        for category in self.categories:
            cur_articles = []
            url_title_tups = self.extractor.get_urls(category.doc, titles=True)
            before_purge = len(url_title_tups)

            for tup in url_title_tups:
                indiv_url = tup[0]
                indiv_title = tup[1]

                _article = Article(
                    url=indiv_url,
                    source_url=self.url,
                    title=indiv_title,
                    config=self.config
                )
                cur_articles.append(_article)

            cur_articles = self.purge_articles('url', cur_articles)
            after_purge = len(cur_articles)

            if self.config.memoize_articles:
                cur_articles = utils.memoize_articles(self, cur_articles)
            after_memo = len(cur_articles)

            articles.extend(cur_articles)

            if self.config.verbose:
                print(('%d->%d->%d for %s' %
                       (before_purge, after_purge, after_memo, category.url)))
            log.debug('%d->%d->%d for %s' %
                      (before_purge, after_purge, after_memo, category.url))
        return articles

    def _generate_articles(self):
        """Returns a list of all articles, from both categories and feeds
        """
        category_articles = self.categories_to_articles()
        feed_articles = self.feeds_to_articles()

        articles = feed_articles + category_articles
        uniq = {article.url: article for article in articles}
        return list(uniq.values())

    def generate_articles(self, limit=5000):
        """Saves all current articles of news source, filter out bad urls
        """
        articles = self._generate_articles()
        self.articles = articles[:limit]
        log.debug('%d articles generated and cutoff at %d',
                  len(articles), limit)

    def download_articles(self, threads=1):
        """Downloads all articles attached to self
        """
        # TODO fix how the article's is_downloaded is not set!
        urls = [a.url for a in self.articles]
        failed_articles = []

        if threads == 1:
            for index, article in enumerate(self.articles):
                url = urls[index]
                html = network.get_html(url, config=self.config)
                self.articles[index].set_html(html)
                if not html:
                    failed_articles.append(self.articles[index])
            self.articles = [a for a in self.articles if a.html]
        else:
            if threads > 5:
                print(('Using 5+ threads on a single source '
                       'may get you rate limited!'))
            filled_requests = network.multithread_request(urls, self.config)
            # Note that the responses are returned in original order
            for index, req in enumerate(filled_requests):
                html = network.get_html(req.url, response=req.resp)
                self.articles[index].set_html(html)
                if not req.resp:
                    failed_articles.append(self.articles[index])
            self.articles = [a for a in self.articles if a.html]

        self.is_downloaded = True
        if len(failed_articles) > 0:
            if self.config.verbose:
                print('[ERROR], these article urls failed the download:',
                      [a.url for a in failed_articles])

    def parse_articles(self):
        """Parse all articles, delete if too small
        """
        for index, article in enumerate(self.articles):
            article.parse()

        self.articles = self.purge_articles('body', self.articles)
        self.is_parsed = True

    def size(self):
        """Number of articles linked to this news source
        """
        if self.articles is None:
            return 0
        return len(self.articles)

    def clean_memo_cache(self):
        """Clears the memoization cache for this specific news domain
        """
        utils.clear_memo_cache(self)

    def feed_urls(self):
        """Returns a list of feed urls
        """
        return [feed.url for feed in self.feeds]

    def category_urls(self):
        """Returns a list of category urls
        """
        return [category.url for category in self.categories]

    def article_urls(self):
        """Returns a list of article urls
        """
        return [article.url for article in self.articles]

    def print_summary(self):
        """Prints out a summary of the data in our source instance
        """
        print('[source url]:', self.url)
        print('[source brand]:', self.brand)
        print('[source domain]:', self.domain)
        print('[source len(articles)]:', len(self.articles))
        print('[source description[:50]]:', self.description[:50])

        print('printing out 10 sample articles...')

        for a in self.articles[:10]:
            print('\t', '[url]:', a.url)
            print('\t[title]:', a.title)
            print('\t[len of text]:', len(a.text))
            print('\t[keywords]:', a.keywords)
            print('\t[len of html]:', len(a.html))
            print('\t==============')

        print('feed_urls:', self.feed_urls())
        print('\r\n')
        print('category_urls:', self.category_urls())
