# -*- coding: utf-8 -*-

import logging
import base64
import hashlib

from . import nlp
from .utils import fix_unicode
from .urls import prepare_url, get_domain, get_scheme, valid_url
from .network import get_html
from .images import Scraper
from .parsers import (
    get_lxml_root, get_top_img, get_imgs, valid_body, GooseObj)

log = logging.getLogger(__name__)

MIN_WORD_COUNT = 300
MIN_SENT_COUNT = 7
MAX_TITLE = 200
MAX_TEXT = 100004
MAX_KEYWORDS = 35
MAX_AUTHORS = 10
MAX_SUMMARY = 5000

class ArticleException(Exception):
    pass

class Article(object):
    def __init__(self, url, title=u'', source_url=None, is_attached=False):
        """
        """

        if source_url is None:
            source_url = get_scheme(url) + '://' + get_domain(url)

        if source_url is None or source_url == '':
            raise ArticleException('input url bad format')

        self.source_url = fix_unicode(source_url)

        self.url = fix_unicode(url)
        self.url = prepare_url(self.url, self.source_url)
        self.title = fix_unicode(title)

        self.top_img = u''
        self.text = u''
        self.keywords = u''
        self.authors = []
        self.published_date = u'' # TODO
        self.summary = u''

        self.domain = get_domain(self.source_url)
        self.scheme = get_scheme(self.source_url)

        self.html = u''
        self.lxml_root = None

        self.imgs = []

        self.is_parsed = False          # flags warning users incase they
        self.is_downloaded = False      # forget to download() or parse()

        # TODO After feedparser works again, we won't need to verify feed urls

    def build(self):
        """build a lone article from a url independent of the
        source (newspaper). We won't normally call this method b/c
        we want to multithread articles on a source (newspaper) level"""

        self.download()
        self.parse()
        self.nlp()

    def get_key(self):
        """returns a md5 representation of the url"""

        return base64.urlsafe_b64encode(hashlib.md5(self.url).digest())

    def download(self, timeout=7):
        """downloads the link's html content, don't use if we are async
        downloading batch articles"""

        self.html = get_html(self.url, timeout=timeout)
        self.is_downloaded = True

    def parse(self):
        """extracts the lxml root, if lxml fails, we also extract the
        BeautifulSoup root. We also parse images to keep cpu bound
        tasks all in one place."""

        if not self.is_downloaded:
            print 'You must download an article before parsing it! run download()'
            raise ArticleException()

        goose_obj = GooseObj(self)
        self.set_text(goose_obj.body_text)
        self.set_title(goose_obj.title)
        self.set_keywords(goose_obj.keywords)
        self.set_authors(goose_obj.authors)

        # Parse xpath tree and query top imgs
        self.lxml_root = get_lxml_root(self.html)

        if self.lxml_root is not None:
            img_url = get_top_img(self)
            self.top_img = fix_unicode(img_url)

            top_imgs = get_imgs(self)
            top_imgs = [ fix_unicode(t) for t in top_imgs ]
            self.imgs = top_imgs

        self.set_reddit_top_img()
        self.is_parsed = True

    def is_valid_url(self):
        """performs a check on the url of this link to
        determine if a real news article or not"""

        return valid_url(self.url)

    def is_valid_body(self):
        """if the article's body text is long enough to meet
        standard article requirements, we keep the article"""

        if not self.is_parsed:
            raise ArticleException('must parse article before checking \
                                    if it\'s body is valid!')
        return valid_body(self)

    def is_media_news(self):
        """if the article is a gallery, video, etc related"""

        safe_urls = [
            '/video', '/slide', '/gallery', '/powerpoint', '/fashion',
            '/glamour', '/cloth'
        ]
        for s in safe_urls:
            if s in self.url:
                return True
        return False

    def nlp(self):
        """keyword extraction wrapper"""

        if not self.is_downloaded or not self.is_parsed:
            print 'You must download and parse an article before parsing it!'
            raise ArticleException()

        text_keyws = nlp.keywords(self.text).keys()
        title_keyws = nlp.keywords(self.title).keys()
        keyws = list(set(title_keyws + text_keyws))
        self.set_keywords(keyws)

        summary_sents = nlp.summarize(title=self.title, text=self.text)
        summary = '\r\n'.join(summary_sents)
        self.set_summary(summary)

    def set_reddit_top_img(self):
        """wrapper for setting images, queries known image attributes
        first, uses reddit's img algorithm as a fallback."""

        if self.top_img != u'': # if we already have a top img...
            return
        try:
            s = Scraper(url=self.url, imgs=self.imgs, top_img=self.top_img)
            self.top_img = s.largest_image_url()
        except Exception, e:
            log.critical('jpeg error with PIL, %s' % e)

    def set_title(self, title):
        """titles are length limited"""

        title = title[:MAX_TITLE]
        title = fix_unicode(title)
        if title:
            self.title = title

    def set_text(self, text):
        """text is length limited"""

        text = text[:MAX_TEXT-5]
        text = fix_unicode(text)
        if text:
            self.text = text

    def set_keywords(self, keywords):
        """keys are stored in list format"""

        if not isinstance(keywords, list):
            raise Exception("Keyword input must be list!")
        if keywords:
            self.keywords = [fix_unicode(k) for k in keywords[:MAX_KEYWORDS]]

    def set_authors(self, authors):
        """authors are in ["firstName lastName", "firsrtName lastName"] format"""

        if not isinstance(authors, list):
            raise Exception("authors input must be list!")
        if authors:
            authors = authors[:MAX_AUTHORS]
            self.authors = [fix_unicode(author) for author in authors]

    def set_summary(self, summary):
        """summary is a paragraph of text from the title + body text"""

        summary = summary[:MAX_SUMMARY]
        self.summary = fix_unicode(summary)
