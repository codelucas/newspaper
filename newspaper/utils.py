# -*- coding: utf-8 -*-

import os
import re
import sys
import threading
import pickle
import time
import logging
import string
from hashlib import sha1

log = logging.getLogger(__name__)

class TimeoutError(Exception):
    pass

def timelimit(timeout):
    """ borrowed from web.py, rip Aaron Shwartz """
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


def is_abs_url(url):
    """this regex was brought to you by django!"""

    regex = re.compile(
        r'^(?:http|ftp)s?://'                                                                 # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
        r'localhost|'                                                                         # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|'                                                # ...or ipv4
        r'\[?[A-F0-9]*:[A-F0-9:]+\]?)'                                                        # ...or ipv6
        r'(?::\d+)?'                                                                          # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)

    c_regex = re.compile(regex)
    return (c_regex.search(url) != None)


def domain_to_filename(domain):
    """all '/' are turned into '-', no trailing. schema's
     are gone, only the raw domain + ".txt" remains"""

    filename =  domain.replace('/', '-')

    if filename[-1] == '-':
        filename = filename[:-1]
    filename += ".txt"
    return filename


def filename_to_domain(filename):
    """[:-4] for the .txt at end"""

    return filename.replace('-', '/')[:-4]


def is_ascii(word):
    """true if a word is only ascii chars"""

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
    """converts arbitrary string (for us domain name)
    into a valid file name for caching"""

    valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
    return ''.join(c for c in s if c in valid_chars)


def cache_disk(seconds=(86400 * 5), cache_folder="/tmp"):
    """caching extracting category locations & rss feeds for 5 days"""

    def doCache(f):
        def inner_function(*args, **kwargs):
            """calculate a cache key based on the decorated method signature
            args[1] indicates the domain of the inputs, we hash on domain!"""
            key = sha1(str(args[1]) + str(kwargs)).hexdigest()
            filepath = os.path.join(cache_folder, key)

            # verify that the cached object exists and is less than $seconds old
            if os.path.exists(filepath):
                modified = os.path.getmtime(filepath)
                age_seconds = time.time() - modified
                if age_seconds < seconds:
                    return pickle.load(open(filepath, "rb"))

            # call the decorated function...
            result = f(*args, **kwargs)
            # ... and save the cached object for next time
            pickle.dump(result, open(filepath, "wb"))

            return result
        return inner_function
    return doCache


def print_duration(method):
    """prints out the runtime duration of a method in seconds"""

    def timed(*args, **kw):
        ts = time.time()
        result = method(*args, **kw)
        te = time.time()

        log.debug('%r %2.2f sec' % (method.__name__, te-ts))
        return result

    return timed


def chunks(l, n):
    """ Yield n successive chunks from l"""

    newn = int(len(l) / n)
    for i in xrange(0, n-1):
        yield l[i*newn:i*newn+newn]
    yield l[n*newn-newn:]


def purge(fn, pattern):
    """delete files in a dir matching pattern"""
    import os, re
    for f in os.listdir(fn):
        if re.search(pattern, f):
            os.remove(os.path.join(fn, f))


def fix_unicode(inputstr):
    """returns unicode version of input"""
    if inputstr is None:
        return u''

    if not isinstance(inputstr, unicode):
        try:
            inputstr = inputstr.decode('utf8', errors='ignore')
        except ValueError, e:
            log.debug(e)
            inputstr = u''

    inputstr = inputstr.strip()
    return inputstr