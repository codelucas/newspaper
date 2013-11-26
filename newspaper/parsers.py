# -*- coding: utf-8 -*-

import logging

import lxml.html
import lxml.html.soupparser

log = logging.getLogger(__name__)


def lxml_wrapper(html):
    return lxml.html.fromstring(html)


def soup_wrapper(html):
    return lxml.html.soupparser.fromstring(html)


def root_to_urls(lxml_root, titles=True):
    """similar to below method but takes a lxml
    html dom root to reduce recomputing roots"""

    if not lxml_root:
        return []

    atags = lxml_root.xpath('//a')
    if titles:
        return [ (a.get('href'), a.text)
                    for a in atags if a.get('href') ]

    return [ a.get('href') for a in atags if a.get('href') ]


def html_to_urls(html, titles=True):
    """takes html, uses xpath to quickly retrieve all <a> tags.
    returns tuples in the form of (url, title) title does
    not have to exist"""

    try:
        lxml_root = lxml_wrapper(html)
    except Exception, e:
        log.debug('urls html lxml failed out %s' % e)
        try:
            lxml_root = soup_wrapper(html)
        except Exception, e:
            log.debug('urls soup lxml failed out %s' % e)
            return []


    atags = lxml_root.xpath('//a')

    if titles:
        return [ (a.get('href'), a.text) for a in atags if a.get('href') ]

    return [ a.get('href') for a in atags if a.get('href') ]
