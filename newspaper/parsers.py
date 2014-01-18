# -*- coding: utf-8 -*-
"""
Parser objects will only contain operations that manipulate
or query an lxml or soup dom object generated from an article's html.
"""
import re
import logging

import lxml.html
from lxml.html import soupparser
from lxml.html.clean import Cleaner
from lxml import etree

from copy import deepcopy
from .text import innerTrim
from .utils import encodeValue

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
    def root_to_urls(cls, doc, titles):
        """
        Return a list of urls from an lxml root.
        """
        if doc is None:
            return []

        a_tags = doc.xpath('//a')
        # tries to find titles of link elements via tag text
        if titles:
            return [ (a.get('href'), a.text) for a in a_tags if a.get('href') ]

        return [ a.get('href') for a in a_tags if a.get('href') ]

    @classmethod
    def get_urls(cls, _input, titles=False, regex=False):
        """
        Inputs html page or doc and returns list of urls, the regex
        flag indicates we don't parse via lxml and just search the html.
        """
        if _input is None:
            log.critical('Must extract urls from either html, text or doc!')
            return []

        # If we are extracting from raw text
        if regex:
            _input = re.sub('<[^<]+?>', ' ', _input)
            _input = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', _input)
            _input = [i.strip() for i in _input]
            return _input or []

        # If the input is html, parse it into a root
        if isinstance(_input, str) or isinstance(_input, unicode):
            doc = cls.fromstring(_input)
        else:
            doc = _input

        return cls.root_to_urls(doc, titles)

    @classmethod
    def get_top_img_url(cls, doc):
        """
        Takes an lxml doc and returns the top img url
        running as method == 'soup' assumes lxml's soupparser.
        """
        try:
            return doc.xpath('/html/head/meta[@property="og:image"][1]/@content')[0]
        except:
            pass
        try:
            return doc.xpath('/html/head/link[@rel="icon"][1]/@href')[0]
        except:
            pass
        try:
            return doc.xpath('/html/head/link[@rel="img_src"][1]/@href')[0]
        except:
            pass
        try:
            return doc.xpath('/html/head/meta[@name="og:image"][1]/@content')[0]
        except:
            pass
        return None

    @classmethod
    def get_img_urls(cls, doc):
        """
        Return all of the images on an html page, lxml root.
        """
        try:
            img_links = doc.xpath('//img/@src')
        except Exception, e:
            print str(e)
            log.critical(e)
            return []

        return img_links

    @classmethod
    def get_feed_urls(cls, doc):
        """
        Returns list of feed urls on an lxml root.
        """
        try:
            return doc.xpath('//*[@type="application/rss+xml"]/@href')
        except Exception, e:
            print str(e)
            log.critical(e)
            return []

    @classmethod
    def get_meta_type(cls, doc):
        """
        Returns the meta "type" of an article.
        """
        try:
            return doc.xpath('/html/head/meta[@property="og:type"][1]/@content')[0]
        except Exception, e:
            print str(e)
            log.critical(e)
            return u''

    @classmethod
    def css_select(cls, node, selector):
        return node.cssselect(selector)

    @classmethod
    def fromstring(cls, html):
        html = encodeValue(html)
        try:
            cls.doc = lxml.html.fromstring(html)
        except Exception, e:
            print '[Parse lxml ERR]', str(e)
            return None

        return cls.doc

    # @classmethod
    # def set_doc(cls, html):
    #    cls.doc = cls.fromstring(html)

    @classmethod
    def node_to_string(cls, node):
        return lxml.html.tostring(node)

    @classmethod
    def clean_article_html(cls, node):
        article_cleaner = Cleaner()
        article_cleaner.javascript = True
        article_cleaner.style = True
        article_cleaner.allow_tags = ['a', 'span', 'p', 'br', 'strong', 'b', 'em']
        article_cleaner.remove_unknown_tags = False
        return article_cleaner.clean_html(node)

    @classmethod
    def nodeToString(cls, node):
        return etree.tostring(node)

    @classmethod
    def replaceTag(cls, node, tag):
        node.tag = tag

    @classmethod
    def stripTags(cls, node, *tags):
        etree.strip_tags(node, *tags)

    @classmethod
    def getElementById(cls, node, idd):
        selector = '//*[@id="%s"]' % idd
        elems = node.xpath(selector)
        if elems:
            return elems[0]
        return None

    @classmethod
    def getElementsByTag(cls, node, tag=None, attr=None, value=None, childs=False):
        NS = "http://exslt.org/regular-expressions"
        # selector = tag or '*'
        selector = 'descendant-or-self::%s' % (tag or '*')
        if attr and value:
            selector = '%s[re:test(@%s, "%s", "i")]' % (selector, attr, value)
        elems = node.xpath(selector, namespaces={"re": NS})
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
        selector = ','.join(tags)
        elems = cls.css_select(node, selector)
        # remove the root node
        # if we have a selection tag
        if node in elems:
            elems.remove(node)
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
                    parent.text += u' ' + node.tail
                else:
                    if not prev.tail:
                        prev.tail = ''
                    prev.tail += u' ' + node.tail
            node.clear()
            parent.remove(node)

    @classmethod
    def getTag(cls, node):
        return node.tag

    @classmethod
    def getText(cls, node):
        txts = [i for i in node.itertext()]
        return innerTrim(u' '.join(txts).strip())

    @classmethod
    def previousSiblings(cls, node):
        nodes = []
        for c, n in enumerate(node.itersiblings(preceding=True)):
            nodes.append(n)
        return nodes

    @classmethod
    def previousSibling(cls, node):
        nodes = []
        for c, n in enumerate(node.itersiblings(preceding=True)):
            nodes.append(n)
            if c == 0:
                break
        return nodes[0] if nodes else None

    @classmethod
    def nextSibling(cls, node):
        nodes = []
        for c, n in enumerate(node.itersiblings(preceding=False)):
            nodes.append(n)
            if c == 0:
                break
        return nodes[0] if nodes else None

    @classmethod
    def isTextNode(cls, node):
        return True if node.tag == 'text' else False

    @classmethod
    def getAttribute(cls, node, attr=None):
        if attr:
            return node.attrib.get(attr, None)
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


class ParserSoup(Parser):
    @classmethod
    def fromstring(cls, html):
        html = encodeValue(html)
        cls.doc = soupparser.fromstring(html)
        return cls.doc

