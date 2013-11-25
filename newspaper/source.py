# -*- coding: utf-8 -*-

from urlparse import urlparse, urljoin

class Source(object):
    """Encapsulation of a news domain, eg cnn.com"""

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


    def get_url(self):
        """Returns href of news source"""
        pass
