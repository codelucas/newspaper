# -*- coding: utf-8 -*-

"""
import os
import glob
from copy import deepcopy
from goose.article import Article
from goose.utils import URLHelper, RawHelper
from goose.extractors import StandardContentExtractor
from goose.cleaners import StandardDocumentCleaner
from goose.outputformatters import StandardOutputFormatter
from goose.images.extractors import UpgradedImageIExtractor
from goose.videos.extractors import VideoExtractor
from goose.network import HtmlFetcher


class CrawlCandidate(object):

    def __init__(self, config, url, raw_html):
        self.config = config
        # parser
        self.parser = self.config.get_parser()
        self.url = url
        self.raw_html = raw_html


class Crawler(object):

    def __init__(self, config):
        self.config = config
        # parser
        self.parser = self.config.get_parser()
        self.logPrefix = "crawler:"

    def crawl(self, crawl_candidate):
        article = Article()

        parse_candidate = self.get_parse_candidate(crawl_candidate)
        raw_html = self.get_html(crawl_candidate, parse_candidate)

        if raw_html is None:
            return article

        doc = self.get_document(raw_html)

        extractor = self.get_extractor()
        document_cleaner = self.get_document_cleaner()
        output_formatter = self.get_output_formatter()

        # article
        article.final_url = parse_candidate.url
        article.link_hash = parse_candidate.link_hash
        article.raw_html = raw_html
        article.doc = doc
        article.raw_doc = deepcopy(doc)
        article.title = extractor.get_title(article)
        # TODO
        # article.publish_date = config.publishDateExtractor.extract(doc)
        # article.additional_data = config.get_additionaldata_extractor.extract(doc)
        article.meta_lang = extractor.get_meta_lang(article)
        article.meta_favicon = extractor.get_favicon(article)
        article.meta_description = extractor.get_meta_description(article)
        article.meta_keywords = extractor.get_meta_keywords(article)
        article.canonical_link = extractor.get_canonical_link(article)
        article.domain = extractor.get_domain(article.final_url)
        article.tags = extractor.extract_tags(article)
        # # before we do any calcs on the body itself let's clean up the document
        article.doc = document_cleaner.clean(article)

        # big stuff
        article.top_node = extractor.calculate_best_node(article)
        if article.top_node is not None:
            # video handeling
            video_extractor = self.get_video_extractor(article)
            video_extractor.get_videos()
            # image handeling
            if self.config.enable_image_fetching:
                image_extractor = self.get_image_extractor(article)
                article.top_image = image_extractor.get_best_image(article.raw_doc, article.top_node)
            # post cleanup
            article.top_node = extractor.post_cleanup(article.top_node)
            # clean_text
            article.cleaned_text = output_formatter.get_formatted_text(article)

        # cleanup tmp file
        self.relase_resources(article)

        return article

    def get_parse_candidate(self, crawl_candidate):
        if crawl_candidate.raw_html:
            return RawHelper.get_parsing_candidate(crawl_candidate.url, crawl_candidate.raw_html)
        return URLHelper.get_parsing_candidate(crawl_candidate.url)

    def get_html(self, crawl_candidate, parsing_candidate):
        if crawl_candidate.raw_html:
            return crawl_candidate.raw_html
        # fetch HTML
        html = HtmlFetcher().get_html(self.config, parsing_candidate.url)
        return html

    def get_image_extractor(self, article):
        http_client = None
        return UpgradedImageIExtractor(http_client, article, self.config)

    def get_video_extractor(self, article):
        return VideoExtractor(article, self.config)

    def get_output_formatter(self):
        return StandardOutputFormatter(self.config)

    def get_document_cleaner(self):
        return StandardDocumentCleaner(self.config)

    def get_document(self, raw_html):
        doc = self.parser.fromstring(raw_html)
        return doc

    def get_extractor(self):
        return StandardContentExtractor(self.config)

    def relase_resources(self, article):
        path = os.path.join(self.config.local_storage_path, '%s_*' % article.link_hash)
        for fname in glob.glob(path):
            try:
                os.remove(fname)
            except OSError:
                # TODO better log handeling
                pass
"""

"""
def fix_unicode(inputstr):

    if inputstr is None:
        return u''

    if not isinstance(inputstr, unicode):
        try:
            inputstr = inputstr.decode('utf8', errors='ignore')
        except ValueError, e:
            log.debug(e)
            inputstr = u''

    inputstr = inputstr.strip()
    return inputstr
"""