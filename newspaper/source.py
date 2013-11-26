# -*- coding: utf-8 -*-

import logging

from .settings import useragent

from urlparse import urlparse

log = logging.getLogger(__name__)

class Source(object):
    """Sources are abstractions of online news
    vendors like HuffingtonPost or cnn.

    domain = www.cnn.com
    scheme = http, https

    categories = ['http://cnn.com/world', 'http://money.cnn.com']
    feeds = ['http://cnn.com/rss.atom', ..]
    links =  [<link obj>, <link obj>, ..]

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

        self.links = []
        self.html = u''
        self.lxml_root = None


    def fill(self, download=True, parse=True):
        """Encapsulates download and fill."""

        if parse is True and download is False:
            print 'ERR: Can\'t parse w/o downloading!'
            return None

    def download(self, threads=1):
        """All IO tasks for a news article.
        Download article html."""
        pass


    def parse(self, summarize=True, keywords=True, processes=1):
        """All CPU bound tasks in a news article,
        parse html, extract summary & keywords, etc"""

        pass

    def download_categories(self):
        """individually download all category html"""

        for c in self.category_urls:
            self.obj_categories.append( [c, self._download(c)] )


    def download_feeds(self):
        """individually download all feed html"""
        for f in self.feed_urls:
            self.obj_feeds.append( [f, self._download(f)] )

    def parse_categories(self):
        """parse out the lxml root in each category"""

        for index, lst in enumerate(self.obj_categories):
            lxml_root = self._parse(lst[1])
            lst.append(lxml_root)
            self.obj_categories[index] = lst


    def parse_feeds(self):
        """use html of feeds to parse out their respective
        dom trees"""

        @timelimit(5)
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


    def download(self):
        """downloads html of source"""

        self.html = self._download(self.url)


    def _download(self, url):
        """base download, url->html"""

        try:
            req_kwargs = {
                'headers' : {'User-Agent': useragent},
                'cookies' : cj(),
                'timeout' : 12
            }

            html = requests.get(url=url, **req_kwargs).text

            if html is None:
                html = u''

            return html

        except Exception, e:
            # logger.critical('%s at %s' % (e, self.domain))
            return u''


    def parse(self):
        """sets the lxml root, also sets lxml roots of all
        children links"""

        self.lxml_root = self._parse(self.html)


    def _parse(self, html):
        """base parse, html->lxml_root"""

        root = None
        try:
            root = self._lxml_wrapper(html)
        except Exception, e:
            # logger.debug('lxml failed %s' % e)
            try:
                root = self._soup_wrapper(html)
            except Exception, e:
                pass
                # logger.critical('soup lxml failed %s' % e)

        return root



