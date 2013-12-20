# -*- coding: utf-8 -*-

import os
import re
import sys
import threading
import pickle
import time
import logging
import string
import codecs
import random
import Queue

from hashlib import sha1
from threading import Thread

from .settings import MEMODIR, MAX_FILE_MEMO, USERAGENTS_FN

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

class TimeoutError(Exception):
    pass

def timelimit(timeout):
    """ borrowed from web.py, rip Aaron Swartz """

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

def cache_disk(seconds=(86400*5), cache_folder="/tmp"):
    """caching extracting category locations & rss feeds for 5 days"""

    def do_cache(function):
        def inner_function(*args, **kwargs):
            """calculate a cache key based on the decorated method signature
            args[1] indicates the domain of the inputs, we hash on domain!"""

            key = sha1(str(args[1]) + str(kwargs)).hexdigest()
            filepath = os.path.join(cache_folder, key)

            # verify that the cached object exists and is less than X seconds old
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
    """prints out the runtime duration of a method in seconds"""

    def timed(*args, **kw):
        ts = time.time()
        result = method(*args, **kw)
        te = time.time()
        print '%r %2.2f sec' % (method.__name__, te-ts)
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

def clear_memo_cache(source):
    """clears the memoization cache for this specific news domain"""

    d_pth = os.path.join(MEMODIR, domain_to_filename(source.domain))
    if os.path.exists(d_pth):
        os.remove(d_pth)
    else:
        print 'memo file for', source.domain, 'has already been deleted!'

def memoize_articles(articles, source_domain):
    """When we parse the <a> links in an <html> page, on the 2nd run
    and later, check the <a> links of previous runs. If they match,
    it means the link must not be an article, because article urls
    change as time passes. This method also uniquifies articles."""

    if len(articles) == 0:
        return []

    cur_articles = { article.url:article for article in articles }
    memo = {}
    #print '******current article urls!', cur_articles.keys()[:10]

    d_pth = os.path.join(MEMODIR, domain_to_filename(source_domain))

    if os.path.exists(d_pth):
        f = codecs.open(d_pth, 'r', 'utf8')
        urls = f.readlines() # list of urls, unicode
        f.close()
        urls = [u.strip() for u in urls]

        memo = { url:True for url in urls }
        # prev_length = len(memo)
        for url, article in cur_articles.items():
            if memo.get(url):
                del cur_articles[url]

        valid_urls = memo.keys() + cur_articles.keys()

        memo_text = u'\r\n'.join(
            [fix_unicode(href.strip()) for href in (valid_urls)])
    # Our first run with memoization, save every url as valid
    else:
        memo_text = u'\r\n'.join(
            [fix_unicode(href.strip()) for href in cur_articles.keys()])

    # new_length = len(cur_articles)

    if len(memo) > MAX_FILE_MEMO:
        # We still keep current batch of articles though!
        log.critical('memo overflow, dumping')
        memo_text = ''

    # TODO if source: source.write_upload_times(prev_length, new_length)
    ff = codecs.open(d_pth, 'w', 'utf-8')
    ff.write(memo_text)
    ff.close()
    #print '***** final article urls', cur_articles.keys()[:10]
    return cur_articles.values() # articles returned

def get_useragent():
    """uses generator to return next useragent in saved file"""

    with open(USERAGENTS_FN, 'r') as f:
        agents = f.readlines()
        selection = random.randint(0, len(agents)-1)
        agent = agents[selection]
        return agent.strip()

class Worker(Thread):
    """Thread executing tasks from a given tasks queue"""

    def __init__(self, tasks):
        Thread.__init__(self)
        self.tasks = tasks
        self.daemon = True
        self.start()

    def run(self):
        while True:
            try:
                func, args, kargs = self.tasks.get()
            except Queue.Empty:
                print 'thread breaking b/c queue is empty'
                break
            try:
                func(*args, **kargs)
            except Exception, e:
                print 'critical multi-thread err %s' % e

            self.tasks.task_done()

class ThreadPool:
    """Pool of threads consuming tasks from a queue"""

    def __init__(self, num_threads):
        self.tasks = Queue.Queue(num_threads)
        for _ in range(num_threads):
            Worker(self.tasks)

    def add_task(self, func, *args, **kargs):
        """Add a task to the queue"""

        self.tasks.put((func, args, kargs))

    def wait_completion(self):
        """Wait for completion of all the tasks in the queue"""

        self.tasks.join()

    def clear_threads(self):
        """"""

        pass

