# -*- coding: utf-8 -*-
"""
Output formatting to text via lxml xpath nodes abstracted in this file.
"""
__title__ = 'newspaper'
__author__ = 'Lucas Ou-Yang'
__license__ = 'MIT'
__copyright__ = 'Copyright 2014, Lucas Ou-Yang'

from HTMLParser import HTMLParser
from .text import innerTrim

import lxml

class OutputFormatter(object):

    def __init__(self, config):
        self.top_node = None
        self.config = config
        # parser
        self.parser = self.config.get_parser()
        self.stopwords_class = config.stopwords_class

    def get_language(self, article):
        """
        Returns the language is by the article or the configuration language.
        """
        if self.config.use_meta_language == True:
            if article.meta_lang:
                return article.meta_lang[:2]
        return self.config.language

    def get_top_node(self):
        return self.top_node

    def get_formatted(self, article):
        """
        Returns the body text of an article, and also the body article
        html if specified. Returns in (text, html) form.
        """
        self.top_node = article.top_node
        html, text = u'', u''

        self.remove_negativescores_nodes()

        if article.config.keep_article_html:
            html = self.convert_to_html()

        self.links_to_text()
        self.add_newline_to_br()
        self.replace_with_text()
        self.remove_fewwords_paragraphs(article)

        text = self.convert_to_text()
        return (text, html)

    def convert_to_text(self):
        txts = []
        for node in list(self.get_top_node()):
            txt = self.parser.getText(node)
            if txt:
                txt = HTMLParser().unescape(txt)
                txt_lis = innerTrim(txt).split(r'\n')
                txts.extend(txt_lis)
        return '\n\n'.join(txts)

    def convert_to_html(self):
        cleaned_node = self.parser.clean_article_html(self.get_top_node())
        return self.parser.node_to_string(cleaned_node)

    def add_newline_to_br(self):
        for e in self.parser.getElementsByTag(self.top_node, tag='br'):
            e.text = r'\n'

    def links_to_text(self):
        """
        Cleans up and converts any nodes that should be considered text into text.
        """
        self.parser.stripTags(self.get_top_node(), 'a')

    def remove_negativescores_nodes(self):
        """
        If there are elements inside our top node that have a negative gravity score,
        let's give em the boot.
        """
        gravity_items = self.parser.css_select(self.top_node, "*[gravityScore]")
        for item in gravity_items:
            score = self.parser.getAttribute(item, 'gravityScore')
            score = int(score, 0)
            if score < 1:
                item.getparent().remove(item)

    def replace_with_text(self):
        """
        Replace common tags with just text so we don't have any crazy
        formatting issues so replace <br>, <i>, <strong>, etc....
        With whatever text is inside them.
        code : http://lxml.de/api/lxml.etree-module.html#strip_tags
        """
        self.parser.stripTags(self.get_top_node(), 'b', 'strong', 'i', 'br', 'sup')

    def remove_fewwords_paragraphs(self, article):
        """
        Remove paragraphs that have less than x number of words,
        would indicate that it's some sort of link.
        """
        all_nodes = self.parser.getElementsByTags(self.get_top_node(), ['*'])
        all_nodes.reverse()
        for el in all_nodes:
            tag = self.parser.getTag(el)
            text = self.parser.getText(el)
            stop_words = self.stopwords_class(language=self.get_language(article)).get_stopword_count(text)
            if (tag != 'br' or text != '\\r') and stop_words.get_stopword_count() < 3 \
                and len(self.parser.getElementsByTag(el, tag='object')) == 0 \
                and len(self.parser.getElementsByTag(el, tag='embed')) == 0:
                self.parser.remove(el)
            # TODO
            # check if it is in the right place
            else:
                trimmed = self.parser.getText(el)
                if trimmed.startswith("(") and trimmed.endswith(")"):
                    self.parser.remove(el)


class StandardOutputFormatter(OutputFormatter):
    pass
