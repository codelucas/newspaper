# -*- coding: utf-8 -*-
"""
Newspaper treats urls for news articles as critical components.
Hence, we have an entire module dedicated to them.
"""
__title__ = 'newspaper'
__author__ = 'Lucas Ou-Yang'
__license__ = 'MIT'
__copyright__ = 'Copyright 2014, Lucas Ou-Yang'

import logging
import os
import re

from urllib.parse import parse_qs, urljoin, urlparse, urlsplit, urlunsplit

from tldextract import tldextract

log = logging.getLogger(__name__)

MAX_FILE_MEMO = 20000

# Positive lookbehind assertion: date string must be preceded by
# [^a-zA_Z0-9], any nonword character.  Make sure we aren't picking
# up portions of gibberish numbers that may look like dates
_STRICT_DATE_REGEX_PREFIX = r'(?<=\W)'

# ISO 8601 dates with a bit of flexibility & ambiguity:
# - YYYYsXXsXX, YYYYsMM
# - Sep, as denoted `s` above, is optional and may be hyphen, period,
#   fwd slash, or underscore

_SEPS = r'([-./_]?)'  # No need to escape leading hyphen, see docs.
_DAY = r'(3[01]|0[1-9]|[12][0-9])'  # 01 thru 31
_MONTH = r'(1[0-2]|0[1-9]|[A-Za-z]{3}(?![a-zA-Z]))'  # 01 thru 12 or 3-5 alpha
_YEAR = r'((?:19|20)\d{2})'  # 4 digit year, 1900 thru 2099
DATE_REGEX = _YEAR + _SEPS + r'(?:' + _DAY + r'\2' + _MONTH + r'|' + _MONTH + r'(?:\2(3[01]|0[1-9]|[12][0-9]))?' + r')'
STRICT_DATE_REGEX = _STRICT_DATE_REGEX_PREFIX + DATE_REGEX

ALLOWED_TYPES = {'html', 'htm', 'md', 'rst', 'aspx', 'jsp', 'rhtml', 'cgi',
                 'xhtml', 'jhtml', 'asp', 'shtml'}

GOOD_PATHS = {'story', 'article', 'feature', 'featured', 'slides',
              'slideshow', 'gallery', 'news', 'video', 'media',
              'v', 'radio', 'press'}

BAD_CHUNKS = {'careers', 'contact', 'about', 'faq', 'terms', 'privacy',
              'advert', 'preferences', 'feedback', 'info', 'browse', 'howto',
              'account', 'subscribe', 'donate', 'shop', 'admin'}

BAD_DOMAINS = {'amazon', 'doubleclick', 'twitter'}

ALLOWED_SCHEMES = {'http', 'https'}


def remove_args(url, keep_params=(), frags=False):
    """
    Remove all param arguments from a url.
    """
    parsed = urlsplit(url)
    filtered_query = '&'.join(
        qry_item for qry_item in parsed.query.split('&')
        if qry_item.startswith(keep_params)
    )
    if frags:
        frag = parsed[4:]
    else:
        frag = ('',)

    return urlunsplit(parsed[:3] + (filtered_query,) + frag)


def redirect_back(url, source_domain):
    """
    Some sites like Pinterest have api's that cause news
    args to direct to their site with the real news url as a
    GET param. This method catches that and returns our param.
    """
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
    """
    Operations that purify a url, removes arguments,
    redirects, and merges relatives with absolutes.
    """
    try:
        if source_url is not None:
            source_domain = urlparse(source_url).netloc
            proper_url = urljoin(source_url, url)
            proper_url = redirect_back(proper_url, source_domain)
            # proper_url = remove_args(proper_url)
        else:
            # proper_url = remove_args(url)
            proper_url = url
    except ValueError as e:
        log.critical('url %s failed on err %s' % (url, str(e)))
        proper_url = ''

    return proper_url


