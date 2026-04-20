# -*- coding: utf-8 -*-
"""
Holds the code for cleaning out unwanted tags from the lxml
dom xpath.
"""
import copy
from .utils import ReplaceSequence


class DocumentCleaner(object):

    def __init__(self, config):
        """Set appropriate tag names and regexes of tags to remove
        from the HTML
        """
        self.config = config
        self.parser = self.config.get_parser()
        self.remove_nodes_re = (
            "^side$|combx|retweet|mediaarticlerelated|menucontainer|"
            "navbar|storytopbar-bucket|utility-bar|inline-share-tools"
            "|comment|PopularQuestions|contact|foot|footer|Footer|footnote"
            "|cnn_strycaptiontxt|cnn_html_slideshow|cnn_strylftcntnt"
            "|links|meta$|shoutbox|sponsor"
            "|tags|socialnetworking|socialNetworking|cnnStryHghLght"
            "|cnn_stryspcvbx|^inset$|pagetools|post-attributes"
            "|welcome_form|contentTools2|the_answers"
            "|communitypromo|runaroundLeft|subscribe|vcard|articleheadings"
            "|date|^print$|popup|author-dropdown|tools|socialtools|byline"
            "|konafilter|KonaFilter|breadcrumbs|^fn$|wp-caption-text"
            "|legende|ajoutVideo|timestamp|js_replies"
        )
        # enable adding additional remove patterns through the config object
        if self.config.additional_remove_nodes_re:
            self.remove_nodes_re += '|' + self.config.additional_remove_nodes_re
        self.regexp_namespace = "http://exslt.org/regular-expressions"
        self.nauthy_ids_re = ("//*[re:test(@id, '%s', 'i')]" %
                              self.remove_nodes_re)
        self.nauthy_classes_re = ("//*[re:test(@class, '%s', 'i')]" %
                                  self.remove_nodes_re)
        self.nauthy_names_re = ("//*[re:test(@name, '%s', 'i')]" %
                                self.remove_nodes_re)
        self.div_to_p_re = r"<(a|blockquote|dl|div|img|ol|p|pre|table|ul)"
        self.caption_re = "^caption$"
        self.google_re = " google "
        self.entries_re = "^[^entry-]more.*$"
        self.facebook_re = "[^-]facebook"
        self.facebook_broadcasting_re = "facebook-broadcasting"
        self.twitter_re = "[^-]twitter"
        self.tablines_replacements = ReplaceSequence()\
            .create("\n", "\n\n")\
            .append("\t")\
            .append("^\\s+$")
        self.contains_article = './/article|.//*[@id="article"]|.//*[@itemprop="articleBody"]'

    def clean(self, doc_to_clean):
        """Remove chunks of the DOM as specified
        """
        doc_to_clean = self.clean_body_classes(doc_to_clean)
        doc_to_clean = self.clean_article_tags(doc_to_clean)
        doc_to_clean = self.clean_em_tags(doc_to_clean)
        doc_to_clean = self.remove_drop_caps(doc_to_clean)
        doc_to_clean = self.remove_scripts_styles(doc_to_clean)
        doc_to_clean = self.clean_bad_tags(doc_to_clean)
        doc_to_clean = self.remove_nodes_regex(doc_to_clean, self.caption_re)
        doc_to_clean = self.remove_nodes_regex(doc_to_clean, self.google_re)
        doc_to_clean = self.remove_nodes_regex(doc_to_clean, self.entries_re)
        doc_to_clean = self.remove_nodes_regex(doc_to_clean, self.facebook_re)
        doc_to_clean = self.remove_nodes_regex(doc_to_clean,
                                               self.facebook_broadcasting_re)
        doc_to_clean = self.remove_nodes_regex(doc_to_clean, self.twitter_re)
        doc_to_clean = self.clean_para_spans(doc_to_clean)
        doc_to_clean = self.div_to_para(doc_to_clean, 'div')
        doc_to_clean = self.div_to_para(doc_to_clean, 'span')
        doc_to_clean = self.div_to_para(doc_to_clean, 'section')
        return doc_to_clean

    def clean_body_classes(self, doc):
        """Removes the `class` attribute from the <body> tag because
        if there is a bad match, the entire DOM will be empty!
        """
        elements = self.parser.getElementsByTag(doc, tag="body")
        if elements:
            self.parser.delAttribute(elements[0], attr="class")
        return doc

    def clean_article_tags(self, doc):
        articles = self.parser.getElementsByTag(doc, tag='article')
        for article in articles:
            for attr in ['id', 'name', 'class']:
                self.parser.delAttribute(article, attr=attr)
        return doc

    def clean_em_tags(self, doc):
        ems = self.parser.getElementsByTag(doc, tag='em')
        for node in ems:
            images = self.parser.getElementsByTag(node, tag='img')
            if len(images) == 0:
                self.parser.drop_tag(node)
        return doc

    def remove_drop_caps(self, doc):
        items = self.parser.css_select(doc, 'span[class~=dropcap], '
                                       'span[class~=drop_cap]')
        for item in items:
            self.parser.drop_tag(item)
        return doc

    def remove_scripts_styles(self, doc):
        # remove scripts
        scripts = self.parser.getElementsByTag(doc, tag='script')
        for item in scripts:
            self.parser.remove(item)
        # remove styles
        styles = self.parser.getElementsByTag(doc, tag='style')
        for item in styles:
            self.parser.remove(item)
        # remove comments
        comments = self.parser.getComments(doc)
        for item in comments:
            self.parser.remove(item)

        return doc

    def clean_bad_tags(self, doc):
        # ids
        naughty_list = self.parser.xpath_re(doc, self.nauthy_ids_re)
        for node in naughty_list:
            if not node.xpath(self.contains_article):
                self.parser.remove(node)
        # class
        naughty_classes = self.parser.xpath_re(doc, self.nauthy_classes_re)
        for node in naughty_classes:
            if not node.xpath(self.contains_article):
                self.parser.remove(node)
        # name
        naughty_names = self.parser.xpath_re(doc, self.nauthy_names_re)
        for node in naughty_names:
            if not node.xpath(self.contains_article):
                self.parser.remove(node)
        return doc

    def remove_nodes_regex(self, doc, pattern):
        for selector in ['id', 'class']:
            reg = "//*[re:test(@%s, '%s', 'i')]" % (selector, pattern)
            naughty_list = self.parser.xpath_re(doc, reg)
            for node in naughty_list:
                self.parser.remove(node)
        return doc

    def clean_para_spans(self, doc):
        spans = self.parser.css_select(doc, 'p span')
        for item in spans:
            self.parser.drop_tag(item)
        return doc

    def get_flushed_buffer(self, replacement_text, doc):
        return self.parser.textToPara(replacement_text)

    def replace_walk_left_right(self, kid, kid_text,
                                replacement_text, nodes_to_remove):
        kid_text_node = kid
        replace_text = self.tablines_replacements.replaceAll(kid_text)
        if len(replace_text) > 1:
            prev_node = self.parser.previousSibling(kid_text_node)
            while prev_node is not None \
                    and self.parser.getTag(prev_node) == "a" \
                    and self.parser.getAttribute(
                        prev_node, 'grv-usedalready') != 'yes':
                outer = " " + self.parser.outerHtml(prev_node) + " "
                replacement_text.append(outer)
                nodes_to_remove.append(prev_node)
                self.parser.setAttribute(prev_node, attr='grv-usedalready',
                                         value='yes')
                prev_node = self.parser.previousSibling(prev_node)

            replacement_text.append(replace_text)
            next_node = self.parser.nextSibling(kid_text_node)
            while next_node is not None \
                    and self.parser.getTag(next_node) == "a" \
                    and self.parser.getAttribute(
                        next_node, 'grv-usedalready') != 'yes':
                outer = " " + self.parser.outerHtml(next_node) + " "
                replacement_text.append(outer)
                nodes_to_remove.append(next_node)
                self.parser.setAttribute(next_node, attr='grv-usedalready',
                                         value='yes')
                next_node = self.parser.nextSibling(next_node)

    def get_replacement_nodes(self, doc, div):
        replacement_text = []
        nodes_to_return = []
        nodes_to_remove = []
        kids = self.parser.childNodesWithText(div)
        for kid in kids:
            # The node is a <p> and already has some replacement text
            if self.parser.getTag(kid) == 'p' and len(replacement_text) > 0:
                new_node = self.get_flushed_buffer(
                    ''.join(replacement_text), doc)
                nodes_to_return.append(new_node)
                replacement_text = []
                nodes_to_return.append(kid)
            # The node is a text node
            elif self.parser.isTextNode(kid):
                kid_text = self.parser.getText(kid)
                self.replace_walk_left_right(kid, kid_text, replacement_text,
                                             nodes_to_remove)
            else:
                nodes_to_return.append(kid)

        # flush out anything still remaining
        if(len(replacement_text) > 0):
            new_node = self.get_flushed_buffer(''.join(replacement_text), doc)
            nodes_to_return.append(new_node)
            replacement_text = []

        for n in nodes_to_remove:
            self.parser.remove(n)

        return nodes_to_return

    def replace_with_para(self, doc, div):
        self.parser.replaceTag(div, 'p')

    def div_to_para(self, doc, dom_type):
        bad_divs = 0
        else_divs = 0
        divs = self.parser.getElementsByTag(doc, tag=dom_type)
        tags = ['a', 'blockquote', 'dl', 'div', 'img', 'ol', 'p',
                'pre', 'table', 'ul']
        for div in divs:
            items = self.parser.getElementsByTags(div, tags)
            if div is not None and len(items) == 0:
                self.replace_with_para(doc, div)
                bad_divs += 1
            elif div is not None:
                replace_nodes = self.get_replacement_nodes(doc, div)
                replace_nodes = [n for n in replace_nodes if n is not None]
                attrib = copy.deepcopy(div.attrib)
                div.clear()
                for i, node in enumerate(replace_nodes):
                    div.insert(i, node)
                for name, value in attrib.items():
                    div.set(name, value)
                else_divs += 1
        return doc
