# -*- coding: utf-8 -*-
"""\
This is a python port of "Goose" orignialy licensed to Gravity.com
under one or more contributor license agreements.  See the NOTICE file
distributed with this work for additional information
regarding copyright ownership.

Python port was written by Xavier Grangier for Recrutae

Gravity.com licenses this file
to you under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance
with the License.  You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
import lxml.html
from lxml.html import soupparser
from lxml import etree
from copy import deepcopy
from .text import innerTrim
from .text import encodeValue


class Parser(object):

    @classmethod
    def xpath_re(self, node, expression):
        regexp_namespace = "http://exslt.org/regular-expressions"
        items = node.xpath(expression, namespaces={'re': regexp_namespace})
        return items

    @classmethod
    def drop_tag(self, nodes):
        if isinstance(nodes, list):
            for node in nodes:
                node.drop_tag()
        else:
            nodes.drop_tag()

    @classmethod
    def css_select(self, node, selector):
        return node.cssselect(selector)

    @classmethod
    def fromstring(self, html):
        html = encodeValue(html)
        self.doc = lxml.html.fromstring(html)
        return self.doc

    @classmethod
    def nodeToString(self, node):
        return etree.tostring(node)

    @classmethod
    def replaceTag(self, node, tag):
        node.tag = tag

    @classmethod
    def stripTags(self, node, *tags):
        etree.strip_tags(node, *tags)

    @classmethod
    def getElementById(self, node, idd):
        selector = '//*[@id="%s"]' % idd
        elems = node.xpath(selector)
        if elems:
            return elems[0]
        return None

    @classmethod
    def getElementsByTag(self, node, tag=None, attr=None, value=None, childs=False):
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
    def appendChild(self, node, child):
        node.append(child)

    @classmethod
    def childNodes(self, node):
        return list(node)

    @classmethod
    def childNodesWithText(self, node):
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
                t = self.createElement(tag='text', text=n.tail, tail=None)
                root.insert(idx + 1, t)
        return list(root)

    @classmethod
    def textToPara(self, text):
        return self.fromstring(text)

    @classmethod
    def getChildren(self, node):
        return node.getchildren()

    @classmethod
    def getElementsByTags(self, node, tags):
        selector = ','.join(tags)
        elems = self.css_select(node, selector)
        # remove the root node
        # if we have a selection tag
        if node in elems:
            elems.remove(node)
        return elems

    @classmethod
    def createElement(self, tag='p', text=None, tail=None):
        t = lxml.html.HtmlElement()
        t.tag = tag
        t.text = text
        t.tail = tail
        return t

    @classmethod
    def getComments(self, node):
        return node.xpath('//comment()')

    @classmethod
    def getParent(self, node):
        return node.getparent()

    @classmethod
    def remove(self, node):
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
    def getTag(self, node):
        return node.tag

    @classmethod
    def getText(self, node):
        txts = [i for i in node.itertext()]
        return innerTrim(u' '.join(txts).strip())

    @classmethod
    def previousSiblings(self, node):
        nodes = []
        for c, n in enumerate(node.itersiblings(preceding=True)):
            nodes.append(n)
        return nodes

    @classmethod
    def previousSibling(self, node):
        nodes = []
        for c, n in enumerate(node.itersiblings(preceding=True)):
            nodes.append(n)
            if c == 0:
                break
        return nodes[0] if nodes else None

    @classmethod
    def nextSibling(self, node):
        nodes = []
        for c, n in enumerate(node.itersiblings(preceding=False)):
            nodes.append(n)
            if c == 0:
                break
        return nodes[0] if nodes else None

    @classmethod
    def isTextNode(self, node):
        return True if node.tag == 'text' else False

    @classmethod
    def getAttribute(self, node, attr=None):
        if attr:
            return node.attrib.get(attr, None)
        return attr

    @classmethod
    def delAttribute(self, node, attr=None):
        if attr:
            _attr = node.attrib.get(attr, None)
            if _attr:
                del node.attrib[attr]

    @classmethod
    def setAttribute(self, node, attr=None, value=None):
        if attr and value:
            node.set(attr, value)

    @classmethod
    def outerHtml(self, node):
        e0 = node
        if e0.tail:
            e0 = deepcopy(e0)
            e0.tail = None
        return self.nodeToString(e0)


class ParserSoup(Parser):
    @classmethod
    def fromstring(self, html):
        html = encodeValue(html)
        self.doc = soupparser.fromstring(html)
        return self.doc

