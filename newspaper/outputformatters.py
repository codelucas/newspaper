# -*- coding: utf-8 -*-
"""
Output formatting to text via lxml xpath nodes abstracted in this file.
"""
__title__ = 'newspaper'
__author__ = 'Lucas Ou-Yang'
__license__ = 'MIT'
__copyright__ = 'Copyright 2014, Lucas Ou-Yang'

import logging
import re

from html import unescape
from .text import innerTrim


log = logging.getLogger(__name__)


# A small method to prepare a given string so it can be added to string list
def _prepare_txt(txt):
    if txt:
        txt = unescape(txt)
        txt_lis = innerTrim(txt).split(r'\n')
        txt_lis = [n.strip(' ') for n in txt_lis]
        return txt_lis
    return []


# A small method to update a txts list with a given string list
def _update_text_list(txts, to_add, index=None):
    if index is not None:
        # If we are given an index, insert the list's elements at the specified index
        txts[index:0] = to_add
    else:
        # Else add the list's elements to the end of txts
        txts.extend(to_add)


def insert_missing_html(html_idx, text_found, pre_parsed_html, parsed_html, node_text, html_to_update):
    """A method that updates html by checking if pre_parsed_html (or parsed_html) which represents node_text should be
    inserted into html_to_update. The method then returns the updated html and a new html-index being the position
    in html_to_update after the insertion."""
    # Begin by assuming we need to update the html with the given pre_parsed_html
    update_html = True
    # If the pre-parsed html already exists in the html...
    if pre_parsed_html in html_to_update:
        # then update the html-index to be its position in the html and flag we do not need to update the html
        html_idx = html_to_update.index(pre_parsed_html)
        update_html = False
    # If the parsed html for this node already exists in the html...
    elif parsed_html in html_to_update:
        # then update the html-index to be its position in the html and continue loop to avoid increment
        html_idx = html_to_update.index(parsed_html) + len(parsed_html)
        logging.warning('Text in article html \'' + node_text[:10] + '...\' is missing hyperlink(s).')
        return html_to_update, html_idx
    # Else if the html is not there but its text was found previously when updating the article text...
    elif text_found:
        # Message to warn with in case of regex search errors or no results
        warning_msg = 'Could not locate position of text \'' + node_text[:10] \
                      + '...\' in article html; output html may be out of order.'
        # attempt to find a variation of the text within the html
        # Make a copy of the text and flag all spaces in between the words to be '.*' (any characters)
        text_copy = innerTrim(node_text[:])
        # Replace any characters that might trigger errors (html tags may be in between word and .; double hyphen can
        # cause matching issues)
        text_copy = text_copy.replace('—', ' ').replace('.', '').replace('\\', '\\\\')
        text_copy_r = text_copy.replace(' ', '.*?')
        try:
            # Search for this combination of words (the node's text) in the html (re.S to consider \n)
            html_match = re.search(text_copy_r, html_to_update, re.S)
        except re.error as e:
            logging.warning('Error encountered: ' + str(e) + '\n' + warning_msg)
            return html_to_update, html_idx
        # If we found a match...
        if html_match:
            # Obtain the start of this match
            match_start = html_match.span()[0]
            # Search for the first opening tag after the last word in node_text. Not guaranteed to acknowledge
            # embedded html tags within the found html representing node_text but can ensure the sentence will
            # not be split (e.g. in case of an anchor tag representing a hyperlink in the middle of a sentence).
            words = text_copy.split()  # Obtain the words of the node's text
            # The starting position to search where the last word was found from where the match began (i.e.) not
            # within the whole string.
            # Add match_start to get index based off of html_to_update and not in relation to the substring
            # Return index value as is if we can't find the end of node_text's sentence in existing html
            try:
                start_search = html_to_update[match_start:].index(words.pop()) + match_start
            except ValueError:
                logging.warning(warning_msg)
                return html_to_update, html_idx
            open_tag_match = re.search(r'<[^/\n].*>', html_to_update[start_search:], re.S)
            # If an open tag was found, update html-index to to be its position in html_to_update
            if open_tag_match:
                html_idx = open_tag_match.span()[0] + start_search
            # If no more open tags occur after this node's text in the html, make html-index point to the
            # end of html_to_update so future nodes are added in order after this node_text
            else:
                html_idx = len(html_to_update)
            # Return index as is because we do not need to update html and do not want html_idx to increment
            return html_to_update, html_idx
    # If we are updating the html
    if update_html:
        # Tidy up this node's html before inserting before and after the specified html-index
        pre_parsed_html = innerTrim(pre_parsed_html) + '\n'
        html_to_update = html_to_update[:html_idx] + pre_parsed_html + html_to_update[html_idx:]
    # Increment html_idx by the length of characters for this node's html
    return html_to_update, html_idx + len(pre_parsed_html)


