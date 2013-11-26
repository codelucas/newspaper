# -*- coding: utf-8 -*-

import logging
import feedparser

from .network import get_html
from .parsers import get_lxml_root

from urlparse import urlparse

log = logging.getLogger(__name__)

class Source(object):
    """Sources are abstractions of online news
    vendors like HuffingtonPost or cnn.

    domain     = www.cnn.com
    scheme     = http, https
    categories = ['http://cnn.com/world', 'http://money.cnn.com']
    feeds      = ['http://cnn.com/rss.atom', ..]
    links      = [<link obj>, <link obj>, ..]

    """

    def __init__(self, url=u''):
        if url == u'' or url is None:
            raise Exception

        if ('://' not in url) or (url[:4] != 'http'):
            raise Exception

        up = urlparse(url)
        self.domain, self.scheme = up.netloc, up.scheme
        self.url = url

        self.category_urls = []
        self.obj_categories = [] # [url, html, lxml] lists
        self.feed_urls = []
        self.obj_feeds = []      # [url, html, lxml] lists

        self.articles = []
        self.html = u''
        self.lxml_root = None


    def fill(self, download=True, parse=True):
        """Encapsulates download and fill."""

        if parse is True and download is False:
            print 'ERR: Can\'t parse w/o downloading!'
            return None


    def parse(self, summarize=True, keywords=True, processes=1):
        """sets the lxml root, also sets lxml roots of all
        children links"""

        self.lxml_root = get_lxml_root(self.html)


    def download(self, threads=1):
        """downloads html of source"""

        self.html = get_html(self.url)


    def download_categories(self):
        """individually download all category html"""

        for url in self.category_urls:
            self.obj_categories.append( [url, get_html(url)] )


    def download_feeds(self):
        """individually download all feed html"""

        for url in self.feed_urls:
            self.obj_feeds.append( [url, get_html(url)] )


    def parse_categories(self):
        """parse out the lxml root in each category"""

        for index, lst in enumerate(self.obj_categories):
            lxml_root = get_lxml_root(lst[1]) # lst[1] is html
            lst.append(lxml_root)
            self.obj_categories[index] = lst


    def parse_feeds(self):
        """use html of feeds to parse out their respective dom trees"""

        def feedparse_wrapper(html):
            return feedparser.parse(html)

        for index, lst in enumerate(self.obj_feeds):
            try:
                dom = feedparse_wrapper(lst[1])
            except Exception, e:
                log.critical('feedparse failed %s' % e)
                print lst[0]
                lst.append(None)

            else:
                lst.append(dom)

            self.obj_feeds[index] = lst

        self.obj_feeds = [ lst for lst in self.obj_feeds if lst[2] ]


    def purge_articles(self, articles=None):
        """delete rejected articles, if there is a articles
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



    def set_feed_urls(self):
        """two types of anchors, categories and feeds (rss)
        we extract category urls first, then jump in each
        to find feeds"""

        all_feeds = []

        for lst in self.obj_categories:

            root = lst[2]

            all_feeds.extend(root.xpath(
                    '//*[@type="application/rss+xml"]/@href'))

        all_feeds = all_feeds[:50]
        all_feeds = [ urljoin(self.get_url(), f)
                            for f in all_feeds ]

        feeds = list(set(all_feeds))
        self.feed_urls = feeds


    def set_category_urls(self):
        """takes a domain and finds all of the top level
        urls, we are assuming that these are the category urls
        ex: cnn.com --> [ cnn.com/latest, cnn.com/world,
        cnn.com/asia ]"""

        urls = root_to_urls(self.lxml_root, titles=False)
        good = []

        for u in urls:

            dat = urlparse(u, allow_fragments=False)
            schme, domain, path = dat.scheme, dat.netloc, dat.path

            if not domain and not path:
                continue
            if path and '#' in path:
                continue
            if schme and (schme!='http' and schme!='https'):
                continue

            if domain:

                child_tld = tldextract.extract(u)
                domain_tld = tldextract.extract(self.get_url())

                if child_tld.domain != domain_tld.domain:
                    continue
                elif child_tld.subdomain in ['m', 'i']:
                    continue
                else:
                    good.append(schme+'://'+domain)

            else:
                # we want a path with just one subdir
                # cnn.com/world and cnn.com/world/ are both good
                path_chunks = [ x for x in path.split('/') if len(x) > 0 ]

                if 'index.html' in path_chunks:
                    path_chunks.remove('index.html')

                if len(path_chunks) == 1 and len(path_chunks[0]) < 14:
                    good.append(domain+path)

        stopwords = [
            'about', 'help', 'privacy', 'legal', 'feedback', 'sitemap',
            'profile', 'account', 'mobile', 'sitemap', 'facebook', 'myspace',
            'twitter', 'linkedin', 'bebo', 'friendster', 'stumbleupon', 'youtube',
            'vimeo', 'store', 'mail', 'preferences', 'maps', 'password', 'imgur',
            'flickr', 'search', 'subscription', 'itunes', 'siteindex', 'events',
            'stop', 'jobs', 'careers', 'newsletter', 'subscribe', 'academy',
            'shopping', 'purchase', 'site-map', 'shop', 'donate', 'newsletter',
            'product', 'advert', 'info', 'tickets', 'coupons', 'forum', 'board',
            'archive', 'browse', 'howto', 'how to', 'faq', 'terms', 'charts',
            'services', 'contact', 'plus', 'admin', 'login', 'signup', 'register']

        _good = []

        # TODO Stop spamming urlparse and tldextract calls...

        for g in good:
            pth = urlparse(g).path
            subdom = tldextract.extract(g).subdomain
            comp = pth + ' ' + subdom
            bad=False
            for s in stopwords:
                if s.lower() in comp.lower():
                    bad=True
                    break
            if not bad:
                _good.append(g)

        _good.append('/') # add the root!

        for i, url in enumerate(_good):

            if url.startswith('://') :
                url = 'http' + url
                _good[i] = url

            elif url.startswith('//'):
                url = 'http:' + url
                _good[i] = url

            if url.endswith('/'):
                url = url[:-1]
                _good[i] = url

        _good = list(set(_good))

        categories = [ urljoin(self.get_url(), url)
                                for url in _good ]

        self.category_urls = categories


    def feeds_to_articles(self):
        """returns links given the url of a feed"""

        all_tuples = []

        for lst in self.obj_feeds:
            feed_url, html, dom = lst[0], lst[1], lst[2]

            if dom.get('entries'):

                ll = dom['entries']
                tuples = [(l['link'], l['title'])
                        for l in ll
                            if l.get('link') and
                                l.get('title')]

                all_tuples.extend(tuples)

        articles = []

        for t in all_tuples:

            article = Article(
                href=t[0],
                source_url=self.url,
                title=t[1],
                from_feed=True
             )
            articles.append(article)

        articles = self.purge_links(articles)
        articles = memoize(articles, self.domain)

        log.debug('%d from feeds at %s' %
                    (len(articles), str(self.feed_urls[:10])))

        return articles


    def categories_to_articles(self):
        """takes the categories, splays them into a big
        list of urls and churns the articles out of each
        url with the url_to_article method"""

        total = []

        for lst in self.obj_categories:
            cat_url, html, root = lst[0], lst[1], lst[2]
            links = []
            tups = root_to_urls(root, titles=True) # (url, title)
            before = len(tups)

            for tup in tups:

                indiv_url, indiv_title = tup[0], tup[1]
                _article = Article(
                    href=indiv_url,
                    source_url=self.get_url(),
                    title=indiv_title
                )
                links.append(_article)

            links = self.purge_links(links=links)
            after = len(links)

            links = memoize(links, self.domain, source=self)
            after_memo = len(links)

            total.extend(links)

            log.debug('%d->%d->%d for %s' %
                         (before, after, after_memo, cat_url))

        return total


    def all_articles(self):
        """returns a list of all articles, from both categories and feeds"""

        category_articles = self.categories_to_articles()
        feed_articles = self.feeds_to_articles()

        articles = feed_articles + category_articles
        uniq = { article.href:article for article in articles }

        return uniq.values()


    def set_articles(self, limit=5000):
        """highest encapsulated method in the Source class
        set the links of the source from feeds and categories.
        Then, immediatly purge the invalid ones."""

        articles = self.all_articles()
        self.articles = articles[:limit]


    def length(self):
        """number of articles linked to this news source"""

        if self.articles is None:
            return 0
        return len(self.articles)


