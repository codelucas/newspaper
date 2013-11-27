# -*- coding: utf-8 -*-

import logging
import urlparse

import lxml.html
import lxml.html.soupparser
from goose import Goose

from .urls import prepare_url, get_path, get_domain, get_scheme
from .packages.tldextract import tldextract

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
    return lxml_wrapper(html)

def get_urls(root_or_html, titles=True):
    """returns a list of urls on the html page or lxml_root"""

    if root_or_html is None:
        log.critical('Must extract urls from either html or lxml_root!')
        return []

    # If the input is html, parse it into a root
    if isinstance(root_or_html, str) or isinstance(root_or_html, unicode):
        lxml_root = lxml_wrapper(root_or_html)
    else:
        lxml_root = root_or_html

    a_tags = lxml_root.xpath('//a')
    if titles: # tries to find titles of link elements via tag text
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

def get_feed_urls(source):
    """REQUIRES: List of category lxml roots.
    two types of anchors, categories and feeds (rss)
    we extract category urls first and then feeds"""

    feed_urls = []
    for category_obj in source.obj_categories:
        root = category_obj[2]
        feed_urls.extend(root.xpath('//*[@type="application/rss+xml"]/@href'))

    feed_urls = feed_urls[:50]
    feed_urls = [ prepare_url(f, source.url) for f in feed_urls ]

    feeds = list(set(feed_urls))
    source.feed_urls = feeds

def get_category_urls(source):
    """REQUIRES: valid lxml root.
    takes a domain and finds all of the top level
    urls, we are assuming that these are the category urls

    cnn.com --> [cnn.com/latest, world.cnn.com, cnn.com/asia]
    """

    urls = get_urls(source.lxml_root, titles=False)
    valid_categories = []
    for url in urls:
        scheme = get_scheme(url, allow_fragments=False)
        domain = get_domain(url, allow_fragments=False)
        path = get_path(url, allow_fragments=False)

        if not domain and not path:
            continue
        if path and '#' in path:
            continue
        if scheme and (scheme!='http' and scheme!='https'):
            continue

        if domain:
            child_tld = tldextract.extract(url)
            domain_tld = tldextract.extract(source.url)

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

    for url in valid_categories:
        path = get_path(url)
        subdomain = tldextract.extract(url).subdomain
        conjunction = path + ' ' + subdomain
        bad=False
        for badword in stopwords:
            if badword.lower() in conjunction.lower():
                bad=True
                break
        if not bad:
            _valid_categories.append(url)

    _valid_categories.append('/') # add the root!

    for i, url in enumerate(_valid_categories):
        if url.startswith('://') :
            url = 'http' + url
            _valid_categories[i] = url

        elif url.startswith('//'):
            url = 'http:' + url
            _valid_categories[i] = url

        if url.endswith('/'):
            url = url[:-1]
            _valid_categories[i] = url

    _valid_categories = list(set(_valid_categories))

    categories = [prepare_url(url, source.url) for url in _valid_categories]
    source.category_urls = categories

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
