# -*- coding: utf-8 -*-

import logging

from .network import get_html
from .article import Article
from .utils import fix_unicode, memoize_articles
from .urls import get_domain, get_scheme, prepare_url
from .packages.tldextract import tldextract
from .parsers import (
    get_lxml_root, get_urls, get_feed_urls, get_category_urls)

from .packages.feedparser import feedparser

log = logging.getLogger(__name__)

class Category(object):

    def __init__(self, url):
        self.url = url
        self.html = None
        self.lxml_root = None

class FeedObj(object):

    def __init__(self, url):
        self.url = url
        self.html = None
        self.lxml_root = None

class Source(object):
    """Sources are abstractions of online news
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

        self.domain = get_domain(url)
        self.scheme = get_scheme(url)

        self.category_urls = []
        self.feed_urls = []
                                 # TODO: This is a bad approach, change soon!
        self.obj_categories = [] # [url, html, lxml] lists of lists
        self.obj_feeds = []      # [url, html, lxml] lists of lists

        self.articles = []
        self.html = u''
        self.lxml_root = None

        self.brand = tldextract.extract(self.url).domain
        self.description = u'' # TODO

    def fill(self, download=True, parse=True):
        """Encapsulates download and fill."""

        if parse is True and download is False:
            print 'ERR: Can\'t parse w/o downloading!'
            return None

        self.download()
        self.parse()

        # can not merge category and feed tasks together because
        # computing feed urls relies on the category urls!
        self.set_category_urls()
        self.download_categories() # async
        self.parse_categories()

        self.set_feed_urls()
        self.download_feeds()      # async
        self.parse_categories()

        self.generate_articles()
        # download articles
        # parse articles

    def purge_articles(self, articles=None):
        """delete rejected articles, if there is an articles
        param, we purge from there, otherwise purge from self"""

        ret = []
        if articles is not None:
            for article in articles:
                if not article.rejected:
                    ret.append(article)
                else:
                    pass
            return ret

        for article in self.articles:
            if not article.rejected:
                ret.append(article)

        self.articles = ret

    def download(self, threads=1):
        """downloads html of source"""

        self.html = get_html(self.url)

    def parse(self, summarize=True, keywords=True, processes=1):
        """sets the lxml root, also sets lxml roots of all
        children links, also sets description"""

        self.lxml_root = get_lxml_root(self.html)
        self.set_description()

    def download_categories(self):
        """individually download all category html, async io'ed"""

        for url in self.category_urls:
            self.obj_categories.append( [url, get_html(url)] )

    def download_feeds(self):
        """individually download all feed html, async io'ed"""

        for url in self.feed_urls:
            self.obj_feeds.append( [url, get_html(url)] )

    def parse_categories(self):
        """parse out the lxml root in each category"""

        for index, category_obj in enumerate(self.obj_categories):
            # category_obj[1] is html, category_obj[0] is url
            lxml_root = get_lxml_root(category_obj[1])
            category_obj.append(lxml_root)
            self.obj_categories[index] = category_obj

    def parse_feeds(self):
        """use html of feeds to parse out their respective dom trees"""

        def feedparse_wrapper(html):
            return feedparser.parse(html)

        for index, category_obj in enumerate(self.obj_feeds):
            try:
                dom = feedparse_wrapper(category_obj[1])
            except Exception, e:
                log.critical('feedparser failed %s' % e)
                print category_obj[0]
                category_obj.append(None)
            else:
                category_obj.append(dom)

            self.obj_feeds[index] = category_obj

        self.obj_feeds = [ category_obj
                for category_obj in self.obj_feeds if category_obj[2] ]

    def feeds_to_articles(self):
        """returns articles given the url of a feed"""

        all_tuples = []
        for feed_obj in self.obj_feeds:
            # feed_url = feed_obj[0]
            # html = feed_obj[1]
            dom = feed_obj[2]

            if dom.get('entries'):
                ll = dom['entries']
                tuples = [(l['link'], l['title']) for l in ll
                                if l.get('link') and l.get('title')]
                all_tuples.extend(tuples)

        articles = []
        for tup in all_tuples:
            article = Article(
                url=tup[0],
                source_url=self.url,
                title=tup[1],
                from_feed=True
             )
            articles.append(article)

        articles = self.purge_articles(articles)
        articles = memoize_articles(articles, self.domain)
        log.debug('%d from feeds at %s' %
                    (len(articles), str(self.feed_urls[:10])))
        return articles

    def categories_to_articles(self):
        """takes the categories, splays them into a big list of urls and churns
        the articles out of each url with the url_to_article method"""

        total = []
        for category_obj in self.obj_categories:
            category_url = category_obj[0]
            # html = category_obj[1]
            lxml_root = category_obj[2]

            articles = []
            tups = get_urls(lxml_root, titles=True) # (url, title) tuples
            before = len(tups)

            for tup in tups:
                indiv_url, indiv_title = tup[0], tup[1]
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
            log.debug('%d->%d->%d for %s' % (before, after, after_memo, category_url))

        return total

    def set_category_urls(self):
        self.category_urls = get_category_urls(self)

    def set_feed_urls(self):
        self.feed_urls = get_feed_urls(self)

    def set_description(self):
        """sets a blub for this source, for now we just
        query the desc html attribute"""

        if self.lxml_root is not None:
            _list = self.lxml_root.xpath('//meta[@name="description"]')
            if len(_list) > 0:
                content_list = _list[0].xpath('@content')
                if len(content_list) > 0:
                    self.description = content_list[0]

    def _generate_articles(self):
        """returns a list of all articles, from both categories and feeds"""

        category_articles = self.categories_to_articles()
        feed_articles = self.feeds_to_articles()

        articles = feed_articles + category_articles
        uniq = { article.href:article for article in articles }
        return uniq.values()

    def generate_articles(self, limit=5000):
        """saves all current articles of news source"""

        articles = self._generate_articles()
        self.articles = articles[:limit]

    def size(self):
        """number of articles linked to this news source"""

        if self.articles is None:
            return 0
        return len(self.articles)
