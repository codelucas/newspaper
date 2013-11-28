# -*- coding: utf-8 -*-

import logging

from .network import get_html
from .article import Article
from .utils import fix_unicode, memoize_articles, cache_disk, print_duration
from .urls import get_domain, get_scheme, prepare_url
from .settings import ANCHOR_DIR
from .packages.tldextract import tldextract
from .packages.feedparser import feedparser
from .parsers import (
    get_lxml_root, get_urls, get_feed_urls, get_category_urls)

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

        self.domain = get_domain(self.url)
        self.scheme = get_scheme(self.url)

        self.category_urls = []
        self.feed_urls = []
                                 # TODO: This is a bad approach, change soon!
        self.category_objs = []  # [url, html, lxml] lists of lists
        self.feed_objs = []      # [url, html, lxml] lists of lists

        self.articles = []
        self.html = u''
        self.lxml_root = None

        self.brand = tldextract.extract(self.url).domain
        self.description = u'' # TODO

    def build(self, download=True, parse=True):
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
        self.parse_feeds()

        self.generate_articles()
        # download articles
        # parse articles

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

    def download(self):
        """downloads html of source"""

        self.html = get_html(self.url)

    @print_duration
    def download_categories(self, async=True, cache=True):
        """individually download all category html, async io'ed"""

        for url in self.category_urls:
            self.category_objs.append( [url, get_html(url)] )

    @print_duration
    def download_feeds(self, async=True, cache=True):
        """individually download all feed html, async io'ed"""

        for url in self.feed_urls:
            self.feed_objs.append( [url, get_html(url)] )

    def parse(self, summarize=True, keywords=True, processes=1):
        """sets the lxml root, also sets lxml roots of all
        children links, also sets description"""

        self.lxml_root = get_lxml_root(self.html)
        self.set_description()

    def parse_categories(self):
        """parse out the lxml root in each category"""

        log.debug('We are extracting from %d categories' % len(self.category_objs))
        for index, category_obj in enumerate(self.category_objs):
            # category_obj[1] is html, category_obj[0] is url
            lxml_root = get_lxml_root(category_obj[1])
            category_obj.append(lxml_root)
            self.category_objs[index] = category_obj

    @print_duration
    def parse_feeds(self):
        """use html of feeds to parse out their respective dom trees"""

        def feedparse_wrapper(html):
            return feedparser.parse(html)

        for index, feed_obj in enumerate(self.feed_objs):
            try:
                dom = feedparse_wrapper(feed_obj[1])
            except Exception, e:
                log.critical('feedparser failed %s' % e)
                print feed_obj[0]
                feed_obj.append(None)
            else:
                feed_obj.append(dom)
            self.feed_objs[index] = feed_obj

        self.feed_objs = [ feed_obj
                for feed_obj in self.feed_objs if feed_obj[2] is not None ]

    def feeds_to_articles(self):
        """returns articles given the url of a feed"""

        all_tuples = []
        for feed_obj in self.feed_objs:
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
        for category_obj in self.category_objs:
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

    @cache_disk(seconds=(86400*1), cache_folder=ANCHOR_DIR)
    def _get_category_urls(self, domain):
        """the domain param is **necessary**, see .utils.cache_disk for reasons
        boilerplate method so we can use this decorator right we are caching
        categories for 1 DAY."""

        return get_category_urls(self)

    def set_category_urls(self):
        """"""

        self.category_urls = self._get_category_urls(self.domain)

    def set_feed_urls(self):
        """don't need to cache getting feed urls, it's almost
        instant w/ xpath"""

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
        uniq = { article.url:article for article in articles }
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

    def print_summary(self):
        """prints out a summary of the data in our source instance"""

        print '[source]: url', self.url
        print '[source]: brand', self.brand
        print '[source]: domain', self.domain
        print '[source]: len(articles)', len(self.articles)
        print '[source]: description[:50]', self.description[:50]

        print 'printing out 10 sample articles...'
        for a in self.articles[:10]:
            print '\t', 'url:', a.url, 'title:', a.title,\
                   'length of text:', len(a.text), 'keywords:', a.keywords

        for f in self.feed_urls:
            print 'feed_url:', f

        for c in self.category_urls:
            print 'category_url:', c


