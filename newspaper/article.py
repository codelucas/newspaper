# -*- coding: utf-8 -*-
__title__ = 'newspaper'
__author__ = 'Lucas Ou-Yang'
__license__ = 'MIT'
__copyright__ = 'Copyright 2014, Lucas Ou-Yang'

import logging
import copy
import os
import glob

import requests

from . import images
from . import network
from . import nlp
from . import settings
from . import urls

from .cleaners import DocumentCleaner
from .configuration import Configuration
from .extractors import ContentExtractor
from .outputformatters import OutputFormatter
from .utils import (URLHelper, RawHelper, extend_config,
                    get_available_languages, extract_meta_refresh)
from .videos.extractors import VideoExtractor

log = logging.getLogger(__name__)


class ArticleDownloadState(object):
    NOT_STARTED = 0
    FAILED_RESPONSE = 1
    SUCCESS = 2


class ArticleException(Exception):
    pass


class Article(object):
    """Article objects abstract an online news article page
    """
    def __init__(self, url, title='', source_url='', config=None, **kwargs):
        """The **kwargs argument may be filled with config values, which
        is added into the config object
        """
        self.config = config or Configuration()
        self.config = extend_config(self.config, kwargs)

        self.extractor = ContentExtractor(self.config)

        if source_url == '':
            scheme = urls.get_scheme(url)
            if scheme is None:
                scheme = 'http'
            source_url = scheme + '://' + urls.get_domain(url)

        if source_url is None or source_url == '':
            raise ArticleException('input url bad format')

        # URL to the main page of the news source which owns this article
        self.source_url = source_url

        self.url = urls.prepare_url(url, self.source_url)

        self.title = title

        # URL of the "best image" to represent this article
        self.top_img = self.top_image = ''

        # stores image provided by metadata
        self.meta_img = ''

        # All image urls in this article
        self.imgs = self.images = []

        # All videos in this article: youtube, vimeo, etc
        self.movies = []

        # Body text from this article
        self.text = ''

        # `keywords` are extracted via nlp() from the body text
        self.keywords = []

        # `meta_keywords` are extracted via parse() from <meta> tags
        self.meta_keywords = []

        # `tags` are also extracted via parse() from <meta> tags
        self.tags = set()

        # List of authors who have published the article, via parse()
        self.authors = []

        self.publish_date = ''

        # Summary generated from the article's body txt
        self.summary = ''

        # This article's unchanged and raw HTML
        self.html = ''

        # The HTML of this article's main node (most important part)
        self.article_html = ''

        # Keep state for downloads and parsing
        self.is_parsed = False
        self.download_state = ArticleDownloadState.NOT_STARTED
        self.download_exception_msg = None

        # Meta description field in the HTML source
        self.meta_description = ""

        # Meta language field in HTML source
        self.meta_lang = ""

        # Meta favicon field in HTML source
        self.meta_favicon = ""

        # Meta tags contain a lot of structured data, e.g. OpenGraph
        self.meta_data = {}

        # The canonical link of this article if found in the meta data
        self.canonical_link = ""

        # Holds the top element of the DOM that we determine is a candidate
        # for the main body of the article
        self.top_node = None

        # A deepcopied clone of the above object before heavy parsing
        # operations, useful for users to query data in the
        # "most important part of the page"
        self.clean_top_node = None

        # lxml DOM object generated from HTML
        self.doc = None

        # A deepcopied clone of the above object before undergoing heavy
        # cleaning operations, serves as an API if users need to query the DOM
        self.clean_doc = None

        # A property dict for users to store custom data.
        self.additional_data = {}

    def build(self):
        """Build a lone article from a URL independent of the source (newspaper).
        Don't normally call this method b/c it's good to multithread articles
        on a source (newspaper) level.
        """
        self.download()
        self.parse()
        self.nlp()

    def download(self, input_html=None, title=None, recursion_counter=0):
        """Downloads the link's HTML content, don't use if you are batch async
        downloading articles

        recursion_counter (currently 1) stops refreshes that are potentially
        infinite
        """
        if input_html is None:
            try:
                html = network.get_html_2XX_only(self.url, self.config)
            except requests.exceptions.RequestException as e:
                self.download_state = ArticleDownloadState.FAILED_RESPONSE
                self.download_exception_msg = str(e)
                log.debug('Download failed on URL %s because of %s' %
                          (self.url, self.download_exception_msg))
                return
        else:
            html = input_html

        if self.config.follow_meta_refresh:
            meta_refresh_url = extract_meta_refresh(html)
            if meta_refresh_url and recursion_counter < 1:
                return self.download(
                    input_html=network.get_html(meta_refresh_url),
                    recursion_counter=recursion_counter + 1)

        self.set_html(html)
        self.set_title(title)

    def parse(self):
        self.throw_if_not_downloaded_verbose()

        self.doc = self.config.get_parser().fromstring(self.html)
        self.clean_doc = copy.deepcopy(self.doc)

        if self.doc is None:
            # `parse` call failed, return nothing
            return

        # TODO: Fix this, sync in our fix_url() method
        parse_candidate = self.get_parse_candidate()
        self.link_hash = parse_candidate.link_hash  # MD5

        document_cleaner = DocumentCleaner(self.config)
        output_formatter = OutputFormatter(self.config)

        title = self.extractor.get_title(self.clean_doc)
        self.set_title(title)

        authors = self.extractor.get_authors(self.clean_doc)
        self.set_authors(authors)

        meta_lang = self.extractor.get_meta_lang(self.clean_doc)
        self.set_meta_language(meta_lang)

        if self.config.use_meta_language:
            self.extractor.update_language(self.meta_lang)
            output_formatter.update_language(self.meta_lang)

        meta_favicon = self.extractor.get_favicon(self.clean_doc)
        self.set_meta_favicon(meta_favicon)

        meta_description = \
            self.extractor.get_meta_description(self.clean_doc)
        self.set_meta_description(meta_description)

        canonical_link = self.extractor.get_canonical_link(
            self.url, self.clean_doc)
        self.set_canonical_link(canonical_link)

        tags = self.extractor.extract_tags(self.clean_doc)
        self.set_tags(tags)

        meta_keywords = self.extractor.get_meta_keywords(
            self.clean_doc)
        self.set_meta_keywords(meta_keywords)

        meta_data = self.extractor.get_meta_data(self.clean_doc)
        self.set_meta_data(meta_data)

        self.publish_date = self.extractor.get_publishing_date(
            self.url,
            self.clean_doc)

        # Before any computations on the body, clean DOM object
        self.doc = document_cleaner.clean(self.doc)

        self.top_node = self.extractor.calculate_best_node(self.doc)
        if self.top_node is not None:
            video_extractor = VideoExtractor(self.config, self.top_node)
            self.set_movies(video_extractor.get_videos())

            self.top_node = self.extractor.post_cleanup(self.top_node)
            self.clean_top_node = copy.deepcopy(self.top_node)

            text, article_html = output_formatter.get_formatted(
                self.top_node)
            self.set_article_html(article_html)
            self.set_text(text)

        if self.config.fetch_images:
            self.fetch_images()

        self.is_parsed = True
        self.release_resources()

    def fetch_images(self):
        if self.clean_doc is not None:
            meta_img_url = self.extractor.get_meta_img_url(
                self.url, self.clean_doc)
            self.set_meta_img(meta_img_url)

            imgs = self.extractor.get_img_urls(self.url, self.clean_doc)
            if self.meta_img:
                imgs.add(self.meta_img)
            self.set_imgs(imgs)

        if self.clean_top_node is not None and not self.has_top_image():
            first_img = self.extractor.get_first_img_url(
                self.url, self.clean_top_node)
            self.set_top_img(first_img)

        if not self.has_top_image():
            self.set_reddit_top_img()

    def has_top_image(self):
        return self.top_img is not None and self.top_img != ''

    def is_valid_url(self):
        """Performs a check on the url of this link to determine if article
        is a real news article or not
        """
        return urls.valid_url(self.url)

    def is_valid_body(self):
        """If the article's body text is long enough to meet
        standard article requirements, keep the article
        """
        if not self.is_parsed:
            raise ArticleException('must parse article before checking \
                                    if it\'s body is valid!')
        meta_type = self.extractor.get_meta_type(self.clean_doc)
        wordcount = self.text.split(' ')
        sentcount = self.text.split('.')

        if (meta_type == 'article' and len(wordcount) >
                (self.config.MIN_WORD_COUNT)):
            log.debug('%s verified for article and wc' % self.url)
            return True

        if not self.is_media_news() and not self.text:
            log.debug('%s caught for no media no text' % self.url)
            return False

        if self.title is None or len(self.title.split(' ')) < 2:
            log.debug('%s caught for bad title' % self.url)
            return False

        if len(wordcount) < self.config.MIN_WORD_COUNT:
            log.debug('%s caught for word cnt' % self.url)
            return False

        if len(sentcount) < self.config.MIN_SENT_COUNT:
            log.debug('%s caught for sent cnt' % self.url)
            return False

        if self.html is None or self.html == '':
            log.debug('%s caught for no html' % self.url)
            return False

        log.debug('%s verified for default true' % self.url)
        return True

    def is_media_news(self):
        """If the article is related heavily to media:
        gallery, video, big pictures, etc
        """
        safe_urls = ['/video', '/slide', '/gallery', '/powerpoint',
                     '/fashion', '/glamour', '/cloth']
        for s in safe_urls:
            if s in self.url:
                return True
        return False

    def nlp(self):
        """Keyword extraction wrapper
        """
        self.throw_if_not_downloaded_verbose()
        self.throw_if_not_parsed_verbose()

        text_keyws = list(nlp.keywords(self.text).keys())
        title_keyws = list(nlp.keywords(self.title).keys())
        keyws = list(set(title_keyws + text_keyws))
        self.set_keywords(keyws)

        max_sents = self.config.MAX_SUMMARY_SENT

        summary_sents = nlp.summarize(title=self.title, text=self.text, max_sents=max_sents)
        summary = '\n'.join(summary_sents)
        self.set_summary(summary)

    def get_parse_candidate(self):
        """A parse candidate is a wrapper object holding a link hash of this
        article and a final_url of the article
        """
        if self.html:
            return RawHelper.get_parsing_candidate(self.url, self.html)
        return URLHelper.get_parsing_candidate(self.url)

    def build_resource_path(self):
        """Must be called after computing HTML/final URL
        """
        res_path = self.get_resource_path()
        if not os.path.exists(res_path):
            os.mkdir(res_path)

    def get_resource_path(self):
        """Every article object has a special directory to store data in from
        initialization to garbage collection
        """
        res_dir_fn = 'article_resources'
        resource_directory = os.path.join(settings.TOP_DIRECTORY, res_dir_fn)
        if not os.path.exists(resource_directory):
            os.mkdir(resource_directory)
        dir_path = os.path.join(resource_directory, '%s_' % self.link_hash)
        return dir_path

    def release_resources(self):
        # TODO: implement in entirety
        path = self.get_resource_path()
        for fname in glob.glob(path):
            try:
                os.remove(fname)
            except OSError:
                pass
        # os.remove(path)

    def set_reddit_top_img(self):
        """Wrapper for setting images. Queries known image attributes
        first, then uses Reddit's image algorithm as a fallback.
        """
        try:
            s = images.Scraper(self)
            self.set_top_img(s.largest_image_url())
        except TypeError as e:
            if "Can't convert 'NoneType' object to str implicitly" in e.args[0]:
                log.debug('No pictures found. Top image not set, %s' % e)
            elif 'timed out' in e.args[0]:
                log.debug('Download of picture timed out. Top image not set, %s' % e)
            else:
                log.critical('TypeError other than None type error. '
                             'Cannot set top image using the Reddit '
                             'algorithm. Possible error with PIL., %s' % e)
        except Exception as e:
            log.critical('Other error with setting top image using the '
                         'Reddit algorithm. Possible error with PIL, %s' % e)

    def set_title(self, input_title):
        if input_title:
            self.title = input_title[:self.config.MAX_TITLE]

    def set_text(self, text):
        text = text[:self.config.MAX_TEXT]
        if text:
            self.text = text

    def set_html(self, html):
        """Encode HTML before setting it
        """
        if html:
            if isinstance(html, bytes):
                html = self.config.get_parser().get_unicode_html(html)
            self.html = html
            self.download_state = ArticleDownloadState.SUCCESS

    def set_article_html(self, article_html):
        """Sets the HTML of just the article's `top_node`
        """
        if article_html:
            self.article_html = article_html

    def set_meta_img(self, src_url):
        self.meta_img = src_url
        self.set_top_img_no_check(src_url)

    def set_top_img(self, src_url):
        if src_url is not None:
            s = images.Scraper(self)
            if s.satisfies_requirements(src_url):
                self.set_top_img_no_check(src_url)

    def set_top_img_no_check(self, src_url):
        """Provide 2 APIs for images. One at "top_img", "imgs"
        and one at "top_image", "images"
        """
        self.top_img = src_url
        self.top_image = src_url

    def set_imgs(self, imgs):
        """The motive for this method is the same as above, provide APIs
        for both `article.imgs` and `article.images`
        """
        self.images = imgs
        self.imgs = imgs

    def set_keywords(self, keywords):
        """Keys are stored in list format
        """
        if not isinstance(keywords, list):
            raise Exception("Keyword input must be list!")
        if keywords:
            self.keywords = keywords[:self.config.MAX_KEYWORDS]

    def set_authors(self, authors):
        """Authors are in ["firstName lastName", "firstName lastName"] format
        """
        if not isinstance(authors, list):
            raise Exception("authors input must be list!")
        if authors:
            self.authors = authors[:self.config.MAX_AUTHORS]

    def set_summary(self, summary):
        """Summary here refers to a paragraph of text from the
        title text and body text
        """
        self.summary = summary[:self.config.MAX_SUMMARY]

    def set_meta_language(self, meta_lang):
        """Save langauges in their ISO 2-character form
        """
        if meta_lang and len(meta_lang) >= 2 and \
           meta_lang in get_available_languages():
            self.meta_lang = meta_lang[:2]

    def set_meta_keywords(self, meta_keywords):
        """Store the keys in list form
        """
        self.meta_keywords = [k.strip() for k in meta_keywords.split(',')]

    def set_meta_favicon(self, meta_favicon):
        self.meta_favicon = meta_favicon

    def set_meta_description(self, meta_description):
        self.meta_description = meta_description

    def set_meta_data(self, meta_data):
        self.meta_data = meta_data

    def set_canonical_link(self, canonical_link):
        self.canonical_link = canonical_link

    def set_tags(self, tags):
        self.tags = tags

    def set_movies(self, movie_objects):
        """Trim video objects into just urls
        """
        movie_urls = [o.src for o in movie_objects if o and o.src]
        self.movies = movie_urls

    def throw_if_not_downloaded_verbose(self):
        """Parse ArticleDownloadState -> log readable status
        -> maybe throw ArticleException
        """
        if self.download_state == ArticleDownloadState.NOT_STARTED:
            print('You must `download()` an article first!')
            raise ArticleException()
        elif self.download_state == ArticleDownloadState.FAILED_RESPONSE:
            print('Article `download()` failed with %s on URL %s' %
                  (self.download_exception_msg, self.url))
            raise ArticleException()

    def throw_if_not_parsed_verbose(self):
        """Parse `is_parsed` status -> log readable status 
        -> maybe throw ArticleException
        """
        if not self.is_parsed:
            print('You must `parse()` an article first!')
            raise ArticleException()
