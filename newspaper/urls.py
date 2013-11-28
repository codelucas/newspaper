# -*- coding: utf-8 -*-

import logging
import re

from .packages.tldextract import tldextract

from urlparse import (
    urlparse, urljoin, urlsplit, urlunsplit, parse_qs)

log = logging.getLogger(__name__)

MAX_FILE_MEMO = 20000

good_paths = ['story', 'article', 'feature', 'featured', 'slides',
              'slideshow', 'gallery', 'news', 'video', 'media',
              'v', 'radio', 'press']

bad_chunks = ['careers', 'contact', 'about', 'faq', 'terms', 'privacy',
              'advert', 'preferences', 'feedback', 'info', 'browse', 'howto',
              'account', 'subscribe', 'donate', 'shop', 'admin']

bad_domains = ['amazon', 'doubleclick', 'twitter']

def remove_args(url, keep_params=(), frags=False):
    """remove all param arguments from a url"""

    parsed = urlsplit(url)
    filtered_query= '&'.join(
        qry_item for qry_item in parsed.query.split('&')
            if qry_item.startswith(keep_params)
    )
    if frags:
        frag = parsed[4:]
    else:
        frag = ('',)

    return urlunsplit(parsed[:3] + (filtered_query,) + frag)

def redirect_back(url, source_domain):
    """some sites like pinterest have api's that cause news
    orgs to direct to their site with the real news url as a
    GET param. This method catches that and returns our param."""

    parse_data = urlparse(url)
    domain = parse_data.netloc
    query = parse_data.query

    # If our url is even from a remotely similar domain or
    # sub domain, we don't need to redirect.
    if source_domain in domain or domain in source_domain:
        return url

    query_item = parse_qs(query)
    if query_item.get('url'):
        # log.debug('caught redirect %s into %s' % (url, query_item['url'][0]))
        return query_item['url'][0]

    return url

def prepare_url(url, source_url=None):
    """operations that purify a url, removes arguments,
    redirects, and merges relatives with absolutes"""

    if source_url is not None:
        source_domain = urlparse(source_url).netloc
        proper_url = urljoin(source_url, url)
        proper_url = redirect_back(proper_url, source_domain)
        proper_url = remove_args(proper_url)
    else:
        proper_url = remove_args(url)

    return proper_url

def valid_url(url, verbose=False):
    """Perform a regex check on a full url (scheme, domain, tld).
    First search of a YYYY/MM/DD pattern in the url. News sites
    love to use this pattern, this is a very safe bet.

    Separators can be [\.-/_]. Years can be 2 or 4 digits, must
    have proper digits 1900-2099. Months and days can be
    ambiguous 2 digit numbers, one is even optional, some sites are
    liberal with their formatting also matches snippets of GET
    queries with keywords inside them. ex: asdf.php?topic_id=blahlbah
    We permit alphanumeric, _ and -.

    Our next check makes sure that a keyword is within one of the
    separators in a url. cnn.com/story/blah-blah-blah is a given.

    We filter out articles in this stage by aggressively checking to
    see if any resemblance of the source& domain's name or tld is
    present within the article title. If it is, that's bad. It must
    be a company link, like 'cnn is hiring new interns'.

    We also filter out articles with a subdomain or first degree path
    on a registered bad keyword"""

    # 11 chars is shortest valid url length, eg: http://x.co
    if url is None or len(url) < 11:
        return False

    if 'mailto:' in url:
        return False

    path = urlparse(url).path

    # input url is not in valid form (scheme, netloc, tld)
    if not path.startswith('/'):
        return False

    if path.endswith('/'):
        path = path[:-1]

    date_re = r'([\./\-_]{0,1}(19|20)\d{2})[\./\-_]{0,1}(([0-3]{0,1}[0-9][\./\-_])|(\w{3,5}[\./\-_]))([0-3]{0,1}[0-9][\./\-]{0,1})?'
    match_date = re.search(date_re, url)

    path_chunks = [ x for x in path.split('/') if len(x) > 0 ]

    # siphon out the file type. eg: .html, .htm, .md
    if len(path_chunks) > 0:
        last_chunk = path_chunks[-1].split('.')

        # set the ending file to the file minus file type
        if len(last_chunk) > 1:
            path_chunks[-1] = last_chunk[:-1]

    # Index gives us no information
    if 'index' in path_chunks:
        path_chunks.remove('index')

    # extract the tld (top level domain)
    tld_dat = tldextract.extract(url)
    subd = tld_dat.subdomain
    tld = tld_dat.domain.lower()

    if tld in bad_domains:
        # log.debug('%s caught for a bad tld' % url)
        return False

    if  len(path_chunks) == 0:
        dash_count, underscore_count = 0, 0

    else:
        dash_count = path_chunks[-1].count('-')
        underscore_count = path_chunks[-1].count('_')

    # If the url has a news slug title
    if path_chunks and len(path_chunks[-1]) > 20 and \
        (dash_count > 5 or underscore_count > 5):

        if dash_count >= underscore_count:
            if tld not in [ x.lower() for x in path_chunks[-1].split('-') ]:
                # log.debug('%s verified for being a slug' % url)
                return True

        if underscore_count > dash_count:
            if tld not in [ x.lower() for x in path_chunks[-1].split('_') ]:
                # log.debug('%s verified for being a slug' % url)
                return True

    # There must be at least 2 subpaths
    if len(path_chunks) <= 1:
        # log.debug('%s caught for path chunks too small' % url)
        return False

    # Check for subdomain & path red flags
    # Eg: http://cnn.com/careers.html or careers.cnn.com --> BAD
    for b in bad_chunks:
        if b in path_chunks or b == subd:
            # log.debug('%s caught for bad chunks' % url)
            return False

    if match_date is not None:
        # log.debug('%s verified for date' % url)
        return True

    # log.debug('%s caught for default false' % url)
    return False

def get_domain(abs_url, **kwargs):
    """returns a url's domain, this method exists to
    encapsulate all url code into this file."""

    if abs_url is None:
        return None
    return urlparse(abs_url, **kwargs).netloc

def get_scheme(abs_url, **kwargs):
    """"""

    if abs_url is None:
        return None
    return urlparse(abs_url, **kwargs).scheme

def get_path(abs_url, **kwargs):
    """"""

    if abs_url is None:
        return None
    return urlparse(abs_url, **kwargs).path
