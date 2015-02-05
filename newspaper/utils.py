# -*- coding: utf-8 -*-
"""
Holds misc. utility methods which prove to be
useful throughout this library.
"""
__title__ = 'newspaper'
__author__ = 'Lucas Ou-Yang'
__license__ = 'MIT'
__copyright__ = 'Copyright 2014, Lucas Ou-Yang'

import codecs
import hashlib
import logging
import os
import pickle
import random
import re
import string
import sys
import threading
import time

from bs4 import UnicodeDammit

from hashlib import sha1

from . import settings

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


class FileHelper(object):
    @classmethod
    def loadResourceFile(self, filename):
        if not os.path.isabs(filename):
            # _PARENT_DIR = os.path.join(_TEST_DIR, '../..') # packages/goose
            # dirpath = os.path.dirname(goose.__file__)
            dirpath = os.path.abspath(os.path.dirname(__file__))
            path = os.path.join(dirpath, 'resources', filename)
        else:
            path = filename
        try:
            f = codecs.open(path, 'r', 'utf-8')
            content = f.read()
            f.close()
            return content
        except IOError:
            raise IOError("Couldn't open file %s" % path)


class ParsingCandidate(object):

    def __init__(self, urlString, link_hash):
        self.urlString = self.url = urlString
        self.link_hash = link_hash


class RawHelper(object):
    @classmethod
    def get_parsing_candidate(self, url, raw_html):
        if isinstance(raw_html, unicode):
            raw_html = raw_html.encode('utf-8')
        link_hash = '%s.%s' % (hashlib.md5(raw_html).hexdigest(), time.time())
        return ParsingCandidate(url, link_hash)


class URLHelper(object):
    @classmethod
    def get_parsing_candidate(self, url_to_crawl):
        # Replace shebang in urls
        final_url = url_to_crawl.replace('#!', '?_escaped_fragment_=') \
            if '#!' in url_to_crawl else url_to_crawl
        link_hash = '%s.%s' % (hashlib.md5(final_url).hexdigest(), time.time())
        return ParsingCandidate(final_url, link_hash)


class StringSplitter(object):
    def __init__(self, pattern):
        self.pattern = re.compile(pattern)

    def split(self, string):
        if not string:
            return []
        return self.pattern.split(string)


class StringReplacement(object):
    def __init__(self, pattern, replaceWith):
        self.pattern = pattern
        self.replaceWith = replaceWith

    def replaceAll(self, string):
        if not string:
            return u''
        return string.replace(self.pattern, self.replaceWith)


class ReplaceSequence(object):
    def __init__(self):
        self.replacements = []

    def create(self, firstPattern, replaceWith=None):
        result = StringReplacement(firstPattern, replaceWith or u'')
        self.replacements.append(result)
        return self

    def append(self, pattern, replaceWith=None):
        return self.create(pattern, replaceWith)

    def replaceAll(self, string):
        if not string:
            return u''

        mutatedString = string
        for rp in self.replacements:
            mutatedString = rp.replaceAll(mutatedString)
        return mutatedString


def get_unicode(text, is_html=False):
    if not text:
        return u''
    if isinstance(text, unicode):
        return text
    converted = UnicodeDammit(text, is_html=is_html)
    if not converted.unicode_markup:
        raise Exception(
            'Failed to detect encoding of text: "%s"...,'
            '\ntried encodings: "%s"' %
            (text[:20], ', '.join(converted.tried_encodings)))
    return converted.unicode_markup


class TimeoutError(Exception):
    pass


def timelimit(timeout):
    """Borrowed from web.py, rip Aaron Swartz
    """
    def _1(function):
        def _2(*args, **kw):
            class Dispatch(threading.Thread):
                def __init__(self):
                    threading.Thread.__init__(self)
                    self.result = None
                    self.error = None

                    self.setDaemon(True)
                    self.start()

                def run(self):
                    try:
                        self.result = function(*args, **kw)
                    except:
                        self.error = sys.exc_info()
            c = Dispatch()
            c.join(timeout)
            if c.isAlive():
                raise TimeoutError()
            if c.error:
                raise c.error[0], c.error[1]
            return c.result
        return _2
    return _1


def domain_to_filename(domain):
    """All '/' are turned into '-', no trailing. schema's
    are gone, only the raw domain + ".txt" remains
    """
    filename = domain.replace('/', '-')
    if filename[-1] == '-':
        filename = filename[:-1]
    filename += ".txt"
    return filename


def filename_to_domain(filename):
    """[:-4] for the .txt at end
    """
    return filename.replace('-', '/')[:-4]


def is_ascii(word):
    """True if a word is only ascii chars
    """
    def onlyascii(char):
        if ord(char) > 127:
            return ''
        else:
            return char
    for c in word:
        if not onlyascii(c):
            return False
    return True


def to_valid_filename(s):
    """Converts arbitrary string (for us domain name)
    into a valid file name for caching
    """
    valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
    return ''.join(c for c in s if c in valid_chars)