class OutputFormatter(object):

    def __init__(self, config, extractor):
        self.top_node = None
        self.config = config
        self.extractor = extractor
        self.parser = self.config.get_parser()
        self.language = config.language
        self.stopwords_class = config.stopwords_class

    def update_language(self, meta_lang):
        '''Required to be called before the extraction process in some
        cases because the stopwords_class has to set incase the lang
        is not latin based
        '''
        if meta_lang:
            self.language = meta_lang
            self.stopwords_class = \
                self.config.get_stopwords_class(meta_lang)

    def get_top_node(self):
        return self.top_node

    def get_formatted(self, top_node, extra_nodes=[]):
        """Returns the body text of an article, and also the body article
        html if specified. Returns in (text, html) form
        """
        self.top_node = top_node
        html, text = '', ''

        self.remove_negativescores_nodes()

        if self.config.keep_article_html:
            html = self.convert_to_html()

        self.links_to_text()
        self.add_newline_to_br()
        self.add_newline_to_li()
        self.replace_with_text()
        self.remove_empty_tags()
        self.remove_trailing_media_div()
        text, html = self.convert_to_text(extra_nodes, html)
        # print(self.parser.nodeToString(self.get_top_node()))
        return (text, html)

    def convert_to_text(self, extra_nodes, html_to_update):
        # The current list of texts to be used for a final combined, joined text
        txts = []
        # Obtain the text based on top_node
        for node in list(self.get_top_node()):
            try:
                txt = self.parser.getText(node)
            except ValueError as err:  # lxml error
                log.info('%s ignoring lxml node error: %s', __title__, err)
                txt = None
            _update_text_list(txts, _prepare_txt(txt))
        # Factor in any missing text before returning final result
        return self.add_missing_text(txts, extra_nodes, html_to_update)

    def add_missing_text(self, txts, extra_nodes, html_to_update):
        """A method to return (text, html) given the current text and html so far (txts list and html_to_update).
        The method uses extra_nodes to consider any text that needs to be added before returning final text and html."""
        # Keep track of the current index we are on for the text and html
        current_idx, html_idx = 0, 0
        # For each additional node we have...
        for extra in extra_nodes:
            # Ignore non-text nodes or nodes with a high link density
            if extra.text is None or self.extractor.is_highlink_density(extra):
                continue
            # Prepare the node's text if it were to be added; count the length of the list to be added
            stripped_txts = _prepare_txt(extra.text)
            txt_count = len(stripped_txts)
            # Check the text is not already within the final txts list
            match = set(stripped_txts).intersection(txts)
            node_found = bool(len(match))
            # In regards to the html, convert to html and then parse any hyperlinks
            pre_parsed_html = self.convert_to_html(extra)
            self.parser.stripTags(extra, 'a')
            parsed_html = self.convert_to_html(extra)
            # If the text is already in the txts list, update current_idx to be where the node's text is + 1
            if node_found:
                # In case of multiple entries for this node's text, gather all indices of the text in txts and
                # find the max (latest) entry
                found_idxs = []
                for m in match:
                    found_idxs.append(txts.index(m))
                current_idx = max(found_idxs) + 1
            # If the current node's text has not been added to the final txts list
            else:
                _update_text_list(txts, _prepare_txt(extra.text), index=current_idx)
                # Update current_idx to be incremented by how many entries were added to txts
                current_idx += txt_count
            # Update the html if it should be updated
            if self.config.keep_article_html:
                html_to_update, html_idx = insert_missing_html(html_idx, node_found, pre_parsed_html,
                                                               parsed_html, extra.text, html_to_update)
        # Return final string based on txts list
        return '\n\n'.join(txts), html_to_update

    def convert_to_html(self, node=None):
        if node is None:
            node = self.get_top_node()
        cleaned_node = self.parser.clean_article_html(node)
        return self.parser.nodeToString(cleaned_node)

    def add_newline_to_br(self):
        for e in self.parser.getElementsByTag(self.top_node, tag='br'):
            e.text = r'\n'

    def add_newline_to_li(self):
        for e in self.parser.getElementsByTag(self.top_node, tag='ul'):
            li_list = self.parser.getElementsByTag(e, tag='li')
            for li in li_list[:-1]:
                li.text = self.parser.getText(li) + r'\n'
                for c in self.parser.getChildren(li):
                    self.parser.remove(c)

    def links_to_text(self):
        """Cleans up and converts any nodes that should be considered
        text into text.
        """
        self.parser.stripTags(self.get_top_node(), 'a')

    def remove_negativescores_nodes(self):
        """If there are elements inside our top node that have a
        negative gravity score, let's give em the boot.
        """
        gravity_items = self.parser.css_select(
            self.top_node, "*[gravityScore]")
        for item in gravity_items:
            score = self.parser.getAttribute(item, 'gravityScore')
            score = float(score) if score else 0
            if score < 1:
                item.getparent().remove(item)

    def replace_with_text(self):
        """
        Replace common tags with just text so we don't have any crazy
        formatting issues so replace <br>, <i>, <strong>, etc....
        With whatever text is inside them.
        code : http://lxml.de/api/lxml.etree-module.html#strip_tags
        """
        self.parser.stripTags(
            self.get_top_node(), 'b', 'strong', 'i', 'br', 'sup')

    def remove_empty_tags(self):
        """It's common in top_node to exit tags that are filled with data
        within properties but not within the tags themselves, delete them
        """
        all_nodes = self.parser.getElementsByTags(
            self.get_top_node(), ['*'])
        all_nodes.reverse()
        for el in all_nodes:
            tag = self.parser.getTag(el)
            text = self.parser.getText(el)
            if (tag != 'br' or text != '\\r') \
                    and not text \
                    and len(self.parser.getElementsByTag(
                        el, tag='object')) == 0 \
                    and len(self.parser.getElementsByTag(
                        el, tag='embed')) == 0:
                self.parser.remove(el)

    def remove_trailing_media_div(self):
        """Punish the *last top level* node in the top_node if it's
        DOM depth is too deep. Many media non-content links are
        eliminated: "related", "loading gallery", etc. It skips removal if
        last top level node's class is one of NON_MEDIA_CLASSES.
        """

        NON_MEDIA_CLASSES = ('zn-body__read-all', )

        def get_depth(node, depth=1):
            """Computes depth of an lxml element via BFS, this would be
            in parser if it were used anywhere else besides this method
            """
            children = self.parser.getChildren(node)
            if not children:
                return depth
            max_depth = 0
            for c in children:
                e_depth = get_depth(c, depth + 1)
                if e_depth > max_depth:
                    max_depth = e_depth
            return max_depth

        top_level_nodes = self.parser.getChildren(self.get_top_node())
        if len(top_level_nodes) < 3:
            return

        last_node = top_level_nodes[-1]

        last_node_class = self.parser.getAttribute(last_node, 'class')
        if last_node_class in NON_MEDIA_CLASSES:
            return

        if get_depth(last_node) >= 2:
            self.parser.remove(last_node)
