# -*- coding: utf-8 -*-

import logging
import base64
import hashlib

from .utils import fix_unicode
from .urls import prepare_url, get_domain, get_scheme, valid_url
# TODO from .nlp import summarize, keywords
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

class Article(object):

    def __init__(self, url, title=u'', source_url=None):
        if source_url is None:
            source_url = get_scheme(url)+'://'+get_domain(url)

        if source_url is None or source_url == '':
            self.rejected = True
            return

        source_url = fix_unicode(source_url)

        self.url = fix_unicode(url)
        self.url = prepare_url(self.url, source_url)
        self.title = fix_unicode(title)

        self.top_img = u''
        self.text = u''
        self.keywords = u''
        self.authors = []
        self.published = u'' # TODO

        self.domain = get_domain(source_url)
        self.scheme = get_scheme(source_url)
        self.rejected = False

        self.html = u''
        self.lxml_root = None

        self.imgs = []

        # If a url is from a feed, we know it's pre-validated,
        # otherwise, we need to make sure its a news article.
        # if not from_feed: TODO Once we figure out feedparser again, restore this
        self.verify_url()

    def build(self):
        """build a lone article from a url independent of the
        source (newspaper). We won't normally call this method b/c
        we want to multithread articles on a source (newspaper) level"""

        self.download()
        self.parse()
        self.set_top_img()
        self.extract_nlp()

    def get_key(self):
        """returns a md5 representation of the url"""

        return base64.urlsafe_b64encode(hashlib.md5(self.url).digest())

    def download(self, timeout=7):
        """downloads the link's html content, don't use if we are async
        downloading batch articles"""

        if self.rejected:
            return
        self.html = get_html(self.url, timeout=timeout)

    def parse(self):
        """extracts the lxml root, if lxml fails, we also extract the
        BeautifulSoup root. We also parse images to keep cpu bound
        tasks all in one place."""

        goose_obj = GooseObj(self)
        self.set_text(goose_obj.body_text)
        self.set_title(goose_obj.title)
        self.set_keywords(goose_obj.keywords)
        self.set_authors(goose_obj.authors)

        self.verify_body()
        if self.rejected:
            return

        # Parse xpath tree and query top imgs
        self.lxml_root = get_lxml_root(self.html)

        if self.lxml_root is not None:
            img_url = get_top_img(self)
            self.top_img = fix_unicode(img_url)

            top_imgs = get_imgs(self)
            top_imgs = [ fix_unicode(t) for t in top_imgs ]
            self.imgs = top_imgs

    def verify_url(self):
        """performs a check on the url of this link to
        determine if a real news article or not"""

        if self.rejected:
            return
        self.rejected = not valid_url(self.url)

    def verify_body(self):
        """if the article's body text is long enough to meet
        standard article requirements, we keep the article"""

        if self.rejected:
            return
        self.rejected = not valid_body(self)

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

    def extract_nlp(self):
        """keyword extraction wrapper"""

        if self.rejected:
            return
        # TODO keys = get_keywords(self)
        # TODO self.set_keywords(keys)

    def set_top_img(self):
        """wrapper for setting images, queries known image attributes
        first, uses reddit's img algorithm as a fallback."""

        if self.rejected or self.top_img != u'': # if we already have a top img...
            return
        try:
            s = Scraper(url=self.url, imgs=self.imgs, top_img=self.top_img)
            self.top_img = s.largest_image_url()
        except Exception, e:
            log.critical('jpeg error with PIL, %s' % e)

    def set_title(self, title):
        """titles are length limited"""

        title = fix_unicode(title)[:MAX_TITLE]
        if title:
            self.title = title

    def set_text(self, text):
        """text is length limited"""

        text = fix_unicode(text)[:MAX_TEXT-5]
        if text:
            self.text = text

    def set_keywords(self, keywords):
        """keys are stored in list format"""

        if not isinstance(keywords, list):
            raise Exception("Keyword input must be list!")

        if keywords:
            self.keywords = [fix_unicode(k) for k in keywords[:MAX_KEYWORDS]]

    def set_authors(self, authors):
        """set authors, perhaps add a limit in future"""

        if authors is not None and isinstance(authors, list):
            self.authors = authors
