# -*- coding: utf-8 -*-

import logging
import urlparse

import lxml.html
import lxml.html.soupparser

from goose import Goose

log = logging.getLogger(__name__)

MIN_WORD_COUNT = 100
MIN_SENT_COUNT = 3


def lxml_wrapper(html):
    return lxml.html.fromstring(html)


def soup_wrapper(html):
    return lxml.html.soupparser.fromstring(html)


def get_lxml_root(article):
    """"""

    if article.html is None:
        return None
    return lxml_wrapper(article.html)


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
    returns tuples in the form of (url, title), the title does
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

    a_tags = lxml_root.xpath('//a')

    if titles:
        return [ (a.get('href'), a.text) for a in a_tags if a.get('href') ]

    return [ a.get('href') for a in a_tags if a.get('href') ]


def valid_body(article, verbose=False):
    """performs a word-count check on article, checks for
    gallery/video makes sure title length is over 2 words,
    makes sure fb og: is article"""

    try:
        og_art=article.lxml_root.xpath('/html/head/meta'
                    '[@property="og:type"][1]/@content')[0]
    except:
        og_art = ''

    wordcount = article.text.split(' ')
    sentcount = article.text.split('.')

    if og_art == 'article' and wordcount > \
            (MIN_WORD_COUNT - 50):
        #log.debug('%s verified for article and wc' % link.href)
        return True

    if not article.is_media_news() and not article.text:
        #log.debug('%s caught for no media no text' % link.href)
        return False

    if article.title is None or \
            len(article.title.split(' ')) < 2:
        #log.debug('%s caught for bad title' % link.href)
        return False

    if len(wordcount) < MIN_WORD_COUNT:
        #log.debug('%s caught for word cnt' % link.href)
        return False

    if len(sentcount) < MIN_SENT_COUNT:
        #log.debug('%s caught for sent cnt' % link.href)
        return False

    if not article.html:
        #log.debug('%s caught for no html' % link.href)
        return False

    #log.debug('%s verified for default true' % link.href)
    return True


def get_top_img(article, method='lxml'):
    """attempts to pull the top img of an article
    from 3 plausible locations"""

    root = article.lxml_root

    # analogous to lxml, but uses BeautifulSoup's root
    if method == 'soup':
        safe_img = (root.find('meta', attrs={'property':'og:image'})
                        or root.find('meta', attrs={'name':'og:image'}))
        if safe_img:
            safe_img = safe_img.get('content')

        if not safe_img:
            safe_img = (root.find('link', attrs={'rel':'img_src'})
                            or root.find('link', attrs={'rel':'icon'}))
            if safe_img:
                safe_img = safe_img.get('content')

        if not safe_img:
            safe_img = ''

        return safe_img

    # It's lxml
    try:
        return root.xpath('/html/head/meta'
                '[@property="og:image"][1]/@content')[0]
    except: pass
    try:
        return root.xpath('/html/head/link'
                '[@rel="icon"][1]/@href')[0]
    except: pass
    try:
        return root.xpath('/html/head/link'
                '[@rel="img_src"][1]/@href')[0]
    except: pass
    try:
        return root.xpath('/html/head/meta'
                '[@name="og:image"][1]/@content')[0]
    except: pass

    return None


def get_imgs(article, method='lxml'):
    """return all of the images on an html page, lxml root"""

    if method == 'soup':
        img_links = article.soup_root.findAll('img')
        img_links = [ i.get('src') for i in img_links if i.get('src')  ]
        img_links = [ urlparse.urljoin(article.href, url)
                            for url in img_links ]
        return img_links
    else:
        img_links = [ urlparse.urljoin(article.href, url)
                for url in article.lxml_root.xpath('//img/@src') ]
        return img_links


class GooseObj(object):
    """encapsulation of goose output"""

    def __init__(self, article):
        g = Goose()
        # g2 = Goose({'parser_class':'soup'})

        goose_obj = g.extract(raw_html=article.html)
        self.body_text = goose_obj.cleaned_text
        keywords = goose_obj.meta_keywords.split(',')
        self.keywords = [w.strip() for w in keywords] # not actual keyw's
        self.title = goose_obj.title
        self.authors = goose_obj.authors


