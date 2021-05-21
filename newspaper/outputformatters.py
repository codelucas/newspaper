# -*- coding: utf-8 -*-
"""
Output formatting to text via lxml xpath nodes abstracted in this file.
"""
__title__ = 'newspaper'
__author__ = 'Lucas Ou-Yang'
__license__ = 'MIT'
__copyright__ = 'Copyright 2014, Lucas Ou-Yang'

import logging

from copy import deepcopy
from html import unescape
from lxml import etree
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

        self.remove_negativescores_nodes()
        # Take a copy of top_node before editing it further
        top_node_copy = deepcopy(self.top_node)
        self.links_to_text()
        self.add_newline_to_br()
        self.add_newline_to_li()
        self.replace_with_text()
        self.remove_empty_tags()
        self.remove_trailing_media_div()
        text, html = self.convert_to_text(extra_nodes, top_node_copy)
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
            # In regards to the html, take a copy of this node before parsing any hyperlinks
            extra_pre_parsed = deepcopy(extra)
            self.parser.stripTags(extra, 'a')
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
                html_idx, html_to_update = self.insert_missing_html(extra_pre_parsed, html_to_update, html_idx,
                                                                    node_found, stripped_txts[0])
        # Return final string based on txts list and html string
        return '\n\n'.join(txts), self.convert_to_html(html_to_update)

    def insert_missing_html(self, node_pre_parsed, html_to_update, html_idx, text_found, node_text):
        """A method that updates html by checking if node_text should be inserted into html_to_update. The method then
        returns the updated html and a new html-index being the position in html_to_update after the insertion."""
        # Message to warn with in case of search errors or no results
        truncated = '\'' + node_text[:30] + '...\''
        warning_msg = 'Could not determine position of element with text ' + truncated \
                      + ' Duplicates may occur in article html.'
        # Matching element(s) given node_text
        found_html = None
        try:
            # Do a starts-with search in case a sentence has been split
            found_html = html_to_update.xpath('//*[starts-with(text(), $nodetext)]', nodetext=node_text)
        except etree.XPathEvalError:
            logging.warning(warning_msg + ' Error searching for text.')
        # If we found a match
        if found_html:
            # Report if multiple matches found
            if len(found_html) > 1:
                logging.warning('Multiple matches for ' + truncated + ' in html, article html may be disordered.')
            # Flag to check if we found the match's position in html_to_update
            pos_found = False
            # The current node we are checking whilst finding the position
            current_node = found_html[0]
            # Whilst we haven't found the position and we still have a current_node to check
            while not pos_found and current_node is not None:
                try:
                    # Attempt to find its position in relation to the rest of the html and return found index + 1
                    html_idx = html_to_update.index(current_node)
                    return html_idx + 1, html_to_update
                except ValueError:
                    # If the element is not found, try the current node's parent
                    parent = current_node.getparent()
                    # If we have exhausted the search via parent nodes, exit loop
                    if current_node == parent:
                        break
                    # Set current node to be its parent to continue the search
                    current_node = parent
            # Warn if node_text is found in the html but we couldn't find the element's position
            logging.warning(
                warning_msg + ' Could not trace element with this text or parent element after xpath match.')
        # No matches with the xpath search
        else:
            # Attempt to search for the html elements from position html_idx and onwards based on text
            for search_idx, search_elem in enumerate(html_to_update[html_idx:]):
                # If we found the element this way, exit loop and return the updated html_idx
                if search_elem.text and innerTrim(search_elem.text) in node_text:
                    return html_idx + search_idx + 1, html_to_update
                # Whilst we are on this node, check its descendants; cannot use
                # self.parser.childNodesWithText() as this creates nodes with text and duplicates text in final html
                search_elem_children = self.parser.childNodes(search_elem)
                # Do same text check for each child and return updated html_idx if there's a match
                for search_elem_child in search_elem_children:
                    if search_elem_child.text and innerTrim(search_elem_child.text) in node_text:
                        return html_idx + search_idx + 1, html_to_update
            # Warn if text originally included node_text because it would have been expected to appear in the final html
            if text_found:
                logging.warning(warning_msg + ' Article text originally included this text.')
        # If we haven't returned an updated html_idx, then update html with element and return both index and html
        html_to_update.insert(html_idx, node_pre_parsed)
        return html_idx + 1, html_to_update

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