def cache_disk(seconds=(86400*5), cache_folder="/tmp"):
    """Caching extracting category locations & rss feeds for 5 days
    """
    def do_cache(function):
        def inner_function(*args, **kwargs):
            """Calculate a cache key based on the decorated method signature
            args[1] indicates the domain of the inputs, we hash on domain!
            """
            key = sha1(str(args[1]) + str(kwargs)).hexdigest()
            filepath = os.path.join(cache_folder, key)

            # verify that the cached object exists and is less than
            # X seconds old
            if os.path.exists(filepath):
                modified = os.path.getmtime(filepath)
                age_seconds = time.time() - modified
                if age_seconds < seconds:
                    return pickle.load(open(filepath, "rb"))

            # call the decorated function...
            result = function(*args, **kwargs)
            # ... and save the cached object for next time
            pickle.dump(result, open(filepath, "wb"))
            return result
        return inner_function
    return do_cache


def print_duration(method):
    """Prints out the runtime duration of a method in seconds
    """
    def timed(*args, **kw):
        ts = time.time()
        result = method(*args, **kw)
        te = time.time()
        print '%r %2.2f sec' % (method.__name__, te-ts)
        return result
    return timed


def chunks(l, n):
    """Yield n successive chunks from l
    """
    newn = int(len(l) / n)
    for i in xrange(0, n-1):
        yield l[i*newn:i*newn+newn]
    yield l[n*newn-newn:]


def purge(fn, pattern):
    """Delete files in a dir matching pattern
    """
    for f in os.listdir(fn):
        if re.search(pattern, f):
            os.remove(os.path.join(fn, f))


def clear_memo_cache(source):
    """Clears the memoization cache for this specific news domain
    """
    d_pth = os.path.join(settings.MEMO_DIR, domain_to_filename(source.domain))
    if os.path.exists(d_pth):
        os.remove(d_pth)
    else:
        print 'memo file for', source.domain, 'has already been deleted!'


def memoize_articles(source, articles):
    """When we parse the <a> links in an <html> page, on the 2nd run
    and later, check the <a> links of previous runs. If they match,
    it means the link must not be an article, because article urls
    change as time passes. This method also uniquifies articles.
    """
    source_domain = source.domain
    config = source.config

    if len(articles) == 0:
        return []

    memo = {}
    cur_articles = {article.url: article for article in articles}
    d_pth = os.path.join(settings.MEMO_DIR, domain_to_filename(source_domain))

    if os.path.exists(d_pth):
        f = codecs.open(d_pth, 'r', 'utf8')
        urls = f.readlines()
        f.close()
        urls = [u.strip() for u in urls]

        memo = {url: True for url in urls}
        # prev_length = len(memo)
        for url, article in cur_articles.items():
            if memo.get(url):
                del cur_articles[url]

        valid_urls = memo.keys() + cur_articles.keys()

        memo_text = u'\r\n'.join(
            [get_unicode(href.strip()) for href in (valid_urls)])
    # Our first run with memoization, save every url as valid
    else:
        memo_text = u'\r\n'.join(
            [get_unicode(href.strip()) for href in cur_articles.keys()])

    # new_length = len(cur_articles)
    if len(memo) > config.MAX_FILE_MEMO:
        # We still keep current batch of articles though!
        log.critical('memo overflow, dumping')
        memo_text = ''

    # TODO if source: source.write_upload_times(prev_length, new_length)
    ff = codecs.open(d_pth, 'w', 'utf-8')
    ff.write(memo_text)
    ff.close()
    return cur_articles.values()


def get_useragent():
    """Uses generator to return next useragent in saved file
    """
    with open(settings.USERAGENTS, 'r') as f:
        agents = f.readlines()
        selection = random.randint(0, len(agents)-1)
        agent = agents[selection]
        return agent.strip()


def get_available_languages():
    """Returns a list of available languages and their 2 char input codes
    """
    stopword_files = os.listdir(os.path.join(settings.STOPWORDS_DIR))
    two_dig_codes = [f.split('-')[1].split('.')[0] for f in stopword_files]
    for d in two_dig_codes:
        assert len(d) == 2
    return two_dig_codes


def print_available_languages():
    """Prints available languages with their full names
    """
    language_dict = {
        'ar':   'Arabic',
        'ru':   'Russian',
        'nl':   'Dutch',
        'de':   'German',
        'en':   'English',
        'es':   'Spanish',
        'fr':   'French',
        'it':   'Italian',
        'ko':   'Korean',
        'no':   'Norwegian',
        'nb':   'Norwegian (Bokmål)',
        'pt':   'Portuguese',
        'sv':   'Swedish',
        'hu':   'Hungarian',
        'fi':   'Finnish',
        'da':   'Danish',
        'zh':   'Chinese',
        'id':   'Indonesian',
        'vi':   'Vietnamese',
    }

    codes = get_available_languages()
    print '\nYour available languages are:'
    print '\ninput code\t\tfull name'
    for code in codes:
        print '  %s\t\t\t  %s' % (code, language_dict[code])
    print


def extend_config(config, config_items):
    """
    We are handling config value setting like this for a cleaner api.
    Users just need to pass in a named param to this source and we can
    dynamically generate a config object for it.
    """
    for key, val in config_items.items():
        if hasattr(config, key):
            setattr(config, key, val)

    return config