def valid_url(url, verbose=False, test=False):
    r"""
    Is this URL a valid news-article URL?  Judge using a few heuristics.

    1. Check the truthiness of the URL and its minimum length.
    2. Confirm its scheme is http or https
    3. Confirm the URL doesn't represent some "file-like" resource
    4. Search for a loose ISO-8601-like date in the URL.  News sites
       love to use this pattern; this is a safe bet.  See DATE_REGEX
       from the urls.py module.  Separators can be { - . / _ }.  Months
       and days may be ambiguous, with days optional.
    5. Check against good and bad domains and chunks of the URL's path,
       aggressively filtering out (or validating) matches in either
       direction.
    """
    # If we are testing this method in the testing suite, we actually
    # need to preprocess the url like we do in the article's constructor!
    if test:
        url = prepare_url(url)

    # 11 chars is shortest valid url length, eg: http://x.co
    if url is None or len(url) < 11:
        if verbose: print('\t%s rejected because len of url is less than 11' % url)
        return False

    _parseresult = urlparse(url)
    if _parseresult.scheme not in ALLOWED_SCHEMES:
        if verbose: print('\t%s rejected because it lacks normal scheme' % url)
        return False

    path = _parseresult.path

    # input url is not in valid form (scheme, netloc, tld)
    if not path.startswith('/'):
        return False

    # the '/' which may exist at the end of the url provides us no information
    if path.endswith('/'):
        path = path[:-1]

    # '/story/cnn/blahblah/index.html' --> ['story', 'cnn', 'blahblah', 'index.html']
    path_chunks = [x for x in path.split('/') if len(x) > 0]

    # siphon out the file type. eg: .html, .htm, .md
    if len(path_chunks) > 0:
        file_type = url_to_filetype(url)

        # if the file type is a media type, reject instantly
        if file_type and file_type not in ALLOWED_TYPES:
            if verbose: print('\t%s rejected due to bad filetype' % url)
            return False

        last_chunk = path_chunks[-1].split('.')
        # the file type is not of use to use anymore, remove from url
        if len(last_chunk) > 1:
            path_chunks[-1] = last_chunk[-2]

    # Index gives us no information
    if 'index' in path_chunks:
        path_chunks.remove('index')

    # extract the tld (top level domain)
    tld_dat = tldextract.extract(url)
    subd = tld_dat.subdomain
    tld = tld_dat.domain.lower()

    url_slug = path_chunks[-1] if path_chunks else ''

    if tld in BAD_DOMAINS:
        if verbose: print('%s caught for a bad tld' % url)
        return False

    if len(path_chunks) == 0:
        dash_count, underscore_count = 0, 0
    else:
        dash_count = url_slug.count('-')
        underscore_count = url_slug.count('_')

    # If the url has a news slug title
    if url_slug and (dash_count > 4 or underscore_count > 4):

        if dash_count >= underscore_count:
            if tld not in [x.lower() for x in url_slug.split('-')]:
                if verbose: print('%s verified for being a slug' % url)
                return True

        if underscore_count > dash_count:
            if tld not in [x.lower() for x in url_slug.split('_')]:
                if verbose: print('%s verified for being a slug' % url)
                return True

    # There must be at least 2 subpaths
    if len(path_chunks) <= 1:
        if verbose: print('%s caught for path chunks too small' % url)
        return False

    lower_chunks = {p.lower() for p in path_chunks}

    # Check for subdomain & path red flags
    # Eg: http://cnn.com/careers.html or careers.cnn.com --> BAD
    found_bad = BAD_CHUNKS.intersection(lower_chunks)
    if found_bad:
        if verbose:
            for b in found_bad:
                print('%s caught for bad chunks' % url)
        return False
    if subd in BAD_CHUNKS:
        if verbose: print('%s caught for bad chunks' % url)
        return False

    match_date = re.search(DATE_REGEX, url)

    # if we caught the verified date above, it's an article
    if match_date is not None:
        if verbose: print('%s verified for date' % url)
        return True

    found_good = GOOD_PATHS.intersection(lower_chunks)
    if found_good:
        if verbose:
            for g in found_good:
                print('%s verified for good path' % url)
        return True

    if verbose: print('%s caught for default false' % url)
    return False


def url_to_filetype(abs_url, max_len_allowed=5):
    """
    Extract filetype from file identified by the input URL.

    Returns None for no detected filetype.

    Strips leading dot on the file type.

    'http://blahblah/images/car.jpg' -> 'jpg'
    'http://yahoo.com'               -> None
    'https://www.python.org/ftp/python/3.7.2/Python-3.7.2.tar.xz' -> 'xz'
    """

    # Eliminate the trailing '/'; we are extracting the file
    path = urlparse(abs_url).path.rstrip('/')
    if not path:
        return None
    _, file_type = os.path.splitext(path.rsplit('/')[-1])
    if file_type and len(file_type) <= max_len_allowed:
        return file_type.lower().strip('.')
    return None


def get_domain(abs_url, **kwargs):
    """
    returns a url's domain, this method exists to
    encapsulate all url code into this file
    """
    if abs_url is None:
        return None
    return urlparse(abs_url, **kwargs).netloc


def get_scheme(abs_url, **kwargs):
    """
    """
    if abs_url is None:
        return None
    return urlparse(abs_url, **kwargs).scheme


def get_path(abs_url, **kwargs):
    """
    """
    if abs_url is None:
        return None
    return urlparse(abs_url, **kwargs).path


def is_abs_url(url):
    """
    Return True if `url` is absolute path and http[s] scheme, False otherwise.
    """

    # Note: This regex was brought to you by Django!
    # Django's URLValidator has been updated dramatically over time;
    # see django.core.validators.
    #
    # Note also that though "//www.python.org" is, from RFC 3986's
    # perspective, an absolute URL, it is not valid by this definition.
    regex = re.compile(
        r'^(?:http|ftp)s?://'                                                                 # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
        r'localhost|'                                                                         # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|'                                                # ...or ipv4
        r'\[?[A-F0-9]*:[A-F0-9:]+\]?)'                                                        # ...or ipv6
        r'(?::\d+)?'                                                                          # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)

    return bool(c_regex.search(url))
