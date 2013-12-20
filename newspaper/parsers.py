# -*- coding: utf-8 -*-

import re
import logging
import urlparse

import lxml.html
import lxml.html.soupparser

from .urls import (
    prepare_url, get_path, get_domain, get_scheme)
from .packages.tldextract import tldextract
from .packages.goose import Goose

log = logging.getLogger(__name__)

MIN_WORD_COUNT = 100
MIN_SENT_COUNT = 3

# try:
#     lxml_root = lxml_wrapper(html)
# except Exception, e:
#     log.debug('urls html lxml failed out %s' % e)
#     try:
#         lxml_root = soup_wrapper(html)
#     except Exception, e:
#         log.debug('urls soup lxml failed out %s' % e)
#         return []

# Wrappers exist in case we need to add decorator methods.

def lxml_wrapper(html):
    return lxml.html.fromstring(html)

def soup_wrapper(html):
    return lxml.html.soupparser.fromstring(html)

def get_lxml_root(html):
    """takes html returns lxml root"""

    if html is None:
        return None
    try:
        return lxml_wrapper(html)
    except Exception, e:
        log.critical(e)
        return None

def lxml_to_urls(lxml_root, titles):
    """converts an lxml root into urls, may include <a> text as titles"""

    if lxml_root is None:
        return []

    a_tags = lxml_root.xpath('//a')
    if titles: # tries to find titles of link elements via tag text
        return [ (a.get('href'), a.text) for a in a_tags if a.get('href') ]

    return [ a.get('href') for a in a_tags if a.get('href') ]

def get_urls(_input, titles=False, regex=False):
    """returns a list of urls on the html page or lxml_root the regex
    flag indicates we don't parse via lxml and just search the html"""

    if _input is None:
        log.critical('Must extract urls from either html, text or lxml_root!')
        return []

    # If we are extracting from raw text
    if regex:
        _input = re.sub('<[^<]+?>', ' ', _input)
        _input = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', _input)
        _input = [i.strip() for i in _input]
        return _input or []

    # If the input is html, parse it into a root
    if isinstance(_input, str) or isinstance(_input, unicode):
        lxml_root = get_lxml_root(_input)
    else:
        lxml_root = _input

    return lxml_to_urls(lxml_root, titles)

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

    if og_art == 'article' and wordcount > (MIN_WORD_COUNT - 50):
        log.debug('%s verified for article and wc' % article.url)
        return True

    if not article.is_media_news() and not article.text:
        log.debug('%s caught for no media no text' % article.url)
        return False

    if article.title is None or len(article.title.split(' ')) < 2:
        log.debug('%s caught for bad title' % article.url)
        return False

    if len(wordcount) < MIN_WORD_COUNT:
        log.debug('%s caught for word cnt' % article.url)
        return False

    if len(sentcount) < MIN_SENT_COUNT:
        log.debug('%s caught for sent cnt' % article.url)
        return False

    if article.html is None or article.html == u'':
        log.debug('%s caught for no html' % article.url)
        return False

    log.debug('%s verified for default true' % article.url)
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
    # Otherwise, lxml
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
        img_links = [ urlparse.urljoin(article.url, url)
                for url in article.lxml_root.xpath('//img/@src') ]
        return img_links

def get_feed_urls(source):
    """
    Requires: List of category lxml roots, two types of anchors: categories
    and feeds (rss). we extract category urls first and then feeds
    """

    feed_urls = []
    for category in source.categories:
        root = category.lxml_root
        feed_urls.extend(root.xpath('//*[@type="application/rss+xml"]/@href'))

    feed_urls = feed_urls[:50]
    feed_urls = [ prepare_url(f, source.url) for f in feed_urls ]

    feeds = list(set(feed_urls))
    return feeds

# extra source_url and source_urls methods are for testing
def get_category_urls(source, source_url=None, page_urls=None):
    """
    REQUIRES: source lxml root and source url takes a domain and finds all of the
    top level urls, we are assuming that these are the category urls

    cnn.com --> [cnn.com/latest, world.cnn.com, cnn.com/asia]
    """

    source_url = source.url if source_url is None else source_url
    page_urls = get_urls(source.lxml_root) if page_urls is None else page_urls

    valid_categories = []
    for p_url in page_urls:
        scheme = get_scheme(p_url, allow_fragments=False)
        domain = get_domain(p_url, allow_fragments=False)
        path = get_path(p_url, allow_fragments=False)

        if not domain and not path:
            continue
        if path and '#' in path:
            continue
        if scheme and (scheme!='http' and scheme!='https'):
            continue

        if domain:
            child_tld = tldextract.extract(p_url)
            domain_tld = tldextract.extract(source_url)

            if child_tld.domain != domain_tld.domain:
                continue
            elif child_tld.subdomain in ['m', 'i']:
                continue
            else:
                valid_categories.append(scheme+'://'+domain)
        else:
            # we want a path with just one subdir
            # cnn.com/world and cnn.com/world/ are both valid_categories
            path_chunks = [ x for x in path.split('/') if len(x) > 0 ]

            if 'index.html' in path_chunks:
                path_chunks.remove('index.html')

            if len(path_chunks) == 1 and len(path_chunks[0]) < 14:
                valid_categories.append(domain+path)

    stopwords = [
        'about', 'help', 'privacy', 'legal', 'feedback', 'sitemap',
        'profile', 'account', 'mobile', 'sitemap', 'facebook', 'myspace',
        'twitter', 'linkedin', 'bebo', 'friendster', 'stumbleupon', 'youtube',
        'vimeo', 'store', 'mail', 'preferences', 'maps', 'password', 'imgur',
        'flickr', 'search', 'subscription', 'itunes', 'siteindex', 'events',
        'stop', 'jobs', 'careers', 'newsletter', 'subscribe', 'academy',
        'shopping', 'purchase', 'site-map', 'shop', 'donate', 'newsletter',
        'product', 'advert', 'info', 'tickets', 'coupons', 'forum', 'board',
        'archive', 'browse', 'howto', 'how to', 'faq', 'terms', 'charts',
        'services', 'contact', 'plus', 'admin', 'login', 'signup', 'register']

    _valid_categories = []

    # TODO Stop spamming urlparse and tldextract calls...

    for p_url in valid_categories:
        path = get_path(p_url)
        subdomain = tldextract.extract(p_url).subdomain
        conjunction = path + ' ' + subdomain
        bad = False
        for badword in stopwords:
            if badword.lower() in conjunction.lower():
                bad=True
                break
        if not bad:
            _valid_categories.append(p_url)

    _valid_categories.append('/') # add the root!

    for i, p_url in enumerate(_valid_categories):
        if p_url.startswith('://') :
            p_url = 'http' + p_url
            _valid_categories[i] = p_url

        elif p_url.startswith('//'):
            p_url = 'http:' + p_url
            _valid_categories[i] = p_url

        if p_url.endswith('/'):
            p_url = p_url[:-1]
            _valid_categories[i] = p_url

    _valid_categories = list(set(_valid_categories))

    category_urls = [prepare_url(p_url, source_url) for p_url in _valid_categories]
    category_urls = [c for c in category_urls if c is not None]
    return category_urls

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
