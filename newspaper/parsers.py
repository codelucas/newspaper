# -*- coding: utf-8 -*-
"""
Newspaper uses a lot of python-goose's parsing code. View theirlicense:
https://github.com/codelucas/newspaper/blob/master/GOOSE-LICENSE.txt

Parser objects will only contain operations that manipulate
or query an lxml or soup dom object generated from an article's html.
"""
import logging
import lxml.etree
import lxml.html
import lxml.html.clean
import re
from html import unescape
import string

from bs4 import UnicodeDammit
from copy import deepcopy

from . import text

log = logging.getLogger(__name__)


class Parser(object):

    @classmethod
    def xpath_re(cls, node, expression):
        regexp_namespace = "http://exslt.org/regular-expressions"
        items = node.xpath(expression, namespaces={'re': regexp_namespace})
        return items

    @classmethod
    def drop_tag(cls, nodes):
        if isinstance(nodes, list):
            for node in nodes:
                node.drop_tag()
        else:
            nodes.drop_tag()

    @classmethod
    def css_select(cls, node, selector):
        return node.cssselect(selector)

    @classmethod
    def get_unicode_html(cls, html):
        if isinstance(html, str):
            return html
        if not html:
            return html
        converted = UnicodeDammit(html, is_html=True)
        if not converted.unicode_markup:
            raise Exception(
                'Failed to detect encoding of article HTML, tried: %s' %
                ', '.join(converted.tried_encodings))
        html = converted.unicode_markup
        return html

    @classmethod
    def fromstring(cls, html):
        html = cls.get_unicode_html(html)
        # Enclosed in a `try` to prevent bringing the entire library
        # down due to one article (out of potentially many in a `Source`)
        try:
            # lxml does not play well with <? ?> encoding tags
            if html.startswith('<?'):
                html = re.sub(r'^\<\?.*?\?\>', '', html, flags=re.DOTALL)
            cls.doc = lxml.html.fromstring(html)
            return cls.doc
        except Exception:
            log.warn('fromstring() returned an invalid string: %s...', html[:20])
            return

    @classmethod
    def clean_article_html(cls, node):
        article_cleaner = lxml.html.clean.Cleaner()
        article_cleaner.javascript = True
        article_cleaner.style = True
        article_cleaner.allow_tags = [
            'a', 'span', 'p', 'br', 'strong', 'b',
            'em', 'i', 'tt', 'code', 'pre', 'blockquote', 'img', 'h1',
            'h2', 'h3', 'h4', 'h5', 'h6',
            'ul', 'ol', 'li', 'dl', 'dt', 'dd']
        article_cleaner.remove_unknown_tags = False
        return article_cleaner.clean_html(node)

    @classmethod
    def nodeToString(cls, node):
        """`decode` is needed at the end because `etree.tostring`
        returns a python bytestring
        """
        return lxml.etree.tostring(node, method='html').decode()

    @classmethod
    def replaceTag(cls, node, tag):
        node.tag = tag

    @classmethod
    def stripTags(cls, node, *tags):
        lxml.etree.strip_tags(node, *tags)

    @classmethod
    def getElementById(cls, node, idd):
        selector = '//*[@id="%s"]' % idd
        elems = node.xpath(selector)
        if elems:
            return elems[0]
        return None

    @classmethod
    def getElementsByTag(
            cls, node, tag=None, attr=None, value=None, childs=False, use_regex=False) -> list:
        NS = None
        # selector = tag or '*'
        selector = 'descendant-or-self::%s' % (tag or '*')
        if attr and value:
            if use_regex:
                NS = {"re": "http://exslt.org/regular-expressions"}
                selector = '%s[re:test(@%s, "%s", "i")]' % (selector, attr, value)
            else:
                trans = 'translate(@%s, "%s", "%s")' % (attr, string.ascii_uppercase, string.ascii_lowercase)
                selector = '%s[contains(%s, "%s")]' % (selector, trans, value.lower())
        elems = node.xpath(selector, namespaces=NS)
        # remove the root node
        # if we have a selection tag
        if node in elems and (tag or childs):
            elems.remove(node)
        return elems

    @classmethod
    def appendChild(cls, node, child):
        node.append(child)

    @classmethod
    def childNodes(cls, node):
        return list(node)

    @classmethod
    def childNodesWithText(cls, node):
        root = node
        # create the first text node
        # if we have some text in the node
        if root.text:
            t = lxml.html.HtmlElement()
            t.text = root.text
            t.tag = 'text'
            root.text = None
            root.insert(0, t)
        # loop childs
        for c, n in enumerate(list(root)):
            idx = root.index(n)
            # don't process texts nodes
            if n.tag == 'text':
                continue
            # create a text node for tail
            if n.tail:
                t = cls.createElement(tag='text', text=n.tail, tail=None)
                root.insert(idx + 1, t)
        return list(root)

    @classmethod
    def textToPara(cls, text):
        return cls.fromstring(text)

    @classmethod
    def getChildren(cls, node):
        return node.getchildren()

    @classmethod
    def getElementsByTags(cls, node, tags):
        selector = 'descendant::*[%s]' % (
            ' or '.join('self::%s' % tag for tag in tags))
        elems = node.xpath(selector)
        return elems

    @classmethod
    def createElement(cls, tag='p', text=None, tail=None):
        t = lxml.html.HtmlElement()
        t.tag = tag
        t.text = text
        t.tail = tail
        return t

    @classmethod
    def getComments(cls, node):
        return node.xpath('//comment()')

    @classmethod
    def getParent(cls, node):
        return node.getparent()

    @classmethod
    def remove(cls, node):
        parent = node.getparent()
        if parent is not None:
            if node.tail:
                prev = node.getprevious()
                if prev is None:
                    if not parent.text:
                        parent.text = ''
                    parent.text += ' ' + node.tail
                else:
                    if not prev.tail:
                        prev.tail = ''
                    prev.tail += ' ' + node.tail
            node.clear()
            parent.remove(node)

    @classmethod
    def getTag(cls, node):
        return node.tag

    @classmethod
    def getText(cls, node):
        txts = [i for i in node.itertext()]
        return text.innerTrim(' '.join(txts).strip())

    @classmethod
    def previousSiblings(cls, node):
        """
            returns preceding siblings in reverse order (nearest sibling is first)
        """
        return [n for n in node.itersiblings(preceding=True)]

    @classmethod
    def previousSibling(cls, node):
        return node.getprevious()

    @classmethod
    def nextSibling(cls, node):
        return node.getnext()

    @classmethod
    def isTextNode(cls, node):
        return True if node.tag == 'text' else False

    @classmethod
    def getAttribute(cls, node, attr=None):
        if attr:
            attr = node.attrib.get(attr, None)
        if attr:
            attr = unescape(attr)
        return attr

    @classmethod
    def delAttribute(cls, node, attr=None):
        if attr:
            _attr = node.attrib.get(attr, None)
            if _attr:
                del node.attrib[attr]

    @classmethod
    def setAttribute(cls, node, attr=None, value=None):
        if attr and value:
            node.set(attr, value)

    @classmethod
    def outerHtml(cls, node):
        e0 = node
        if e0.tail:
            e0 = deepcopy(e0)
            e0.tail = None
        return cls.nodeToString(e0)
